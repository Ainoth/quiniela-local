"""Interfaz compacta para el generador Normal clásico, conectada al dominio."""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quiniela_ai_studio.domain.normal_generation import (
    ProbabilitySource,
    best_base,
    best_base_under_limit,
    import_probability_source,
    normalize_percentages,
    parse_columns_file,
    validate_percentages,
    weighted_probabilities,
)
from quiniela_ai_studio.infrastructure.files import read_bytes
from quiniela_ai_studio.infrastructure.normal_generation import generate_actions_file


class ActionWorker(QThread):
    progress = Signal(int, int, str)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, path, actions, *, keep_duplicates, intersection, parent=None):
        super().__init__(parent)
        self.path, self.actions = path, actions
        self.keep_duplicates, self.intersection = keep_duplicates, intersection
        import threading
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            result = generate_actions_file(self.path, self.actions,
                keep_duplicates=self.keep_duplicates, intersection=self.intersection,
                cancelled=self.cancel_event.is_set,
                progress=lambda done, total, message: self.progress.emit(done, total, message))
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class NormalGenerator(QWidget):
    """Matriz editable, ponderaciones, base automática y tabla de acciones."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.repository = window.repository
        self.current_round = None
        self.probability_sources: dict[str, ProbabilitySource] = {}
        self.column_sources: dict[str, tuple[str, ...]] = {}
        self.column_source_meta: dict[str, dict[str, str]] = {}
        self.worker = None
        self.last_report = None
        self._loading = False
        self.matrix_origin = "manual"
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 2, 4, 2)
        root.setSpacing(5)

        self.base_group = QGroupBox("QUINIELA BASE AUTOMÁTICA")
        base_layout = QVBoxLayout(self.base_group)
        base_layout.setContentsMargins(7, 12, 7, 7)
        base_layout.setSpacing(4)
        upper = QHBoxLayout()
        self.probability_table = QTableWidget(14, 5)
        self.probability_table.setHorizontalHeaderLabels(("#", "Partido", "1", "X", "2"))
        self.probability_table.verticalHeader().hide()
        self.probability_table.verticalHeader().setDefaultSectionSize(19)
        self.probability_table.setAlternatingRowColors(True)
        self.probability_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.probability_table.setFixedHeight(328)
        self.probability_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.probability_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in (2, 3, 4):
            self.probability_table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            self.probability_table.setColumnWidth(column, 49)
        self.probability_table.setColumnWidth(0, 27)
        self.probability_table.setStyleSheet("QTableWidget{font-size:10px;gridline-color:#2a5b88;} QHeaderView::section{padding:2px;font-size:10px;} QTableWidget::item{padding:1px;}")
        self.probability_table.itemChanged.connect(self._matrix_user_edited)
        upper.addWidget(self.probability_table, 4)

        right = QVBoxLayout()
        weight_box = QGroupBox("Ponderaciones (0–100%)")
        weight_layout = QGridLayout(weight_box)
        weight_layout.setContentsMargins(6, 8, 6, 6)
        weight_layout.setHorizontalSpacing(5)
        weight_layout.setVerticalSpacing(3)
        self.weight_spin = {}
        self.weight_status = {}
        labels = (("classification", "CLASIFICACIÓN", "Fuerza relativa actual; si existe, separada por local/visitante."),
                  ("form5", "5 ÚLT. JORNADAS", "Forma con los últimos cinco resultados disponibles."),
                  ("history", "HISTORIAL", "Enfrentamientos anteriores u otra serie histórica importada."))
        for row, (key, label, tip) in enumerate(labels):
            title = QLabel(label); title.setToolTip(tip); title.setStyleSheet("font-size:10px;font-weight:bold;")
            spin = QSpinBox(); spin.setRange(0, 100); spin.setValue(50); spin.setSuffix(" %"); spin.setFixedWidth(80)
            spin.valueChanged.connect(self._configuration_changed)
            status = QLabel("Sin datos importados"); status.setObjectName("muted"); status.setStyleSheet("font-size:9px;")
            weight_layout.addWidget(title, row, 0); weight_layout.addWidget(spin, row, 1); weight_layout.addWidget(status, row, 2)
            self.weight_spin[key], self.weight_status[key] = spin, status
        right.addWidget(weight_box)

        controls_box = QGroupBox("Signos que añadirá a la base")
        controls = QGridLayout(controls_box)
        controls.setContentsMargins(6, 8, 6, 5); controls.setHorizontalSpacing(5); controls.setVerticalSpacing(3)
        self.assignment_mode = QComboBox()
        self.assignment_mode.addItem("Automática · según porcentajes", "automatic")
        self.assignment_mode.addItem("Manual · indicar cantidades", "manual")
        self.assignment_mode.setFixedWidth(220)
        controls.addWidget(QLabel("ASIGNACIÓN"), 0, 0)
        controls.addWidget(self.assignment_mode, 0, 1, 1, 3)
        self.triples = QSpinBox(); self.triples.setRange(0, 14); self.triples.setValue(0); self.triples.setFixedWidth(64)
        self.doubles = QSpinBox(); self.doubles.setRange(0, 14); self.doubles.setValue(0); self.doubles.setFixedWidth(64)
        self.triples.valueChanged.connect(lambda value: self._count_changed("triples", value))
        self.doubles.valueChanged.connect(lambda value: self._count_changed("doubles", value))
        self.triple_plus, self.triple_minus = self._step_buttons(self.triples)
        self.double_plus, self.double_minus = self._step_buttons(self.doubles)
        controls.addWidget(QLabel("TRIPLES"), 1, 0); controls.addWidget(self.triples, 1, 1); controls.addWidget(self.triple_plus, 1, 2); controls.addWidget(self.triple_minus, 1, 3)
        controls.addWidget(QLabel("DOBLES"), 2, 0); controls.addWidget(self.doubles, 2, 1); controls.addWidget(self.double_plus, 2, 2); controls.addWidget(self.double_minus, 2, 3)
        self.max_columns = QSpinBox(); self.max_columns.setRange(1, 100_000); self.max_columns.setValue(6); self.max_columns.setGroupSeparatorShown(True); self.max_columns.setFixedWidth(94)
        self.max_columns.setToolTip("En Automática se buscará la base que conserve más probabilidad conjunta sin superar este número de columnas.")
        self.max_columns.valueChanged.connect(self._configuration_changed)
        self.max_columns_label = QLabel("Máx. columnas")
        controls.addWidget(self.max_columns_label, 3, 0); controls.addWidget(self.max_columns, 3, 1)
        self.combination_count = QLabel("1 columna base"); self.combination_count.setStyleSheet("color:#49dbff;font-weight:bold;")
        controls.addWidget(self.combination_count, 4, 0, 1, 4)
        self.assignment_mode.currentIndexChanged.connect(self._assignment_mode_changed)
        right.addWidget(controls_box)

        save_row = QHBoxLayout()
        self.normalize_button = QPushButton("Normalizar filas")
        self.save_percentages = QPushButton("Guardar %")
        self.load_percentages = QPushButton("Cargar %")
        self.manage_sources = QPushButton("Gestionar fuentes…")
        for button in (self.normalize_button, self.save_percentages, self.load_percentages, self.manage_sources):
            button.setFixedHeight(25); button.setStyleSheet("padding:2px 5px;font-size:10px;")
            save_row.addWidget(button)
        self.normalize_button.clicked.connect(lambda: self.window.safe(self._normalize_matrix))
        self.save_percentages.clicked.connect(lambda: self.window.safe(self._save_percentages))
        self.load_percentages.clicked.connect(lambda: self.window.safe(self._load_percentages))
        self.manage_sources.clicked.connect(lambda: self.window.safe(self._manage_sources))
        right.addLayout(save_row)
        self.recalculate_button = QPushButton("Recalcular porcentajes")
        self.recalculate_button.setFixedHeight(28); self.recalculate_button.clicked.connect(lambda: self.window.safe(self._recalculate))
        right.addWidget(self.recalculate_button)
        self.base_status = QLabel("Los porcentajes se muestran con su fuente; puedes editarlos o importar datos.")
        self.base_status.setWordWrap(True); self.base_status.setObjectName("muted"); self.base_status.setStyleSheet("font-size:10px;")
        right.addWidget(self.base_status)
        self.fill_base_button = QPushButton("Rellenar quiniela base")
        self.fill_base_button.setObjectName("primary"); self.fill_base_button.setFixedHeight(30)
        self.fill_base_button.clicked.connect(lambda: self.window.safe(self._fill_base))
        right.addWidget(self.fill_base_button)
        right.addStretch(1)
        upper.addLayout(right, 5)
        base_layout.addLayout(upper)

        self.actions_group = QGroupBox("GENERAR FICHERO POR COEFICIENTE DE PROBABILIDAD Y POR TRIPLES / DOBLES")
        actions_layout = QVBoxLayout(self.actions_group)
        actions_layout.setContentsMargins(6, 12, 6, 6); actions_layout.setSpacing(4)
        self.action_table = QTableWidget(0, 10)
        self.action_table.setHorizontalHeaderLabels(("Usar", "Acción", "Núm. Colum.", "Desde", "Hasta", "C.P. desde / hasta", "Triples", "Dobles", "Terminaciones 0–9", "% de…"))
        self.action_table.verticalHeader().hide(); self.action_table.setAlternatingRowColors(True)
        self.action_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.action_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.action_table.setFixedHeight(190)
        self.action_table.setStyleSheet("QTableWidget{font-size:10px;gridline-color:#2a5b88;} QHeaderView::section{padding:2px;font-size:9px;}")
        widths = (42, 145, 84, 62, 62, 220, 58, 58, 190, 160)
        for index, width in enumerate(widths):
            self.action_table.setColumnWidth(index, width)
            self.action_table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeMode.Fixed)
        actions_layout.addWidget(self.action_table)
        table_actions = QHBoxLayout()
        self.add_action_button = QPushButton("+ Fila"); self.remove_action_button = QPushButton("− Fila")
        self.add_action_button.clicked.connect(self._add_action); self.remove_action_button.clicked.connect(self._remove_action)
        table_actions.addWidget(self.add_action_button); table_actions.addWidget(self.remove_action_button)
        self.import_columns_button = QPushButton("Importar columnas…"); self.import_columns_button.clicked.connect(lambda: self.window.safe(self._import_columns))
        self.view_percentages_button = QPushButton("Ver porcentajes"); self.view_percentages_button.clicked.connect(lambda: self.window.safe(self._view_selected_percentages))
        self.help_button = QPushButton("Información / Ayuda"); self.help_button.clicked.connect(self._show_help)
        for button in (self.import_columns_button, self.view_percentages_button, self.help_button): table_actions.addWidget(button)
        table_actions.addStretch(1); actions_layout.addLayout(table_actions)
        terms_note = QLabel("Terminaciones: son la última cifra de la posición (desde 1) en el orden de probabilidad. Sin cifras marcadas, no se filtra.")
        terms_note.setWordWrap(True); terms_note.setObjectName("muted"); terms_note.setStyleSheet("font-size:10px;")
        actions_layout.addWidget(terms_note)
        self.keep_duplicates = QCheckBox("Mantener columnas duplicadas (concatenar acciones)")
        self.intersection = QCheckBox("Generar solo columnas presentes en todas las acciones (intersección)")
        self.keep_duplicates.toggled.connect(self._combination_changed); self.intersection.toggled.connect(self._combination_changed)
        actions_layout.addWidget(self.keep_duplicates); actions_layout.addWidget(self.intersection)
        self.action_status = QLabel("Las filas inactivas no se ejecutan. Rango Desde/Hasta inclusivo; en blanco se usa Núm. Colum.")
        self.action_status.setWordWrap(True); self.action_status.setObjectName("muted"); actions_layout.addWidget(self.action_status)
        run_row = QHBoxLayout()
        self.generate_file_button = QPushButton("Generar fichero…"); self.generate_file_button.setObjectName("primary")
        self.cancel_action_button = QPushButton("Cancelar"); self.cancel_action_button.setEnabled(False)
        self.action_progress = QProgressBar(); self.action_progress.setValue(0)
        run_row.addWidget(self.generate_file_button); run_row.addWidget(self.cancel_action_button); run_row.addWidget(self.action_progress, 1)
        actions_layout.addLayout(run_row)
        self.generate_file_button.clicked.connect(lambda: self.window.safe(self._choose_output))
        self.cancel_action_button.clicked.connect(self._cancel_generation)
        self._load_action_rows(None)
        self._assignment_mode_changed()
        self._apply_local_styles()

    @staticmethod
    def _step_buttons(spin):
        plus = QPushButton("+"); minus = QPushButton("−")
        for button in (plus, minus):
            button.setFixedSize(20, 15); button.setStyleSheet("padding:0;font-size:10px;font-weight:bold;")
        plus.clicked.connect(lambda: spin.setValue(spin.value() + 1))
        minus.clicked.connect(lambda: spin.setValue(spin.value() - 1))
        return plus, minus

    def _apply_local_styles(self):
        self.base_group.setStyleSheet("QGroupBox{border:1px solid #2a6698;margin-top:8px;padding-top:7px;} QGroupBox::title{color:#49dbff;font-weight:bold;}")
        self.actions_group.setStyleSheet("QGroupBox{border:1px solid #2a6698;margin-top:8px;padding-top:7px;} QGroupBox::title{color:#49dbff;font-size:11px;font-weight:bold;}")
        for button in (self.normalize_button, self.save_percentages, self.load_percentages,
                       self.manage_sources, self.add_action_button, self.remove_action_button,
                       self.import_columns_button, self.view_percentages_button, self.help_button,
                       self.cancel_action_button):
            button.setStyleSheet("padding:3px 6px;font-size:10px;")

    def load_round(self, round_, system):
        """Carga o conserva perfiles por jornada; nunca comparte matrices entre rondas."""
        if self.current_round and self.current_round.key == round_.key:
            previous_snapshots = {
                key: value for key, value in self.probability_sources.items()
                if key.startswith("snapshot:")
            }
            updated_snapshots = {}
            for snapshot in round_.snapshots:
                kind = "market" if snapshot.kind == "sport" else "public"
                key = f"snapshot:{snapshot.kind}"
                updated_snapshots[key] = ProbabilitySource(
                    round_.key, snapshot.source, snapshot.captured_at,
                    snapshot.values, kind,
                    tuple((match.home, match.away) for match in round_.matches[:14]),
                )
            snapshots_changed = previous_snapshots != updated_snapshots
            self.probability_sources = {
                key: source for key, source in self.probability_sources.items()
                if not key.startswith("snapshot:")
            }
            self.probability_sources.update(updated_snapshots)
            self.current_round = round_
            if snapshots_changed:
                source_key = self.matrix_origin if self.matrix_origin.startswith("snapshot:") else None
                try:
                    self._matrix_values()
                    matrix_is_valid = True
                except ValueError:
                    matrix_is_valid = False
                if source_key is None and not matrix_is_valid:
                    preferred = self.window.ranking_source.currentData()
                    source_key = f"snapshot:{preferred}"
                source = self.probability_sources.get(source_key or "")
                if source is not None:
                    self._populate_probability_table(source.values)
                    self.matrix_origin = source_key
                    self.base_status.setText(
                        f"Matriz desde {source.source} · captura {source.captured_at}."
                    )
                    self._matrix_edited()
            self._refresh_availability(system)
            return
        self._loading = True
        self.current_round = round_
        self.probability_sources = {}
        self.column_sources = {}
        for snap in round_.snapshots:
            kind = "market" if snap.kind == "sport" else "public"
            key = f"snapshot:{snap.kind}"
            self.probability_sources[key] = ProbabilitySource(round_.key, snap.source, snap.captured_at,
                snap.values, kind, tuple((m.home, m.away) for m in round_.matches[:14]))
        for item in self.repository.setting(f"normal_sources:{round_.key}", []):
            source = ProbabilitySource(**item)
            key = f"local:{source.source}:{source.kind}:{source.captured_at}"
            self.probability_sources[key] = source
        for item in self.repository.setting(f"normal_column_sources:{round_.key}", []):
            self.column_sources[item["id"]] = tuple(item["columns"])
            self.column_source_meta[item["id"]] = {"file_name": item.get("name", "fichero importado"), "columns_sha256": item.get("columns_sha256", "")}
        config = self.repository.setting(f"normal_generator:{round_.key}", {})
        values = config.get("percentages")
        selected_snapshot = self.probability_sources.get("snapshot:sport") or self.probability_sources.get("snapshot:public")
        default_origin = "snapshot:sport" if "snapshot:sport" in self.probability_sources else ("snapshot:public" if selected_snapshot else "manual")
        self.matrix_origin = config.get("matrix_origin", "manual" if values is not None else default_origin)
        if values and isinstance(values[0][0], str):
            try: values = [[float(value.replace(",", ".").replace("%", "")) / 100 for value in row] for row in values]
            except ValueError: values = None
        if values is None:
            snapshot = selected_snapshot
            values = snapshot.values if snapshot else None
            if snapshot:
                self.base_status.setText(f"Matriz inicial desde {snapshot.source} · captura {snapshot.captured_at}.")
            else:
                self.base_status.setText("No hay porcentajes para esta jornada. Importa una fuente o introduce los 1/X/2; no se inventan valores.")
        elif config.get("percentages") is not None:
            self.base_status.setText(f"Matriz guardada para {round_.key}; puedes editarla antes de usarla.")
        self._populate_probability_table(values)
        for key, spin in self.weight_spin.items():
            spin.setValue(int(config.get("weights", {}).get(key, 50)))
        initial_base = system.base if system and self.window.system_mode(system) == "normal" else ("1",) * 14
        self.assignment_mode.setCurrentIndex(max(0, self.assignment_mode.findData(config.get("assignment_mode", "automatic"))))
        self.triples.setValue(int(config.get("triples", sum(len(value) == 3 for value in initial_base))))
        self.doubles.setValue(int(config.get("doubles", sum(len(value) == 2 for value in initial_base))))
        self.max_columns.setValue(max(1, min(100_000, int(config.get("max_columns", 6)))))
        self.keep_duplicates.setChecked(bool(config.get("keep_duplicates", False)))
        self.intersection.setChecked(bool(config.get("intersection", False)))
        self._load_action_rows(config.get("actions"))
        self._loading = False
        self._refresh_availability(system)
        self._matrix_edited()
        self._update_theoretical_count()

    def _populate_probability_table(self, values):
        self.probability_table.blockSignals(True)
        for row in range(14):
            match = self.current_round.matches[row]
            number = QTableWidgetItem(f"{row + 1:02}"); number.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.probability_table.setItem(row, 0, number)
            teams = QTableWidgetItem(f"{match.home} – {match.away}"); teams.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.probability_table.setItem(row, 1, teams)
            for offset in range(3):
                text = "" if values is None else f"{100 * float(values[row][offset]):.2f}"
                item = QTableWidgetItem(text); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.probability_table.setItem(row, offset + 2, item)
        self.probability_table.blockSignals(False)

    def _matrix_values(self):
        rows = []
        for row in range(14):
            values = []
            for column in range(2, 5):
                item = self.probability_table.item(row, column)
                text = item.text().strip().replace("%", "").replace(",", ".") if item else ""
                try: value = float(text) / 100
                except ValueError as exc: raise ValueError(f"Introduce un porcentaje válido en el partido {row + 1}.") from exc
                values.append(value)
            rows.append(tuple(values))
        return validate_percentages(rows)

    def _matrix_edited(self, *_):
        if self._loading: return
        self._configuration_changed()
        try:
            self._matrix_values()
            self.base_status.setText("Matriz válida: cada fila suma 100%.")
            system = self.window.system
            self.fill_base_button.setEnabled(bool(system and self.window.round.editable and self.window.system_mode(system) == "normal"))
        except ValueError as exc:
            self.base_status.setText(str(exc)); self.fill_base_button.setEnabled(False)

    def _matrix_user_edited(self, *_):
        self.matrix_origin = "manual"
        self._matrix_edited()

    def _configuration_changed(self, *_):
        if not self._loading: self._save_configuration()

    def _assignment_mode_changed(self, *_):
        manual = self.assignment_mode.currentData() == "manual"
        for widget in (self.triples, self.doubles, self.triple_plus, self.triple_minus, self.double_plus, self.double_minus):
            widget.setEnabled(manual)
        self.max_columns.setEnabled(not manual)
        self.max_columns_label.setEnabled(not manual)
        self.assignment_mode.setToolTip(
            "Indica las cantidades; los partidos se eligen por su probabilidad." if manual
            else "El programa elige cantidades y partidos con mayor probabilidad conjunta dentro del máximo de columnas."
        )
        if not self._loading: self._save_configuration()

    def _count_changed(self, which, value):
        other = self.doubles if which == "triples" else self.triples
        if value + other.value() > 14:
            target = self.triples if which == "triples" else self.doubles
            target.blockSignals(True); target.setValue(14 - other.value()); target.blockSignals(False)
        self._update_theoretical_count()
        if not self._loading: self._save_configuration()

    def _update_theoretical_count(self):
        count = 3 ** self.triples.value() * 2 ** self.doubles.value()
        self.combination_count.setText(f"{count:,} columnas base · {14 - self.triples.value() - self.doubles.value()} fijos")

    def _save_configuration(self):
        if not self.current_round: return
        try: percentages = [[self.probability_table.item(row, col).text() for col in range(2, 5)] for row in range(14)]
        except AttributeError: percentages = None
        data = dict(percentages=percentages,
                    weights={key: spin.value() for key, spin in self.weight_spin.items()},
                    triples=self.triples.value(), doubles=self.doubles.value(),
                    assignment_mode=self.assignment_mode.currentData(),
                    max_columns=self.max_columns.value(),
                    matrix_origin=self.matrix_origin,
                    keep_duplicates=self.keep_duplicates.isChecked(), intersection=self.intersection.isChecked(),
                    actions=[self._action_config(row) for row in range(self.action_table.rowCount())])
        key = f"normal_generator:{self.current_round.key}"
        previous = self.repository.setting(key, {})
        # Keep the explicit snapshot created by «Guardar %» while autosaving
        # the live matrix and controls after every edit.
        if "saved_percentages" in previous:
            data["saved_percentages"] = previous["saved_percentages"]
        self.repository.set_setting(key, data)

    def _save_percentages(self):
        self._matrix_values()
        key=f"normal_generator:{self.current_round.key}"
        config=self.repository.setting(key,{})
        config["saved_percentages"]=[[self.probability_table.item(row,col).text() for col in range(2,5)] for row in range(14)]
        self.repository.set_setting(key,config)
        self._save_configuration()
        self.base_status.setText(f"Porcentajes guardados para {self.current_round.key}.")

    def _load_percentages(self):
        config = self.repository.setting(f"normal_generator:{self.current_round.key}", {})
        values = config.get("saved_percentages")
        if values is None:
            source = self.probability_sources.get("snapshot:sport") or self.probability_sources.get("snapshot:public")
            values = source.values if source else None
        if values is None:
            raise ValueError("No hay porcentajes guardados ni instantáneas descargadas para esta jornada.")
        if values and isinstance(values[0][0], str): values = [[float(value.replace(",", ".")) / 100 for value in row] for row in values]
        self._populate_probability_table(values); self.matrix_origin = "manual"
        self._matrix_edited()

    def _normalize_matrix(self):
        rows = []
        for row in range(14):
            values = []
            for col in range(2, 5):
                item = self.probability_table.item(row, col)
                try: values.append(float(item.text().strip().replace(",", ".").replace("%", "")) / 100)
                except (ValueError, AttributeError) as exc: raise ValueError(f"Rellena los tres porcentajes del partido {row + 1}.") from exc
            rows.append(values)
        normalized = normalize_percentages(rows, 2)
        self._populate_probability_table(normalized); self.matrix_origin = "manual"; self._matrix_edited()

    def use_selected_snapshot(self, kind):
        """Actualiza la matriz solo si aún sigue vinculada a una captura externa."""
        if not self.matrix_origin.startswith("snapshot:"):
            return
        source = self.probability_sources.get(f"snapshot:{kind}")
        if source is None:
            return
        self._populate_probability_table(source.values)
        self.matrix_origin = f"snapshot:{kind}"
        self.base_status.setText(f"Matriz desde {source.source} · captura {source.captured_at}.")
        self._matrix_edited()

    def _refresh_availability(self, system):
        for kind in ("classification", "form5", "history"):
            sources = [source for source in self.probability_sources.values() if source.kind == kind]
            if sources:
                source = sources[-1]
                self.weight_status[kind].setText(f"{source.source} · importado")
                self.weight_status[kind].setToolTip(source.captured_at)
                self.weight_spin[kind].setEnabled(True)
            else:
                self.weight_status[kind].setText("Sin datos importados")
                self.weight_status[kind].setToolTip("Esta fuente no existe en la jornada. No se sustituye por porcentajes inventados.")
                spin = self.weight_spin[kind]
                spin.blockSignals(True)
                spin.setValue(0)
                spin.setEnabled(False)
                spin.blockSignals(False)
        weighted_sources = any(
            spin.value() > 0 and self._sources_for_kind(kind)
            for kind, spin in self.weight_spin.items()
        )
        missing_sources = any(
            spin.value() > 0 and not self._sources_for_kind(kind)
            for kind, spin in self.weight_spin.items()
        )
        self.recalculate_button.setEnabled(weighted_sources and not missing_sources)
        self.recalculate_button.setToolTip(
            "Combina clasificación, forma e historial importados. Para usar los porcentajes de mercado o popularidad, elige esa fuente y pulsa Rellenar quiniela base."
        )
        self.fill_base_button.setEnabled(bool(system and self.window.round.editable and self.window.system_mode(system) == "normal"))
        self._update_source_combos()

    def _available_sources(self, include_columns=False):
        items = [(key, source.source, source) for key, source in self.probability_sources.items()]
        if include_columns:
            items.extend((key, f"Fichero local · {len(columns):,} columnas", columns) for key, columns in self.column_sources.items())
        return items

    def _update_source_combos(self):
        for combo in getattr(self, "action_sources", []):
            current = combo.currentData(); combo.blockSignals(True); combo.clear()
            for key, label, _value in self._available_sources(include_columns=True): combo.addItem(label, key)
            for label, key in (("LAE · sin datos disponibles", "unavailable:lae"),
                               ("Betfair independiente · sin feed", "unavailable:betfair"),
                               ("WIN1X2 · importa un fichero local", "unavailable:win1x2")):
                combo.addItem(label, key)
            if current is not None:
                index = combo.findData(current)
                if index >= 0: combo.setCurrentIndex(index)
            combo.blockSignals(False)
        for row in range(self.action_table.rowCount()): self._action_type_changed(row)

    def _add_action(self, config=None):
        row = self.action_table.rowCount(); self.action_table.insertRow(row)
        check = QCheckBox(); check.setChecked(row == 0 if config is None else bool(config.get("enabled", False)))
        check.setToolTip("Ejecutar esta acción"); check.toggled.connect(self._configuration_changed)
        self.action_table.setCellWidget(row, 0, check)
        action = QComboBox(); action.addItem("Columnas más probables", "top"); action.addItem("Triples / Dobles", "base"); action.addItem("Fichero de columnas", "imported")
        if config: action.setCurrentIndex(max(0, action.findData(config.get("kind", "top"))))
        action.currentIndexChanged.connect(lambda _idx, r=row: self._action_type_changed(r)); action.currentIndexChanged.connect(self._configuration_changed)
        self.action_table.setCellWidget(row, 1, action)
        count = self._spin(1, 5_000_000, 100_000 if config is None else int(config.get("count", 100_000)))
        start = self._spin(0, 5_000_000, 0 if config is None else int(config.get("start", 0)))
        end = self._spin(0, 5_000_000, 0 if config is None else int(config.get("end", 0)))
        cp_min = QDoubleSpinBox(); cp_min.setRange(0, 1); cp_min.setDecimals(12); cp_min.setSingleStep(1e-8); cp_min.setFixedWidth(96); cp_min.setValue(0 if config is None else float(config.get("minimum_probability", 0))); cp_min.setToolTip("C.P. mínimo: producto de las 14 probabilidades marginales.")
        cp_max = QDoubleSpinBox(); cp_max.setRange(0, 1); cp_max.setDecimals(12); cp_max.setSingleStep(1e-8); cp_max.setFixedWidth(96); cp_max.setValue(1 if config is None else float(config.get("maximum_probability", 1))); cp_max.setToolTip("C.P. máximo: producto de las 14 probabilidades marginales.")
        cp_widget = QWidget(); cp_layout = QHBoxLayout(cp_widget); cp_layout.setContentsMargins(1, 1, 1, 1); cp_layout.setSpacing(2); cp_layout.addWidget(QLabel("≥")); cp_layout.addWidget(cp_min); cp_layout.addWidget(QLabel("≤")); cp_layout.addWidget(cp_max)
        for column, widget in ((2, count), (3, start), (4, end)):
            self.action_table.setCellWidget(row, column, widget); widget.valueChanged.connect(self._configuration_changed)
        self.action_table.setCellWidget(row, 5, cp_widget)
        cp_min.valueChanged.connect(self._configuration_changed); cp_max.valueChanged.connect(self._configuration_changed)
        triples = self._spin(0, 14, 0 if config is None else int(config.get("triples", 7)))
        doubles = self._spin(0, 14, 0 if config is None else int(config.get("doubles", 7)))
        triples.valueChanged.connect(lambda value, d=doubles: self._bound_pair(triples, d, value)); doubles.valueChanged.connect(lambda value, t=triples: self._bound_pair(doubles, t, value))
        triples.valueChanged.connect(self._configuration_changed); doubles.valueChanged.connect(self._configuration_changed)
        self.action_table.setCellWidget(row, 6, triples); self.action_table.setCellWidget(row, 7, doubles)
        endings_widget = QWidget(); endings_layout = QHBoxLayout(endings_widget); endings_layout.setContentsMargins(1, 1, 1, 1); endings_layout.setSpacing(1)
        endings = []
        selected = set(config.get("endings", ())) if config else set()
        for digit in range(10):
            button = QPushButton(str(digit)); button.setCheckable(True); button.setChecked(digit in selected); button.setFixedSize(18, 21)
            button.setToolTip(f"Conservar posiciones cuyo último dígito sea {digit}")
            button.setStyleSheet("QPushButton{padding:0;background:#f1f5f9;color:#183a5a;border:1px solid #9bb9d4;border-radius:1px;font-size:9px;} QPushButton:checked{background:#18864b;color:white;border-color:#35d27f;font-weight:bold;}")
            button.toggled.connect(self._configuration_changed); endings_layout.addWidget(button); endings.append(button)
        self.action_table.setCellWidget(row, 8, endings_widget)
        source = QComboBox(); self.action_table.setCellWidget(row, 9, source)
        self.action_sources.append(source)
        source.currentIndexChanged.connect(self._configuration_changed)
        self.action_table.setRowHeight(row, 29)
        self.action_table.cellWidget(row, 0).setProperty("actionCheck", check)
        self._action_widgets.append(dict(check=check, kind=action, count=count, start=start, end=end, cp_min=cp_min, cp_max=cp_max,
                                         triples=triples, doubles=doubles, endings=endings, source=source))
        if config is not None and config.get("source"):
            idx = source.findData(config["source"])
            if idx >= 0: source.setCurrentIndex(idx)
        self._update_source_combos()
        self._action_type_changed(row); self._save_configuration()

    def _spin(self, minimum, maximum, value):
        spin = QSpinBox(); spin.setRange(minimum, maximum); spin.setValue(value); spin.setFixedWidth(68)
        spin.setStyleSheet("padding:1px 2px;font-size:10px;")
        return spin

    def _load_action_rows(self, actions):
        self._loading = True
        self.action_table.setRowCount(0); self._action_widgets = []; self.action_sources = []
        sport = "snapshot:sport" if "snapshot:sport" in self.probability_sources else next(iter(self.probability_sources), None)
        public = "snapshot:public" if "snapshot:public" in self.probability_sources else sport
        configs = actions if actions else [dict(kind="top", count=100_000, enabled=True, source=sport),
            dict(kind="top", count=100_000, enabled=False, source=public), dict(kind="top", count=100_000, enabled=False, source=sport),
            dict(kind="base", count=100_000, triples=7, doubles=7, enabled=False, source=sport), dict(kind="top", count=100_000, enabled=False, source=sport)]
        for config in configs: self._add_action(config)
        self._loading = False

    @staticmethod
    def _bound_pair(changed, other, value):
        if value + other.value() > 14:
            changed.blockSignals(True); changed.setValue(14 - other.value()); changed.blockSignals(False)

    def _action_type_changed(self, row):
        if row >= len(self._action_widgets): return
        widgets = self._action_widgets[row]; kind = widgets["kind"].currentData()
        widgets["triples"].setEnabled(kind == "base"); widgets["doubles"].setEnabled(kind == "base")
        widgets["count"].setEnabled(kind == "top")
        widgets["cp_min"].setEnabled(kind != "imported"); widgets["cp_max"].setEnabled(kind != "imported")
        combo = widgets["source"]
        if kind == "imported":
            for index in range(combo.count()):
                combo.model().item(index).setEnabled(combo.itemData(index) in self.column_sources)
        else:
            for index in range(combo.count()):
                combo.model().item(index).setEnabled(combo.itemData(index) in self.probability_sources)
        self._save_configuration()

    def _action_config(self, row):
        if row >= len(getattr(self, "_action_widgets", [])): return {}
        widgets = self._action_widgets[row]
        return dict(enabled=widgets["check"].isChecked(), kind=widgets["kind"].currentData(),
                    count=widgets["count"].value(), start=widgets["start"].value(), end=widgets["end"].value(),
                    minimum_probability=widgets["cp_min"].value(), maximum_probability=widgets["cp_max"].value(),
                    triples=widgets["triples"].value(),
                    doubles=widgets["doubles"].value(), endings=[int(button.text()) for button in widgets["endings"] if button.isChecked()],
                    source=widgets["source"].currentData())

    def _remove_action(self):
        if self.action_table.rowCount() <= 1: return
        row = self.action_table.currentRow()
        if row < 0: row = self.action_table.rowCount() - 1
        configs = [self._action_config(i) for i in range(self.action_table.rowCount())]
        del configs[row]
        self._load_action_rows(configs)

    def _combination_changed(self, *_):
        if self.intersection.isChecked():
            self.keep_duplicates.setEnabled(False)
            self.keep_duplicates.setToolTip("La intersección produce un conjunto único de columnas.")
        else:
            self.keep_duplicates.setEnabled(True); self.keep_duplicates.setToolTip("")
        self._save_configuration()

    def _sources_for_kind(self, kind):
        return [(key, source) for key, source in self.probability_sources.items() if source.kind == kind]

    def _recalculate(self):
        sources = []
        for kind, spin in self.weight_spin.items():
            weight = spin.value()
            available = self._sources_for_kind(kind)
            if weight and not available:
                raise ValueError(f"No hay datos importados para {self.weight_status[kind].text().split(' · ')[0]}. Importa esa fuente o pon su peso a 0%.")
            if weight:
                sources.append((available[-1][1], weight))
        if not sources:
            raise ValueError("No hay fuentes auxiliares importadas. Elige Mercado o Popularidad en la fuente de porcentajes y pulsa Rellenar quiniela base.")
        values = weighted_probabilities(sources)
        self._populate_probability_table(values); self.matrix_origin = "weighted"; self._matrix_edited()
        self.base_status.setText("Porcentajes recalculados como media ponderada de las fuentes importadas. Se normalizó cada fila a 100%.")
        self._save_configuration()

    def _fill_base(self):
        system = self.window.system
        if not system: raise ValueError("Pulsa Nuevo para crear la quiniela de esta jornada.")
        if self.window.system_mode(system) != "normal": raise ValueError("La base automática solo modifica una quiniela Normal.")
        probabilities = self._matrix_values()
        if self.assignment_mode.currentData() == "manual":
            base, report = best_base(probabilities, self.triples.value(), self.doubles.value(), system.locks, system.base)
            mode = "cantidades elegidas por ti; partidos seleccionados por probabilidad"
        else:
            base, report = best_base_under_limit(probabilities, self.max_columns.value(), system.locks, system.base)
            for spin, value in ((self.triples, report["triples"]), (self.doubles, report["doubles"])):
                spin.blockSignals(True); spin.setValue(value); spin.blockSignals(False)
            mode = "cantidades y partidos elegidos por probabilidad conjunta bajo el límite"
            self._update_theoretical_count()
        parameters = json.loads(system.parameters)
        weights = {key: spin.value() for key, spin in self.weight_spin.items()}
        used_sources = ({key: [source.source for _source_key, source in self._sources_for_kind(key)] if weights[key] else [] for key in weights}
                        if self.matrix_origin == "weighted" else {})
        report.update(round_key=system.round_key, created_at=__import__("datetime").datetime.now().astimezone().isoformat(),
                      weights=weights if self.matrix_origin == "weighted" else {}, sources=used_sources,
                      weighted_recalculation_applied=self.matrix_origin == "weighted",
                      matrix_origin=self.matrix_origin, matrix_source=self.base_status.text(),
                      probabilities=[list(row) for row in probabilities])
        parameters["normal_base_generation"] = report
        updated = self.window.service.version(system, base=base, bets=(), origin=f"Base Normal · {mode}", parameters=json.dumps(parameters, ensure_ascii=False))
        self.repository.record_event("normal_base_generated", report)
        self.window.set_system(updated)
        self._save_configuration()
        self.base_status.setText(f"Base rellenada: {report['triples']} triples, {report['doubles']} dobles y {report['fixed']} fijos. Criterio: {mode}.")

    def _profile_items(self):
        return self.repository.setting(f"normal_sources:{self.current_round.key}", [])

    def _manage_sources(self):
        dialog = QDialog(self); dialog.setWindowTitle(f"Fuentes de porcentajes · {self.current_round.key}"); dialog.resize(620, 460)
        layout = QVBoxLayout(dialog)
        note = QLabel("Importa una matriz 1/X/2 UTF-8 con jornada, partidos, fuente y fecha. Clasificación, forma e historial requieren datos separados; no se derivan de mercado ni de popularidad.")
        note.setWordWrap(True); layout.addWidget(note)
        kind = QComboBox()
        kind.addItem("Clasificación", "classification"); kind.addItem("Últimas 5 jornadas", "form5"); kind.addItem("Historial", "history"); kind.addItem("Otra fuente de porcentajes", "custom")
        layout.addWidget(kind)
        listing = QTableWidget(0, 4); listing.setHorizontalHeaderLabels(("Tipo", "Fuente", "Captura", "Jornada")); listing.verticalHeader().hide(); listing.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); layout.addWidget(listing, 1)
        source_keys = list(self.probability_sources)
        for source_key in source_keys:
            source = self.probability_sources[source_key]
            row = listing.rowCount(); listing.insertRow(row)
            for column, value in enumerate((source.kind, source.source, source.captured_at, source.round_key)):
                listing.setItem(row, column, QTableWidgetItem(value))
            listing.item(row, 0).setData(Qt.ItemDataRole.UserRole, source_key)
        buttons = QHBoxLayout(); import_button = QPushButton("Importar CSV/TXT/JSON…"); use_button = QPushButton("Usar en fila activa"); done = QDialogButtonBox(QDialogButtonBox.StandardButton.Close); buttons.addWidget(import_button); buttons.addWidget(use_button); buttons.addStretch(1); buttons.addWidget(done); layout.addLayout(buttons)
        done.rejected.connect(dialog.reject); done.accepted.connect(dialog.accept)
        import_button.clicked.connect(lambda: self.window.safe(lambda: self._import_probability_source(kind.currentData(), dialog)))
        def use_selected_source():
            row = listing.currentRow()
            if row < 0:
                note.setText("Selecciona una fuente de la lista y vuelve a pulsar «Usar en fila activa».")
                return
            target = self.action_table.currentRow()
            if target < 0: target = 0
            source_key = listing.item(row, 0).data(Qt.ItemDataRole.UserRole)
            combo = self._action_widgets[min(target, len(self._action_widgets) - 1)]["source"]
            index = combo.findData(source_key)
            if index < 0:
                note.setText("Esta fuente no se puede usar como matriz de probabilidades.")
                return
            combo.setCurrentIndex(index)
            dialog.accept()
        use_button.clicked.connect(use_selected_source)
        dialog.exec()

    def _import_probability_source(self, source_kind, dialog=None):
        path, _ = QFileDialog.getOpenFileName(self, "Importar porcentajes", "", "CSV/TXT/JSON (*.csv *.txt *.json)")
        if not path: return
        source = import_probability_source(read_bytes(path), round_key=self.current_round.key,
                                          matches=self.current_round.matches, source_kind=source_kind, filename=path)
        items = [item for item in self._profile_items() if not (item["source"] == source.source and item["kind"] == source.kind)]
        items.append(asdict(source)); self.repository.set_setting(f"normal_sources:{self.current_round.key}", items)
        self.probability_sources[f"local:{source.source}:{source.kind}:{source.captured_at}"] = source
        self._refresh_availability(self.window.system)
        if dialog: dialog.accept()
        self.window.repository.record_event("normal_probability_source_imported", dict(round_key=source.round_key,
            source=source.source, captured_at=source.captured_at, kind=source.kind, file_name=Path(path).name,
            rows=14, sums_checked=True))

    def _import_columns(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar columnas 1/X/2", "", "TXT/CSV/JSON (*.txt *.csv *.json)")
        if not path: return
        columns = parse_columns_file(read_bytes(path))
        if len(columns) > 1_000_000: raise ValueError("Por seguridad, el gestor local limita la importación en memoria a 1.000.000 de columnas.")
        items = self.repository.setting(f"normal_column_sources:{self.current_round.key}", [])
        entry = dict(id=uuid.uuid4().hex, name=Path(path).name,
                     columns_sha256=hashlib.sha256("\n".join(columns).encode("ascii")).hexdigest(),
                     columns=list(columns))
        items.append(entry); self.repository.set_setting(f"normal_column_sources:{self.current_round.key}", items)
        self.column_sources[entry["id"]] = columns
        self.column_source_meta[entry["id"]] = {"file_name": entry["name"], "columns_sha256": entry["columns_sha256"]}
        self._update_source_combos(); self._save_configuration()
        self.repository.record_event("normal_columns_imported", dict(round_key=self.current_round.key,
            file_name=entry["name"], columns=len(columns)))

    def _view_selected_percentages(self):
        if not self._action_widgets: raise ValueError("No hay filas de acciones.")
        row = max(0, self.action_table.currentRow())
        key = self._action_widgets[min(row, len(self._action_widgets) - 1)]["source"].currentData()
        source = self.probability_sources.get(key)
        if source is None: raise ValueError("Selecciona una fuente de porcentajes en la columna «% de…».")
        dialog = QDialog(self); dialog.setWindowTitle(f"{source.source} · {self.current_round.key}"); dialog.resize(700, 440)
        layout = QVBoxLayout(dialog)
        label = QLabel(f"{source.source} · captura {source.captured_at} · {source.round_key}"); layout.addWidget(label)
        table = QTableWidget(14, 5); table.setHorizontalHeaderLabels(("#", "Partido", "1", "X", "2")); table.verticalHeader().hide(); table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (0, 2, 3, 4): table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        for i, match in enumerate(self.current_round.matches[:14]):
            for j, value in enumerate((f"{i+1:02}", f"{match.home} – {match.away}", *(f"{100*p:.2f}%" for p in source.values[i]))):
                item = QTableWidgetItem(value); item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable); table.setItem(i, j, item)
        layout.addWidget(table, 1); buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close); buttons.rejected.connect(dialog.reject); buttons.accepted.connect(dialog.accept); layout.addWidget(buttons); dialog.show()
        self.percentages_dialog = dialog

    def _show_help(self):
        QMessageBox.information(self, "Cómo funciona el generador Normal",
            "C.P. es el producto de las 14 probabilidades elegidas, calculado en logaritmos; supone independencia y no predice premios. Sus dos casillas fijan el mínimo y el máximo admitidos. «Núm. Colum.» conserva las primeras N; Desde/Hasta conserva ese rango inclusivo, numerado desde 1. Las terminaciones filtran la última cifra de esa posición antes de renumerar. Triples/Dobles crea una base con exactamente esas anchuras y ordena sus columnas con la fuente de la fila. Si mantienes duplicados se concatenan filas; si no, se hace unión exacta; Intersección conserva solo columnas comunes a todas las filas activas.")

    def _action_payloads(self):
        system = self.window.system
        if not system: raise ValueError("Pulsa Nuevo para crear una quiniela.")
        actions = []
        for row, widgets in enumerate(self._action_widgets):
            if not widgets["check"].isChecked(): continue
            kind = widgets["kind"].currentData(); source_key = widgets["source"].currentData()
            start, end, count = widgets["start"].value(), widgets["end"].value(), widgets["count"].value()
            if bool(start) != bool(end): raise ValueError(f"Fila {row+1}: completa Desde y Hasta, o deja ambas en 0.")
            if kind == "imported":
                columns = self.column_sources.get(source_key)
                if columns is None: raise ValueError(f"Fila {row+1}: importa y selecciona un fichero de columnas.")
                rank_start = start or 1; rank_end = end or min(count, len(columns))
                actions.append(dict(label=f"Fila {row+1} · fichero local", imported_columns=columns,
                                    rank_start=rank_start, rank_end=rank_end,
                                    endings=[int(b.text()) for b in widgets["endings"] if b.isChecked()],
                                    source_audit=self.column_source_meta.get(source_key, {})))
                continue
            source = self.probability_sources.get(source_key)
            if source is None: raise ValueError(f"Fila {row+1}: selecciona una fuente disponible.")
            if kind == "base":
                generated, decision = best_base(source.values, widgets["triples"].value(), widgets["doubles"].value(), system.locks, system.base)
                rank_end = math.prod(len(value) for value in generated)
                rank_start = start or 1
            else:
                generated = None; decision = None
                rank_end = end or count; rank_start = start or 1
            actions.append(dict(label=f"Fila {row+1} · {source.source}", probabilities=source.values,
                                base=generated, rank_start=rank_start, rank_end=rank_end,
                                endings=[int(b.text()) for b in widgets["endings"] if b.isChecked()],
                                minimum_probability=widgets["cp_min"].value(), maximum_probability=widgets["cp_max"].value(),
                                source=asdict(source),
                                base_decision=decision))
        if not actions: raise ValueError("Marca «Usar» en al menos una fila.")
        return actions

    def _choose_output(self):
        actions = self._action_payloads()
        path, selected = QFileDialog.getSaveFileName(self, "Guardar fichero generado", str(Path.home() / f"{self.current_round.key.replace('/', '-')}-columnas.txt"), "TXT de columnas (*.txt);;CSV de columnas (*.csv);;JSON de columnas (*.json)")
        if not path: return
        if not Path(path).suffix:
            path += ".csv" if selected.startswith("CSV") else ".json" if selected.startswith("JSON") else ".txt"
        estimates = sum(int(action["rank_end"]) for action in actions)
        if estimates > 1_000_000:
            fmt = Path(path).suffix.lower()
            bytes_per_column = 15 if fmt == ".txt" else 15 if fmt == ".csv" else len(json.dumps({"signs14": "1" * 14}, separators=(",", ":"))) + 1
            size_estimate = estimates * bytes_per_column
            if size_estimate >= 1_000_000_000: size_label = f"{size_estimate / 1_000_000_000:.2f} GB"
            elif size_estimate >= 1_000_000: size_label = f"{size_estimate / 1_000_000:.1f} MB"
            else: size_label = f"{size_estimate / 1_000:.0f} kB"
            answer = QMessageBox.warning(self, "Generación extensa", f"Se revisarán hasta {estimates:,} posiciones. Tamaño máximo aproximado del fichero: {size_label}; la unión o intersección puede reducirlo. El cálculo se puede cancelar y se escribe por bloques. ¿Continuar?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes: return
        self.worker = ActionWorker(path, actions, keep_duplicates=self.keep_duplicates.isChecked(), intersection=self.intersection.isChecked(), parent=self)
        self.worker.progress.connect(self._progress)
        self.worker.completed.connect(self._generation_finished)
        self.worker.failed.connect(self._generation_failed)
        self.worker.finished.connect(self._worker_finished)
        self.generate_file_button.setEnabled(False); self.cancel_action_button.setEnabled(True); self.action_progress.setValue(0)
        self.worker.start()

    def _progress(self, done, total, message):
        self.action_status.setText(message)
        self.action_progress.setMaximum(max(1, total)); self.action_progress.setValue(min(done, max(1, total)))

    def _generation_finished(self, report):
        self.last_report = report
        audit = dict(round_key=self.current_round.key, created_at=__import__("datetime").datetime.now().astimezone().isoformat(), **report)
        self.repository.record_event("normal_action_file_generated", audit)
        action_lines = "; ".join(f"{item['label']}: {item['accepted']:,} admitidas, {item['rejected_endings']:,} por terminación, {item['rejected_coefficient']:,} por C.P." for item in report["actions"])
        common = f" · coincidentes: {report['count_final']:,}" if report["intersection"] else ""
        self.action_status.setText(f"Generadas {report['count_final']:,} columnas · {report['combination']}{common} · repetidas eliminadas: {report['duplicates_removed']:,} · {report['elapsed_seconds']:.2f} s. {action_lines}")
        self.window.statusBar().showMessage(f"Fichero guardado: {report['path']}", 12000)

    def _generation_failed(self, message):
        self.action_status.setText(message)
        QMessageBox.warning(self, "No se pudo generar el fichero", message)

    def _worker_finished(self):
        self.generate_file_button.setEnabled(True); self.cancel_action_button.setEnabled(False)
        if self.worker: self.worker.deleteLater(); self.worker = None

    def _cancel_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel(); self.action_status.setText("Cancelando con seguridad… se conserva el archivo anterior.")
