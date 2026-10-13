"""Escritorio Qt en español: siete secciones y un sistema activo."""
import json
import shutil
import sqlite3
import threading
from dataclasses import asdict, replace
from datetime import datetime
from decimal import Decimal
from functools import partial
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from live_results import LiveMatch
from quiniela_ai_studio import __version__
from quiniela_ai_studio.application.services import SystemService
from quiniela_ai_studio.domain import engine
from quiniela_ai_studio.domain.models import round_from_dict, utcnow
from quiniela_ai_studio.infrastructure import files
from quiniela_ai_studio.infrastructure.integration import (
    fetch_round_sources,
    live_for_round,
    prepare_data,
    public_snapshot,
    read_legacy_systems,
    reconcile_import,
    scrutiny_from_cache,
)
from quiniela_ai_studio.infrastructure.providers import (
    migrate_legacy,
    scrutiny_record,
    text,
)

STYLE = """
QWidget {font-family: "DejaVu Sans", "Segoe UI"; font-size: 12px; color: #eaf4ff; background: #071a33;}
QLabel#brand {font-size:24px; font-weight:bold; color:#49dbff; background:#0b315c;}
QLabel#title {font-size:20px; font-weight:bold; color:#ffc83d;}
QLabel#muted {color:#8fb5d8;}
QWidget#plenoPanel {background:#0b2948; border:1px solid #28577d; border-radius:6px;}
QLabel#plenoTeam {background:transparent; color:#eaf4ff; font-weight:bold;}
QLabel#plenoPercentage {background:#123450; color:#8ec8e8; font-size:10px; border-radius:3px; padding:1px;}
QLabel#footer {background:#d89b12; color:#10213a; font-weight:bold; padding:7px;}
QWidget#hero {background:#0b315c;}
QPushButton {background:#123b65; border:1px solid #2d6b9e; border-radius:4px; padding:6px 9px; color:#eaf6ff;}
QPushButton:hover {background:#1a568c; border-color:#35c8ff;}
QPushButton:checked {background:#d82848; color:white; border:1px solid #ff6678; font-weight:bold;}
QPushButton#primary {background:#18864b; border-color:#35d27f; font-weight:bold;}
QPushButton:disabled {color:#7c92a8; background:#112b43; border-color:#24405b;}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {background:#eef7ff; color:#10243b; border:1px solid #53a8d2; padding:4px; border-radius:3px;}
QComboBox QAbstractItemView {background:#eef7ff; color:#10243b;}
QTableView {background:#0b2442; alternate-background-color:#10304f; gridline-color:#2a5b88; border:1px solid #2a5b88;}
QHeaderView::section {background:#123b65; padding:6px; color:#ffffff; font-weight:bold;}
QTabBar::tab {background:#102f52; color:#c9e8ff; padding:9px 13px; font-weight:bold;}
QTabBar::tab:selected {background:#087fbe; color:white;}
QScrollArea {border:none;}
QScrollBar:vertical {background:#102f52; width:14px;}
QScrollBar::handle:vertical {background:#3c88b8; min-height:30px;}
QScrollBar::handle:vertical:hover {background:#57d4ff;}
QGroupBox {border:1px solid #2a6698; border-radius:4px; margin-top:12px; padding-top:12px;}
QGroupBox::title {color:#57d4ff;}
QCheckBox::indicator {width:18px; height:18px; border:2px solid #86bfe8; border-radius:3px; background:#eef7ff;}
QCheckBox::indicator:checked {background:#18864b; border-color:#35d27f;}
QCheckBox::indicator:disabled {background:#24405b; border-color:#62768b;}
QLineEdit:disabled, QSpinBox:disabled {background:#173451; color:#8ba5be; border-color:#35536e;}
QSlider::groove:horizontal {height:7px; background:#123b65; border:1px solid #53a8d2; border-radius:3px;}
QSlider::handle:horizontal {background:#ffc83d; width:18px; margin:-6px 0; border-radius:5px;}
QSlider#optimizationSlider::handle:horizontal {background:#35d27f;}
QProgressBar {border:1px solid #2a6698; text-align:center;}
QProgressBar::chunk {background:#159881;}
QWidget#ballot QLabel {color:#082b70; background:#f6f7fb;}
QWidget#ballot {background:#f6f7fb; border-radius:5px;}
QWidget#ballot QPushButton {background:#fffafa; color:#b33448; border:1px solid #ffaaaa;}
QWidget#ballot QPushButton:checked {background:#d82848; color:white; border-color:#b12038;}
QWidget#ballot QPushButton:disabled {color:#a0a9b3; background:#edf0f4;}
"""



def money(cents):
    return f'{cents // 100},{cents % 100:02} €'


class RowsModel(QAbstractTableModel):
    def __init__(self, headers, rows=()):
        super().__init__()
        self.headers, self.rows = headers, list(rows)

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role==Qt.ItemDataRole.BackgroundRole and self.headers[index.column()] in ('Acierto / fallo','Pleno ahora'):
            value=str(self.rows[index.row()][index.column()])
            if value.startswith(('Acierto','Pleno acertado')):return QColor('#165c3b')
            if value.startswith(('Fallo','Goles fallados')):return QColor('#7f2338')
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            value=str(self.rows[index.row()][index.column()])
            header=self.headers[index.column()]
            if role==Qt.ItemDataRole.DisplayRole:
                if header=='Apuesta':return f'#{index.row()+1}'
                if header in ('Pleno','Tu signo','Resultado') and len(value)==2 and not set(value)-set('012M'):return value[0]+'–'+value[1]
            return value

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section] if orientation == Qt.Orientation.Horizontal else section+1

    def update_rows(self, rows):
        rows = list(rows)
        if rows == self.rows:
            return
        if len(rows) == len(self.rows):
            for i, (old, new) in enumerate(zip(self.rows, rows)):
                if old != new:
                    self.rows[i] = new
                    self.dataChanged.emit(self.index(i, 0), self.index(i, len(self.headers)-1))
        else:
            self.beginResetModel()
            self.rows = rows
            self.endResetModel()


class GenerationTask(QThread):
    completed = Signal(object)
    failed = Signal(str)
    progress = Signal(int, int)

    def __init__(self, version):
        super().__init__()
        self.version = version
        self.cancel_event = threading.Event()

    def run(self):
        try:
            result = engine.generate(self.version.base, self.version.plenos,
                                     self.cancel_event.is_set, self.progress.emit)
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class DataTask(QThread):
    completed = Signal(object)
    failed = Signal(str)
    status = Signal(str)

    def __init__(self, operation, parent):
        super().__init__(parent)
        self.operation = operation
        self.cancel_event = threading.Event()

    def run(self):
        try:
            result = self.operation(self.cancel_event.is_set, self.status.emit)
            if self.cancel_event.is_set() and not (isinstance(result,dict) and result.get('published')):
                if hasattr(result, 'directory'): shutil.rmtree(result.directory)
                raise engine.Cancelled('Operación cancelada; los datos anteriores se conservan.')
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    SECTIONS = ('Inicio', 'Normal', 'Optimizar', 'Análisis', 'Aciertos', 'Mis Sistemas', 'Configuración', 'Reducidas')

    def __init__(self, repository):
        super().__init__()
        self.repository = repository
        self.service = SystemService(repository)
        self.system = None
        self.worker = None
        self.data_worker = None
        self.data_buttons = []
        self.template_timer=QTimer(self);self.template_timer.setSingleShot(True);self.template_timer.setInterval(150);self.template_timer.timeout.connect(self.apply_pending_template)
        self.template_context=None
        self.optimization_result=None;self.optimization_source=None;self.optimization_dialog=None
        self.live_matches = None
        self.close_pending = False
        self.edit_buttons = []
        self.setWindowTitle(f'Quiniela AI Studio · v{__version__}')
        self.resize(1200, 820)
        self.setMinimumSize(900, 650)
        body = QWidget(); self.setCentralWidget(body)
        root = QVBoxLayout(body); root.setContentsMargins(12, 10, 12, 8)
        hero = QWidget(); hero.setObjectName('hero'); bar = QHBoxLayout(hero)
        logo = QLabel('QUINIELA  AI STUDIO'); logo.setObjectName('brand'); bar.addWidget(logo)
        bar.addStretch()
        self.data_button('↻ Descargar datos', self.download_data, bar, primary=True)
        self.export_button = self.button('Guardar apuestas (TXT)', self.export_txt, bar, primary=True)
        self.button('TuLotero',self.open_tulotero,bar)
        self.button('Mis sistemas', lambda: self.navigation.setCurrentRow(5), bar)
        root.addWidget(hero)
        self.tabs = QTabBar(); self.tabs.setExpanding(False)
        for name in self.SECTIONS:self.tabs.addTab(name)
        root.addWidget(self.tabs)
        self.navigation = QListWidget(); self.navigation.addItems(self.SECTIONS); self.navigation.hide()
        self.navigation.currentRowChanged.connect(self.tabs.setCurrentIndex)
        self.tabs.currentChanged.connect(self.navigation.setCurrentRow)
        bar = QHBoxLayout()
        self.button('‹ Anterior', lambda:self.move_round(-1), bar)
        self.round_picker = QComboBox(); self.round_picker.setMinimumWidth(150)
        bar.addWidget(self.round_picker)
        self.button('Siguiente ›', lambda:self.move_round(1), bar)
        self.button('En curso',self.go_current,bar);bar.addStretch()
        self.system_label = QLabel(); bar.addWidget(self.system_label);root.addLayout(bar)
        self.metadata = QLabel(); self.metadata.setObjectName('muted'); self.metadata.setWordWrap(True); root.addWidget(self.metadata)
        self.splitter=QSplitter(Qt.Orientation.Horizontal)
        self.ballot=QWidget();self.ballot.setMinimumWidth(450);QVBoxLayout(self.ballot)
        self.splitter.addWidget(self.ballot)
        self.pages=QStackedWidget();self.pages.setMinimumWidth(360);self.splitter.addWidget(self.pages)
        self.splitter.setSizes([480,700]);root.addWidget(self.splitter,1)
        for name in self.SECTIONS:
            page=QWidget();page_layout=QVBoxLayout(page)
            title=QLabel(name);title.setObjectName('title');page_layout.addWidget(title)
            self.pages.addWidget(page)
        self.footer = QLabel();self.footer.setObjectName('footer');self.footer.setWordWrap(True);root.addWidget(self.footer)
        self.build_home(); self.build_builder(); self.build_optimize(); self.build_analysis()
        self.build_evaluation(); self.build_systems(); self.build_settings();self.build_reductions()
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.currentRowChanged.connect(self.ensure_live_updates)
        self.navigation.currentRowChanged.connect(self.construction_page_changed)
        self.round_picker.currentIndexChanged.connect(self.select_round)
        self.navigation.setCurrentRow(0)
        self.load_rounds()
        QShortcut(QKeySequence('Ctrl+Z'), self, activated=lambda: self.safe(self.undo))

    def page_layout(self, index):
        return self.pages.widget(index).layout()

    def safe(self, fn):
        try:
            return fn()
        except (ValueError, OSError, KeyError, TypeError, sqlite3.Error, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, 'No se pudo completar la acción', str(exc))

    def button(self, label, fn, layout, primary=False, editable=False):
        button = QPushButton(label)
        if primary: button.setObjectName('primary')
        button.clicked.connect(lambda: self.safe(fn))
        layout.addWidget(button)
        if editable: self.edit_buttons.append(button)
        return button

    def table(self, headers, layout):
        view = QTableView(); model = RowsModel(headers); view.setModel(model)
        view.setAlternatingRowColors(True); view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        view.verticalHeader().setDefaultSectionSize(27)
        layout.addWidget(view, 1)
        return view, model

    def load_rounds(self, preferred=None):
        self.round_picker.blockSignals(True); self.round_picker.clear()
        for round_ in self.repository.rounds():
            self.round_picker.addItem(round_.key + (' · simulación' if round_.mode == 'simulation' else ''), round_.key)
        if preferred is None:
            preferred = self.repository.setting('selected_round')
        index = self.round_picker.findData(preferred) if preferred else -1
        if index < 0:
            current = next((r.key for r in self.repository.rounds() if r.mode == 'current'), None)
            index = self.round_picker.findData(current) if current else 0
        self.round_picker.setCurrentIndex(max(0, index)); self.round_picker.blockSignals(False)
        self.select_round()

    @property
    def round(self):
        return self.repository.round(self.round_picker.currentData())

    def select_round(self, *_):
        if not self.round_picker.currentData(): return
        self.repository.set_setting('selected_round', self.round_picker.currentData())
        self.template_timer.stop()
        mode='reduced' if self.navigation.currentRow()==7 else 'normal'
        self.system=self.saved_builder(mode)
        self.restore_builder_controls()
        self.choose_reduction_positions()
        self.restore_filter_controls()
        self.result_input.setText('-'*14)
        self.result_pleno.clear()
        self.final_check.setChecked(False)
        self.eval_model.update_rows([])
        self.eval_summary.setText('Selecciona resultados para esta jornada.')
        self.live_matches = None
        self.live_pleno_summary.setText('Pleno actual: pendiente')
        self.live_model.update_rows([])
        cached = self.repository.setting('live:' + self.round.key)
        self.live_status.setText('Sin marcador guardado para esta jornada.')
        if cached:
            try:self.restore_live()
            except ValueError as exc:self.live_status.setText(str(exc))
        self.reset_manual_inputs()
        self.ensure_live_updates()
        self.refresh()
        if mode=='reduced' and not self.system and self.round.editable:self.construction_page_changed(7)

    def refresh(self):
        round_ = self.round
        self.update_source_status()
        view_round = round_from_dict(json.loads(self.system.round_snapshot)) if self.system and self.system.round_snapshot else round_
        self.system_label.setText(f'{"REDUCIDA" if self.construction_mode()=="reduced" else "NORMAL"} · {self.system.name} · v{self.system.revision}' if self.system else 'Ninguna quiniela abierta')
        modes = dict(simulation='DEMO FICTICIA · datos de ejemplo', current='EN CURSO · puedes editar', past='ANTERIOR · solo consulta', future='FUTURA · consulta')
        mode_label = modes[round_.mode] if round_.mode != 'current' or round_.editable else 'SOLO CONSULTA · jornada pasada'
        self.metadata.setText(f'{mode_label} · {view_round.source}\nDatos usados: {datetime.fromisoformat(view_round.captured_at).astimezone():%d/%m/%Y %H:%M} · Precio por apuesta: {money(view_round.price_cents)} (referencia local)')
        self.metadata.setToolTip(f'Versión de reglas: {view_round.rules_version}\nProveedor: {view_round.source}')
        quantity = self.system.quantity if self.system else 0
        pending = sum(b.quantity for b in self.system.bets if not b.pleno) if self.system else 0
        params=json.loads(self.system.parameters) if self.system else {}
        verification=params.get('reduction_verification') or params.get('optimization_report',{}).get('after')
        guarantee=f' · cobertura {verification["status"]}, mínimo {verification["minimum_hits"] if verification["minimum_hits"] is not None else "NO VERIFICADO"} dentro del universo' if verification else ' · cobertura aún no verificada'
        self.footer.setText(f'{quantity:,} apuestas · {money(self.system.cost(round_) if self.system else 0)} · {pending} sin Pleno{guarantee} · Premio económico no garantizado')
        self.home_info.setText(f'{round_.key}\n15 partidos · {len(self.repository.systems(round_.key))} quinielas guardadas\nPrecio por apuesta: {money(round_.price_cents)} por apuesta. Guardar un archivo no envía ni paga la apuesta.')
        self.data_info.setText('Datos guardados: ' + (self.repository.setting('data_directory') or 'todavía no has añadido datos') + '\nWIN1X2 aporta partidos y premios. Quinielista aporta elecciones de otros jugadores y marcadores.')
        self.rule_price.setValue(round_.price_cents)
        busy = bool((self.filter_job and self.filter_job.isRunning()) or (self.worker and self.worker.isRunning()) or (self.data_worker and self.data_worker.isRunning()))
        for button in self.edit_buttons:
            button.setEnabled(round_.editable and not busy)
        generating=bool(self.worker and self.worker.isRunning())
        if not generating:
            self.progress.setValue(100 if self.system and self.system.bets else 0)
        self.progress.setFormat('%p%' if generating or (self.system and self.system.bets) else 'Sin desarrollo generado')
        self.filter_group.setEnabled(round_.editable and not ((self.worker and self.worker.isRunning()) or (self.data_worker and self.data_worker.isRunning())))
        self.update_filter_controls()
        self.quick_conditions_slider.setEnabled(round_.editable and not ((self.worker and self.worker.isRunning()) or (self.data_worker and self.data_worker.isRunning())))
        system = self.system
        number=json.loads(system.parameters).get('reduction_choice',json.loads(system.parameters).get('reduction',self.reduction_picker.currentData())) if system else None
        self.ballot_title.setText(f'BASE PARA REDUCIDA {number}' if self.construction_mode()=='reduced' else 'QUINIELA NORMAL')
        self.coverage.setEnabled(bool(system and self.construction_mode()=='normal' and round_.editable and not busy))
        self.differentiation.setEnabled(bool(system and round_.editable and not busy))
        self.pleno_mode.setEnabled(bool(system and round_.editable and not busy))
        self.update_budget_capacity()
        for i, match in enumerate(view_round.matches[:14]):
            kickoff=match.kickoff[:10]+' '+match.kickoff[10:] if len(match.kickoff)==15 else match.kickoff
            self.match_labels[i].setText(f'{i+1:02}  {match.home} – {match.away}')
            self.match_labels[i].setToolTip(f'{match.home} – {match.away}\n{kickoff}')
            snapshot = view_round.snapshot('sport'); public = view_round.snapshot('public')
            fmt = lambda snap: ' / '.join(f'{100*v:.0f}' for v in snap.values[i]) if snap else 'Sin datos'
            self.prob_labels[i].setText(f'{fmt(snapshot)}   |   {fmt(public)}')
            self.match_labels[i].setToolTip(f'{match.home} – {match.away}\n{kickoff}\nDeportiva 1/X/2: {fmt(snapshot)}\nPúblico 1/X/2: {fmt(public)}')
            for sign, button in self.sign_buttons[i].items():
                button.blockSignals(True); button.setChecked(bool(system and sign in system.base[i])); button.blockSignals(False)
                button.setEnabled(bool(system and round_.editable and not system.locks[i] and not busy))
            lock = self.lock_buttons[i]; lock.blockSignals(True)
            lock.setChecked(bool(system and system.locks[i])); lock.setText('Fijo' if lock.isChecked() else 'Libre')
            lock.setEnabled(bool(system and round_.editable and not busy)); lock.blockSignals(False)
        for i, combo in enumerate(self.pleno_combos):
            pending=system.goal_masks if system else ('','')
            combo.blockSignals(True); combo.setCurrentText(pending[i][0] if pending[i] else '—')
            combo.setEnabled(bool(system and round_.editable and not busy)); combo.blockSignals(False)
        pleno_match=view_round.matches[14]
        self.pleno_match_label.setText(f'Pleno al 15 · {pleno_match.home} – {pleno_match.away}')
        for side,buttons in enumerate(self.goal_buttons):
            for goal,button in buttons.items():
                button.setChecked(bool(system and goal in system.goal_masks[side]))
                button.setEnabled(bool(system and round_.editable and not busy))
        self.pleno_selection_info.setText(f'{engine.size(system.base):,} columnas × {len(system.plenos)} Plenos = {engine.size(system.base)*len(system.plenos):,} apuestas\nCoste si juegas todas: {money(engine.size(system.base)*len(system.plenos)*view_round.price_cents)} · {len(system.plenos)} parejas de goles' if system and system.plenos else 'Elige al menos un gol para el local y otro para el visitante.\nPuedes marcar varias casillas. M significa 3 goles o más.')
        self.preview_model.update_rows([(b.column,b.pleno or '—',b.quantity) for b in system.bets[:100]] if system else [])
        self.preview_info.setText(f'{quantity:,} apuestas listas. Pulsa Guardar apuestas (TXT) para sacar el archivo.' if quantity else 'Elige los signos y los goles del Pleno y pulsa Generar debajo del boleto.' if system else 'Pulsa Nuevo para empezar una quiniela.')
        self.name_input.blockSignals(True); self.name_input.setText(system.name if system else ''); self.name_input.blockSignals(False)
        self.name_input.setEnabled(bool(system and round_.editable and not busy))
        self.builder_info.setText(f'Apuestas posibles: {engine.size(system.base)*len(system.plenos):,} · {sum(len(p)==1 for p in system.base)} fijos / {sum(len(p)==2 for p in system.base)} dobles / {sum(len(p)==3 for p in system.base)} triples\nCoste si juegas todas: {money(engine.size(system.base)*len(system.plenos)*view_round.price_cents)} · apuestas guardadas: {system.quantity:,}' if system else 'Pulsa Nuevo y elige los signos de cada partido.')
        self.update_system_list()
        self.update_export_controls()
        self.analysis_info.setText(self.analysis_text())
        def percentages(kind,index):
            snap=view_round.snapshot(kind)
            return ' / '.join(f'{100*v:.1f}' for v in snap.values[index]) if snap else 'Sin datos'
        self.analysis_model.update_rows([(f'{i+1}. {m.home} – {m.away}',percentages('sport',i),percentages('public',i)) for i,m in enumerate(view_round.matches[:14])])
        self.optimize_info.setToolTip(f'Identificador de contenido: {system.hash}' if system else '')
        self.optimize_info.setText(f'{system.quantity:,} apuestas · coste {money(system.cost(round_))}' if system else 'Abre una quiniela en Mis Sistemas.')
        self.refresh_reduction()
        self.update_data_buttons()

    def build_home(self):
        layout = self.page_layout(0)
        self.home_info = QLabel(); self.home_info.setWordWrap(True); layout.addWidget(self.home_info)
        row = QHBoxLayout()
        self.button('Crear quiniela normal', self.new_system, row, primary=True, editable=True)
        self.button('Crear reducida',lambda:self.navigation.setCurrentRow(7),row,editable=True)
        layout.addLayout(row);row=QHBoxLayout()
        self.button('Probar ejemplo de 6 apuestas', self.example_system, row, editable=True)
        self.button('Consultar aciertos', lambda: self.navigation.setCurrentRow(4), row)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.data_button('Descargar / actualizar datos', self.download_data, row, primary=True)
        self.data_button('Importar datos locales', self.import_win1x2, row)
        self.button('En curso', self.go_current, row)
        layout.addLayout(row)
        note = QLabel('Empieza con un ejemplo o crea tu quiniela. Elige 1 si gana el local, X si empatan y 2 si gana el visitante.\nEl ejemplo usa partidos inventados y funciona sin Internet. IA y reducción avanzada todavía no están disponibles.')
        note.setWordWrap(True); layout.addWidget(note); layout.addStretch()

    def new_system(self):
        if not self.round.editable: raise ValueError('Jornada de consulta.')
        mode='reduced' if self.navigation.currentRow()==7 else 'normal'
        self.set_system(self.service.new(self.round,'Mi reducida' if mode=='reduced' else 'Mi quiniela normal',mode=mode))
        if mode=='reduced':self.rebuild_reduced_template()
        else:self.navigation.setCurrentRow(1)

    def example_system(self):
        self.new_system()
        self.system = self.service.edit(self.system, ('1X','1','1X2')+('1',)*11, (False,)*14, 'M1')
        self.refresh(); self.start_generation()

    def build_builder(self):
        layout = self.ballot.layout()
        self.ballot_title=QLabel('QUINIELA NORMAL');self.ballot_title.setObjectName('title');layout.addWidget(self.ballot_title)
        row = QHBoxLayout(); self.name_input = QLineEdit(); self.name_input.setPlaceholderText('Nombre de tu quiniela')
        self.name_input.editingFinished.connect(lambda: self.safe(self.rename))
        row.addWidget(self.name_input)
        self.button('Nuevo', self.new_system, row, editable=True)
        self.button('Deshacer', self.undo, row, editable=True); layout.addLayout(row)
        self.builder_info = QLabel(); self.builder_info.setWordWrap(True);self.builder_info.setMinimumHeight(38); layout.addWidget(self.builder_info)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        grid_widget = QWidget(); grid = QGridLayout(grid_widget); grid.setSpacing(1);grid.setContentsMargins(6,4,6,4)
        grid_widget.setObjectName('ballot')
        for col, title in enumerate(('Partidos', '1', 'X', '2', 'Bloq.')):
            grid.addWidget(QLabel(title), 0, col)
        self.match_labels=[]; self.prob_labels=[]; self.sign_buttons=[]; self.lock_buttons=[]
        for i in range(14):
            label=QLabel(); label.setMinimumWidth(160);label.setStyleSheet("font-size:11px;"); label.setWordWrap(True); self.match_labels.append(label); grid.addWidget(label,i+1,0)
            prob=QLabel();prob.hide();self.prob_labels.append(prob)
            signs={}
            for j, sign in enumerate('1X2'):
                button=QPushButton(sign); button.setCheckable(True); button.setFixedSize(27,20); button.setStyleSheet("padding: 1px;")
                button.setAccessibleName(f'Partido {i+1}, signo {sign}')
                button.clicked.connect(partial(self.toggle_sign,i,sign)); grid.addWidget(button,i+1,j+1); signs[sign]=button
            self.sign_buttons.append(signs)
            lock=QPushButton('Bloquear');lock.setCheckable(True);lock.setFixedSize(44,20);lock.setStyleSheet('padding:1px 5px;')
            lock.clicked.connect(partial(self.toggle_lock,i));grid.addWidget(lock,i+1,4);self.lock_buttons.append(lock)
        grid.setColumnStretch(0,1)
        scroll.setWidget(grid_widget);layout.addWidget(scroll,1)
        row=QHBoxLayout();self.pleno_match_label=QLabel();self.pleno_match_label.setWordWrap(True);self.pleno_match_label.setStyleSheet('color:#ffc83d; font-weight:bold;');row.addWidget(self.pleno_match_label)
        self.pleno_combos=[]
        for _ in range(2):
            combo=QComboBox();combo.addItems(['—','0','1','2','M']);combo.currentIndexChanged.connect(self.change_pleno)
            combo.hide();self.pleno_combos.append(combo)
        layout.addLayout(row)
        row=QHBoxLayout();row.addWidget(QLabel('Modo del Pleno'));self.pleno_mode=QComboBox();self.pleno_mode.addItem('Manual','manual');self.pleno_mode.addItem('Automático según fuente','auto');self.pleno_mode.addItem('Diversificado: varias parejas manuales','diversified');self.pleno_mode.currentIndexChanged.connect(self.schedule_template);row.addWidget(self.pleno_mode,1);layout.addLayout(row)
        self.goal_buttons=[]
        self.goal_percentages=[]
        self.pleno_panel=QWidget();self.pleno_panel.setObjectName('plenoPanel')
        pleno_grid=QGridLayout(self.pleno_panel);pleno_grid.setContentsMargins(10,8,10,8);pleno_grid.setHorizontalSpacing(9);pleno_grid.setVerticalSpacing(3)
        for side,label_text in enumerate(('Local','Visitante')):
            team_label=QLabel(label_text);team_label.setObjectName('plenoTeam');pleno_grid.addWidget(team_label,side*3,0,2,1);buttons={};percentages={}
            for column,goal in enumerate('012M',1):
                button=QPushButton(goal);button.setCheckable(True);button.setFixedSize(48,27);button.setToolTip('3 goles o más' if goal=='M' else f'{goal} goles')
                button.clicked.connect(lambda checked=False,i=side,g=goal:self.toggle_goal(i,g))
                pleno_grid.addWidget(button,side*3,column);buttons[goal]=button
                percentage=QLabel('—');percentage.setObjectName('plenoPercentage');percentage.setFixedWidth(48);percentage.setAlignment(Qt.AlignmentFlag.AlignCenter);pleno_grid.addWidget(percentage,side*3+1,column);percentages[goal]=percentage
            self.goal_buttons.append(buttons)
            self.goal_percentages.append(percentages)
        pleno_grid.setRowMinimumHeight(2,7);pleno_grid.setColumnStretch(5,1);layout.addWidget(self.pleno_panel)
        self.pleno_selection_info=QLabel();self.pleno_selection_info.setWordWrap(True);layout.addWidget(self.pleno_selection_info)
        left_layout=layout;layout=self.page_layout(1)
        row=QHBoxLayout();row.addWidget(QLabel('Añadir dobles y triples (0–10)'))
        self.coverage=QSlider(Qt.Orientation.Horizontal);self.coverage.setRange(0,10);row.addWidget(self.coverage,1)
        self.coverage_label=QLabel('0');row.addWidget(self.coverage_label);self.coverage.valueChanged.connect(lambda v:self.coverage_label.setText(str(v)));self.coverage.valueChanged.connect(self.schedule_template)
        self.coverage.sliderPressed.connect(self.schedule_template)
        layout.addLayout(row)
        note=QLabel('La barra amplía signos. Solo en Pleno Automático amplía también goles. Nivel 10: hasta 3.456 columnas × 16 Plenos; los bloqueos no cambian. En Manual/Diversificado marca los goles tú, sin reasignación automática.')
        note.setWordWrap(True);note.setObjectName('muted');layout.addWidget(note)
        row=QHBoxLayout();row.addWidget(QLabel('Elegir signos según'))
        self.ranking_source=QComboBox();self.ranking_source.addItem('Mercado: casas de apuestas','sport');self.ranking_source.addItem('Popularidad: Quinielista','public');row.addWidget(self.ranking_source,1)
        self.button('Descargar porcentajes',self.refresh_system_sources,row,editable=True).setToolTip('Descarga los porcentajes de los 14 partidos y del Pleno para la jornada abierta, sin cambiar tus apuestas.');layout.addLayout(row)
        self.source_status=QLabel();self.source_status.setWordWrap(True);layout.addWidget(self.source_status)
        self.ranking_source.currentIndexChanged.connect(self.ranking_source_changed)
        self.differentiation=QSlider(Qt.Orientation.Horizontal);self.differentiation.setRange(0,10)
        row=QHBoxLayout();row.addWidget(QLabel('Diferenciación del público'));row.addWidget(self.differentiation,1);self.differentiation_label=QLabel('0');row.addWidget(self.differentiation_label);layout.addLayout(row)
        self.differentiation.valueChanged.connect(lambda value:self.differentiation_label.setText(str(value)));self.differentiation.valueChanged.connect(self.schedule_template)
        note=QLabel('Las barras actualizan el boleto automáticamente. Diferenciación 0: seguir la fuente elegida. Subir requiere Mercado y popularidad; favorece signos menos populares en relación con su probabilidad. Son pesos de selección, no probabilidades ni rentabilidad: puede reducir tus aciertos y no garantiza grandes premios. El Pleno multiplica las apuestas.')
        note.setWordWrap(True);note.setObjectName('muted');layout.addWidget(note)
        layout=left_layout
        row=QHBoxLayout();self.generate_button=self.button('Generar',self.start_generation,row,primary=True,editable=True)
        self.cancel_button=self.button('Cancelar',self.cancel_generation,row);self.cancel_button.setEnabled(False)
        self.progress=QProgressBar();self.progress.setValue(0);row.addWidget(self.progress,1);layout.addLayout(row)
        preview=self.page_layout(1)
        self.preview_info=QLabel();self.preview_info.setWordWrap(True);preview.addWidget(self.preview_info)
        self.preview_view,self.preview_model=self.table(('Columna','Pleno','Cantidad'),preview)
        note=QLabel('El boleto permanece visible a la izquierda. La vista muestra hasta 100 filas; el archivo exportado conserva todas las apuestas.');note.setWordWrap(True);preview.addWidget(note)
        row=QHBoxLayout();self.button('Guardar apuestas (TXT)',self.export_txt,row);self.button('Guardar quiniela (JSON)',self.export_json,row);preview.addLayout(row)
        self.full_export_button=self.data_button('Guardar todas las combinaciones…',self.export_development,preview)

    def rename(self):
        if self.system and self.name_input.text().strip()!=self.system.name:
            self.system=self.service.version(self.system,name=self.name_input.text().strip());self.refresh()

    def toggle_sign(self,i,sign,*_):
        def action():
            base=list(self.system.base);selected=set(base[i]);selected.symmetric_difference_update({sign})
            if not selected: raise ValueError('Mantén al menos un signo en cada partido.')
            base[i]=''.join(s for s in '1X2' if s in selected)
            self.system=self.service.edit(self.system,base,self.system.locks,self.system.pleno)
        self.safe(action);self.refresh()

    def toggle_lock(self,i,*_):
        locks=list(self.system.locks);locks[i]=not locks[i]
        def action():self.set_system(self.service.edit(self.system,self.system.base,locks,self.system.pleno))
        self.safe(action);self.refresh()

    def toggle_goal(self,side,goal):
        if not self.system:return
        masks=list(self.system.goal_masks)
        masks[side]=''.join(g for g in '012M' if (g in masks[side]) != (g==goal))
        pairs=tuple(a+b for a in masks[0] for b in masks[1])
        self.safe(lambda:self.set_system(self.service.edit(self.system,self.system.base,self.system.locks,
                                                          pairs[0] if len(pairs)==1 else '',pleno_choices=masks)))

    def change_pleno(self,*_):
        if not self.system:return
        pleno=''.join(c.currentText() for c in self.pleno_combos)
        if '—' in pleno:pleno=''
        choices=[c.currentText().replace('—','') for c in self.pleno_combos]
        self.safe(lambda:self.set_system(self.service.edit(self.system,self.system.base,self.system.locks,pleno,pleno_choices=choices)))

    def set_system(self,system):
        changed=not self.system or not system or self.system.system_id!=system.system_id
        self.system=system
        self.remember_builder()
        if changed:self.template_timer.stop();self.restore_builder_controls();self.restore_filter_controls();self.choose_reduction_positions()
        self.refresh()

    @staticmethod
    def system_mode(system):
        if not system:return 'normal'
        params=json.loads(system.parameters)
        return params.get('construction_mode','reduced' if 'reduction' in params else 'normal')

    def construction_mode(self):
        return self.system_mode(self.system) if self.system else ('reduced' if self.navigation.currentRow()==7 else 'normal')

    def remember_builder(self):
        if not self.system:return
        key='builder_modes:'+self.system.round_key
        saved=self.repository.setting(key,{})
        saved[self.system_mode(self.system)]=self.system.system_id
        self.repository.set_setting(key,saved)

    def saved_builder(self,mode):
        key=self.repository.setting('builder_modes:'+self.round.key,{}).get(mode)
        if key:
            candidate=self.repository.load(key)
            if candidate.round_key==self.round.key and self.system_mode(candidate)==mode:return candidate
        systems=[s for s in self.repository.systems(self.round.key) if self.system_mode(s)==mode and (mode!='reduced' or json.loads(s.parameters).get('construction_mode')=='reduced')]
        return systems[-1] if systems else None

    def restore_builder_controls(self):
        params=json.loads(self.system.parameters) if self.system else {}
        for slider,value in ((self.coverage,params.get('level',0)),(self.differentiation,params.get('differentiation_level',0)),(self.reduction_pleno_level,params.get('level',0)),(self.reduction_differentiation,params.get('differentiation_level',0))):
            slider.blockSignals(True);slider.setValue(value);slider.blockSignals(False)
        self.coverage_label.setText(str(self.coverage.value()));self.differentiation_label.setText(str(self.differentiation.value()))
        self.reduction_diff_label.setText(str(self.reduction_differentiation.value()));self.reduction_level_label.setText(str(self.reduction_pleno_level.value()))
        for combo in (self.ranking_source,self.reduction_source):
            combo.blockSignals(True);combo.setCurrentIndex(max(0,combo.findData(params.get('kind','sport'))));combo.blockSignals(False)
        self.pleno_mode.blockSignals(True);self.pleno_mode.setCurrentIndex(max(0,self.pleno_mode.findData(params.get('pleno_mode','manual'))));self.pleno_mode.blockSignals(False)
        self.reduction_picker.blockSignals(True);self.reduction_picker.setCurrentIndex(params.get('reduction_choice',params.get('reduction',1))-1);self.reduction_picker.blockSignals(False)

    def construction_page_changed(self,index):
        self.template_timer.stop()
        self.update_export_controls()
        if index not in (1,7) or not self.round_picker.currentData():return
        mode='reduced' if index==7 else 'normal'
        if self.system and self.system_mode(self.system)==mode:
            self.restore_builder_controls();self.refresh();return
        self.remember_builder()
        candidate=self.saved_builder(mode)
        if not candidate and mode=='reduced' and self.round.editable:
            candidate=self.service.new(self.round,'Mi reducida',mode='reduced')
            self.set_system(candidate);self.rebuild_reduced_template();return
        self.set_system(candidate)

    def ranking_source_changed(self,index):
        if hasattr(self,'reduction_source'):
            self.reduction_source.blockSignals(True);self.reduction_source.setCurrentIndex(index);self.reduction_source.blockSignals(False)
        self.update_source_status();self.schedule_template()

    def schedule_template(self,*_):
        if not self.system or self.navigation.currentRow() not in (1,7) or not self.round.editable:return
        if self.export_busy():return
        mode=self.construction_mode()
        if (mode=='normal') != (self.navigation.currentRow()==1):return
        self.template_context=(self.system.system_id,self.system.round_key,mode,self.system.revision)
        if hasattr(self,'reduction_differentiation'):
            self.reduction_differentiation.blockSignals(True);self.reduction_differentiation.setValue(self.differentiation.value());self.reduction_differentiation.blockSignals(False)
            self.reduction_diff_label.setText(str(self.differentiation.value()));self.reduction_level_label.setText(str(self.reduction_pleno_level.value()))
        self.template_timer.start()
        self.update_export_controls()

    def apply_pending_template(self):
        if not self.system or self.template_context!=(self.system.system_id,self.round.key,self.construction_mode(),self.system.revision):
            self.update_export_controls();return
        if self.export_busy() or not self.round.editable:return
        try:
            if self.construction_mode()=='reduced':self.rebuild_reduced_template()
            else:self.apply_template()
        except (ValueError,KeyError) as exc:self.background_status('El boleto anterior se conserva. '+str(exc));self.update_export_controls()

    def rebuild_reduced_template(self,*_):
        self.template_timer.stop()
        if not self.system or self.construction_mode()!='reduced':return
        try:
            updated=self.service.reduced_template(self.system,self.reduction_picker.currentData(),self.ranking_source.currentData(),
                pleno_level=self.reduction_pleno_level.value(),differentiation=self.differentiation.value(),include_pleno=self.pleno_mode.currentData()=='auto',pleno_mode=self.pleno_mode.currentData())
            self.set_system(updated);self.choose_reduction_positions()
        except ValueError as exc:
            self.background_status(str(exc));self.reduction_info.setText(str(exc))

    def undo(self):
        if self.system:self.set_system(self.service.undo(self.system));self.restore_builder_controls();self.refresh()

    def apply_template(self):
        self.template_timer.stop()
        if not self.system:raise ValueError('Pulsa Nuevo para crear una quiniela.')
        kind=self.ranking_source.currentData()
        if not self.frozen_round().snapshot(kind):raise ValueError('Esta fuente no tiene porcentajes para esta quiniela. Pulsa Descargar porcentajes. No se sustituirán por valores inventados.')
        has_pleno=bool(self.frozen_round().snapshot(kind).pleno_values)
        self.set_system(self.service.template(self.system,self.coverage.value(),kind,include_pleno=self.pleno_mode.currentData()=='auto',differentiation=self.differentiation.value(),pleno_mode=self.pleno_mode.currentData()))
        if not has_pleno:self.background_status('Signos aplicados. Esta fuente no publica porcentajes del Pleno; se conserva tu selección de goles, sin inventar resultados.')

    def refresh_system_sources(self):
        if not self.system:raise ValueError('Pulsa Nuevo para crear una quiniela.')
        if self.round.season=='DEMO':
            self.background_status('La demo tiene porcentajes ficticios, no descargables. Pulsa Descargar datos en la cabecera y selecciona una jornada real.');return
        context=self.system
        round_=self.round
        self.start_background('sources',context,lambda cancel,status:fetch_round_sources(round_,self.repository.path.parent/'source-cache',cancelled=cancel))

    def update_source_status(self,*_):
        snapshot=self.frozen_round().snapshot(self.ranking_source.currentData())
        for side,labels in enumerate(self.goal_percentages):
            for i,goal in enumerate('012M'):
                labels[goal].setText(f'{snapshot.pleno_values[side][i]:.1%}' if snapshot and snapshot.pleno_values else '—')
                labels[goal].setToolTip(f'{snapshot.source} · goles {goal}' if snapshot and snapshot.pleno_values else 'Sin porcentajes del Pleno para esta fuente; descarga datos actualizados.')
        if snapshot:
            captured=datetime.fromisoformat(snapshot.captured_at).astimezone()
            self.source_status.setText(f'{self.round.key} · {snapshot.source}\nCaptura: {captured:%d/%m/%Y %H:%M}. Datos guardados en esta versión de tu quiniela; no son una actualización automática.')
        else:
            self.source_status.setText(f'{self.round.key} · Sin porcentajes de esta fuente. Descárgalos antes de aplicar recomendaciones. No se usa 40/30/30 ni un modelo oculto.')
        if hasattr(self,'reduction_source'):self.reduction_source.setToolTip(self.source_status.text())

    def start_generation(self):
        if not self.system:raise ValueError('Pulsa Nuevo para crear una quiniela.')
        pending=self.template_timer.isActive()
        self.template_timer.stop()
        if pending:self.apply_pending_template()
        if self.construction_mode()=='reduced':return self.apply_reduction()
        if self.worker and self.worker.isRunning():return
        if self.data_worker and self.data_worker.isRunning():raise ValueError('Espera a que termine la actualización de datos.')
        if not self.system.plenos:raise ValueError('En el Pleno, elige los goles del local y del visitante: 0, 1, 2 o M (3 o más). Después pulsa Generar.')
        if engine.size(self.system.base)*len(self.system.plenos)>engine.MAX_GENERATED:raise ValueError('Has elegido más de 100.000 apuestas. Quita algunos dobles o triples, o usa Guardar todas las combinaciones para escribirlas en un archivo.')
        version=self.system
        self.worker=GenerationTask(version)
        self.worker.completed.connect(lambda bets:self.safe(lambda:self.generation_done(version,bets)))
        self.worker.failed.connect(lambda message:self.statusBar().showMessage(message,12000))
        self.worker.progress.connect(lambda done,total:self.progress.setValue(int(done/total*100)))
        self.worker.finished.connect(self.generation_finished)
        self.worker.start();self.cancel_button.setEnabled(True);self.refresh()

    def generation_done(self,version,bets):
        created=self.service.generated(version,bets)
        if self.round.key==created.round_key and self.system and self.system.system_id==created.system_id:
            self.set_system(created)
        self.statusBar().showMessage(f'{len(bets):,} apuestas guardadas en {created.round_key}.',10000)

    def generation_finished(self):
        self.cancel_button.setEnabled(False);self.refresh()

    def cancel_generation(self):
        if self.worker:self.worker.cancel_event.set()

    def build_optimize(self):
        outer=self.page_layout(2)
        scroll=QScrollArea();scroll.setWidgetResizable(True)
        content=QWidget();layout=QVBoxLayout(content);scroll.setWidget(content)
        self.quick_level=None;self.configuring_filters=False
        self.filter_job=None;self.filter_epoch=0;self.filter_pending=False
        self.filter_timer=QTimer(self);self.filter_timer.setSingleShot(True);self.filter_timer.setInterval(150);self.filter_timer.timeout.connect(self.start_live_filter)
        progressive=QGroupBox('1. Ajusta cuántas apuestas conservar')
        progressive_layout=QVBoxLayout(progressive)
        self.quick_conditions_slider=QSlider(Qt.Orientation.Horizontal);self.quick_conditions_slider.setObjectName('optimizationSlider');self.quick_conditions_slider.setRange(0,10);self.quick_conditions_slider.setValue(10)
        self.quick_conditions_slider.setTickPosition(QSlider.TickPosition.TicksBelow);self.quick_conditions_slider.setTickInterval(1)
        self.quick_conditions_slider.setAccessibleName('Ajustes de optimización: cero menos apuestas, diez máximo de apuestas')
        progressive_layout.addWidget(self.quick_conditions_slider)
        ends=QHBoxLayout();ends.addWidget(QLabel('0 · menos apuestas'));ends.addStretch();ends.addWidget(QLabel('10 · máximo de apuestas'));progressive_layout.addLayout(ends)
        self.quick_description=QLabel('Nivel 10 / 10');self.quick_description.setWordWrap(True);progressive_layout.addWidget(self.quick_description)
        outer.addWidget(progressive)
        self.optimize_info=QLabel();self.optimize_info.setWordWrap(True);outer.addWidget(self.optimize_info)
        outer.addWidget(scroll,1)
        self.methods_status=QLabel('La garantía combinatoria se verifica dentro de un universo concreto. No garantiza un premio económico.')
        self.methods_status.setWordWrap(True)
        self.filter_group=QGroupBox('Condiciones · puedes ajustarlas a mano')
        grid=QGridLayout(self.filter_group);self.filter_ranges={};self.filter_checks={}
        self.filter_tips={'variants':'Cuenta cuántos partidos llevan X o 2 en cada apuesta.', 'x_count':'Cuenta los empates (signo X) en cada apuesta.', 'changes':'Cuenta las veces que cambia el signo de un partido al siguiente. Por ejemplo, 1X2 tiene dos cambios.', 'max_one_run':'Máximo de victorias locales consecutivas que permites.', 'two_count':'Cuenta las victorias del visitante (signo 2) en cada apuesta.', 'x_distance':'Cuenta las posiciones entre dos X consecutivas: dos X juntas tienen distancia 1. Con cero o una X, esta condición no descarta la apuesta.', 'coincidences':'Cuenta cuántos signos coinciden con la otra quiniela que escribas abajo.', 'max_x_run':'Máximo de signos X consecutivos que permites.', 'max_two_run':'Máximo de signos 2 consecutivos que permites.'}
        self.filter_defaults={'variants':(0,14),'x_count':(0,14),'two_count':(0,14),'changes':(0,13),'x_distance':(1,13),'coincidences':(0,14)}
        for i,(key,label_text) in enumerate((('variants','Total de X y 2'),('x_count','Número de empates (X)'),('two_count','Victorias visitantes (2)'),('changes','Cambios entre signos'),('x_distance','Separación entre X'),('coincidences','Parecido a otra quiniela'))):
            lower,upper=self.filter_defaults[key]
            check=QCheckBox(label_text);check.setProperty('filterLabel',label_text);check.setToolTip(self.filter_tips[key]);self.filter_checks[key]=check
            check.toggled.connect(self.filters_changed);grid.addWidget(check,i,0)
            minimum=QSpinBox();minimum.setRange(lower,upper);minimum.setValue(lower);minimum.setMaximumWidth(70)
            maximum=QSpinBox();maximum.setRange(lower,upper);maximum.setValue(upper);maximum.setMaximumWidth(70)
            self.filter_ranges[key]=(minimum,maximum)
            grid.addWidget(QLabel('Desde'),i,1);grid.addWidget(minimum,i,2);grid.addWidget(QLabel('Hasta'),i,3);grid.addWidget(maximum,i,4)
        self.filter_max_one=QSpinBox();self.filter_max_one.setRange(1,14);self.filter_max_one.setValue(14)
        self.filter_max_x=QSpinBox();self.filter_max_x.setRange(1,14);self.filter_max_x.setValue(14)
        self.filter_max_two=QSpinBox();self.filter_max_two.setRange(1,14);self.filter_max_two.setValue(14)
        for row,key,label_text,control in ((6,'max_one_run','Locales seguidos (1)',self.filter_max_one),(7,'max_x_run','Empates seguidos (X)',self.filter_max_x),(8,'max_two_run','Visitantes seguidos (2)',self.filter_max_two)):
            check=QCheckBox(label_text);check.setProperty('filterLabel',label_text);check.setToolTip(self.filter_tips[key]);self.filter_checks[key]=check
            check.toggled.connect(self.filters_changed);grid.addWidget(check,row,0);grid.addWidget(QLabel('Máximo'),row,1);grid.addWidget(control,row,2)
        self.filter_reference=QLineEdit();self.filter_reference.setMaxLength(14);self.filter_reference.setPlaceholderText('Ejemplo: 11111111111111 (14 signos)')
        self.filter_reference.setToolTip('Solo se usa con «Parecido a otra quiniela». Cuenta cuántos signos coinciden con esta columna.')
        grid.addWidget(QLabel('La otra quiniela'),9,0);grid.addWidget(self.filter_reference,9,1,1,4)
        self.filter_reset=QPushButton('Quitar todas las condiciones');self.filter_reset.clicked.connect(self.reset_filters)
        self.filter_feedback=QLabel();self.filter_feedback.setWordWrap(True)
        layout.addWidget(self.filter_group);layout.addStretch()
        outer.addWidget(self.filter_feedback);outer.addWidget(self.filter_reset)
        self.budget_group=QGroupBox('2. Ajusta el resultado a tu presupuesto')
        budget_outer=QVBoxLayout(self.budget_group);budget_layout=QHBoxLayout();budget_outer.addLayout(budget_layout);budget_layout.addWidget(QLabel('1. Máximo (€)'))
        self.budget=QDoubleSpinBox();self.budget.setRange(0,100000);self.budget.setDecimals(2);self.budget.setValue(10);budget_layout.addWidget(self.budget)
        self.budget_capacity=QLabel();budget_layout.addWidget(self.budget_capacity)
        row=QHBoxLayout();row.addWidget(QLabel('2. Objetivo'));self.portfolio_objective=QComboBox()
        for label,key in (('Automático recomendado','auto'),('Máxima probabilidad','probability'),('Máxima cobertura 13+/12+','coverage'),('Valor esperado: no disponible','expected')):self.portfolio_objective.addItem(label,key)
        self.portfolio_objective.model().item(3).setEnabled(False);row.addWidget(self.portfolio_objective,1);budget_outer.addLayout(row)
        self.budget_apply=self.button('3. Optimizar mis apuestas',self.optimize,row,primary=True,editable=True)
        advanced_toggle=QCheckBox('Parámetros avanzados');budget_outer.addWidget(advanced_toggle)
        advanced=QWidget();advanced_layout=QGridLayout(advanced);advanced.hide();budget_outer.addWidget(advanced);advanced_toggle.toggled.connect(advanced.setVisible)
        self.portfolio_seed=QSpinBox();self.portfolio_seed.setRange(0,2_000_000_000)
        self.portfolio_time=QSpinBox();self.portfolio_time.setRange(1,300);self.portfolio_time.setValue(10)
        self.portfolio_scope=QComboBox();self.portfolio_scope.addItem('Base completa (incluye descartadas)','base');self.portfolio_scope.addItem('Solo candidatas tras condiciones','candidates')
        self.portfolio_channel=QComboBox();self.portfolio_channel.addItem('Genérico: mínimo 1 por Pleno',1);self.portfolio_channel.addItem('TuLotero sencillas: mínimo 2 por Pleno',2)
        self.portfolio_pleno_model=QCheckBox('Incluir Pleno en probabilidad: independencia explícita de goles')
        for i,(label_text,control) in enumerate((('Semilla',self.portfolio_seed),('Tiempo de búsqueda (s)',self.portfolio_time),('Universo',self.portfolio_scope),('Canal',self.portfolio_channel))):advanced_layout.addWidget(QLabel(label_text),i,0);advanced_layout.addWidget(control,i,1)
        advanced_layout.addWidget(self.portfolio_pleno_model,4,0,1,2)
        self.portfolio_summary=QLabel('La propuesta se revisa antes de aplicar. Valor esperado desactivado: faltan recaudación y modelo de premios fiable.');self.portfolio_summary.setWordWrap(True);budget_outer.addWidget(self.portfolio_summary)
        self.budget.valueChanged.connect(self.update_budget_capacity)
        outer.addWidget(self.budget_group)
        self.budget_apply.setToolTip('Optimiza el desarrollo de origen respetando las condiciones. Muestra una propuesta sin cambiar tus apuestas hasta que la apliques.')
        outer.addWidget(self.methods_status)
        for minimum,maximum in self.filter_ranges.values():
            minimum.valueChanged.connect(self.manual_filters_changed);maximum.valueChanged.connect(self.manual_filters_changed)
        for control in (self.filter_max_one,self.filter_max_x,self.filter_max_two):control.valueChanged.connect(self.manual_filters_changed)
        self.filter_reference.textChanged.connect(self.manual_filters_changed)
        self.quick_conditions_slider.valueChanged.connect(self.configure_quick_conditions)
        self.update_filter_controls()

    def restore_filter_controls(self):
        """Restore saved optimization settings without recalculating on load."""
        self.filter_timer.stop();self.filter_epoch+=1
        if self.filter_job:self.filter_job.cancel_event.set()
        self.configuring_filters=True
        params=json.loads(self.system.parameters) if self.system else {}
        saved=params.get('filter_spec',{})
        level=params.get('quick_level')
        self.quick_level=level if type(level) is int and 0<=level<=10 else None
        self.quick_conditions_slider.blockSignals(True);self.quick_conditions_slider.setValue(self.quick_level if self.quick_level is not None else 10);self.quick_conditions_slider.blockSignals(False)
        automatic={'variants','x_count','two_count','changes','max_one_run','max_x_run','max_two_run'}
        for key,(minimum,maximum) in self.filter_ranges.items():
            limits=tuple(saved.get(key,self.filter_defaults[key]))
            minimum.setValue(limits[0]);maximum.setValue(limits[1])
            self.filter_checks[key].setChecked((self.quick_level is not None and key in automatic) or limits!=self.filter_defaults[key])
        for key,control in (('max_one_run',self.filter_max_one),('max_x_run',self.filter_max_x),('max_two_run',self.filter_max_two)):
            control.setValue(saved.get(key,14));self.filter_checks[key].setChecked((self.quick_level is not None) or control.value()!=14)
        self.filter_reference.setText(saved.get('reference',''))
        self.filter_checks['coincidences'].setChecked(bool(saved.get('reference')))
        self.quick_description.setText(f'Nivel {self.quick_level} / 10' if self.quick_level is not None else 'Condiciones personalizadas' if saved else 'Nivel 10 / 10')
        self.filter_feedback.setText('Primero pulsa Generar debajo del boleto.' if not self.system or (not self.system.bets and not saved) else '')
        self.configuring_filters=False;self.update_filter_controls()

    def configure_quick_conditions(self, level):
        """Populate filter controls; moving the slider never edits a saved system."""
        from quiniela_ai_studio.domain.filters import quick_conditions
        spec=quick_conditions(level)
        self.configuring_filters=True
        self.quick_level=level
        active={'variants','x_count','two_count','changes','max_one_run','max_x_run','max_two_run'}
        for key,check in self.filter_checks.items():check.setChecked(key in active)
        for key,(minimum,maximum) in self.filter_ranges.items():
            limits=getattr(spec,key)
            minimum.setValue(limits[0]);maximum.setValue(limits[1])
        self.filter_max_one.setValue(spec.max_one_run)
        self.filter_max_x.setValue(spec.max_x_run);self.filter_max_two.setValue(spec.max_two_run)
        self.quick_description.setText(f'Nivel {level} / 10')
        self.configuring_filters=False
        self.update_filter_controls();self.schedule_live_filter()

    def filters_changed(self):
        self.update_filter_controls();self.manual_filters_changed()

    def manual_filters_changed(self):
        if self.configuring_filters:return
        self.quick_level=None
        self.quick_description.setText('Condiciones personalizadas')
        self.schedule_live_filter()

    def update_filter_controls(self):
        """Make activation explicit; inactive limits remain editable only after selection."""
        for check in self.filter_checks.values():
            check.setText(('✓ ' if check.isChecked() else '')+check.property('filterLabel'))
        for key,controls in self.filter_ranges.items():
            for control in controls:control.setEnabled(self.filter_checks[key].isChecked())
        self.filter_max_one.setEnabled(self.filter_checks['max_one_run'].isChecked())
        self.filter_max_x.setEnabled(self.filter_checks['max_x_run'].isChecked())
        self.filter_max_two.setEnabled(self.filter_checks['max_two_run'].isChecked())
        self.filter_reference.setEnabled(self.filter_checks['coincidences'].isChecked())
        ready=bool(self.system and self.system.bets)
        if self.round_picker.currentData():
            self.budget_apply.setEnabled(ready and self.round.editable and not self.filter_timer.isActive() and self.filter_job is None)

    def reset_filters(self):
        self.configuring_filters=True
        self.quick_level=None
        self.quick_description.setText('Sin condiciones')
        self.quick_conditions_slider.blockSignals(True);self.quick_conditions_slider.setValue(10);self.quick_conditions_slider.blockSignals(False)
        for check in self.filter_checks.values():check.setChecked(False)
        self.configuring_filters=False
        self.update_filter_controls();self.schedule_live_filter()

    def apply_filters_ui(self):
        try:
            self.apply_filters()
        except ValueError as exc:
            self.filter_feedback.setText(f'{exc} Puedes corregir los datos o desmarcar el filtro; no se han cambiado tus apuestas.')

    def filter_spec(self):
        if self.filter_checks['coincidences'].isChecked() and not self.filter_reference.text().strip():
            raise ValueError('Para comparar, escribe la otra quiniela con 14 signos (por ejemplo, 11111111111111), o desmarca «Parecido a otra quiniela».')
        from quiniela_ai_studio.domain.filters import BasicFilters
        return BasicFilters(**{key:(a.value(),b.value()) if self.filter_checks[key].isChecked() else self.filter_defaults[key] for key,(a,b) in self.filter_ranges.items()},
                          max_one_run=self.filter_max_one.value() if self.filter_checks['max_one_run'].isChecked() else 14,
                          max_x_run=self.filter_max_x.value() if self.filter_checks['max_x_run'].isChecked() else 14,
                          max_two_run=self.filter_max_two.value() if self.filter_checks['max_two_run'].isChecked() else 14,
                          reference=self.filter_reference.text().upper() if self.filter_checks['coincidences'].isChecked() else '')

    def apply_filters(self):
        if not self.system:raise ValueError('Abre primero una quiniela.')
        self.filter_timer.stop();self.filter_epoch+=1
        if self.filter_job:self.filter_job.cancel_event.set()
        spec=self.filter_spec()
        candidates=self.service.origin_bets(self.system)[1]
        before=sum(b.quantity for b in candidates)
        bets=spec.apply(candidates)
        if bets!=self.system.bets:
            self.set_system(self.service.save_filtered(self.system,spec,bets,candidates,quick_level=self.quick_level))
        self.statusBar().showMessage(f'Has conservado {self.system.quantity} de {before} apuestas. Puedes recuperar las anteriores con Recuperar apuestas anteriores.',15000)

    def schedule_live_filter(self):
        if self.configuring_filters or not self.system or self.close_pending or not self.round.editable:return
        if not self.system.bets and not json.loads(self.system.parameters).get('filter_spec'):
            self.filter_feedback.setText('Primero pulsa Generar debajo del boleto.');return
        self.filter_epoch+=1
        if self.filter_job:self.filter_job.cancel_event.set()
        self.filter_timer.start()
        self.filter_feedback.setText('Actualizando apuestas y coste…')
        self.budget_apply.setEnabled(False)
        self.update_export_controls()
        self.update_data_buttons()

    def start_live_filter(self):
        if self.close_pending or not self.system:return
        if self.filter_job is not None:
            self.filter_pending=True;return
        try:
            spec=self.filter_spec()
            candidates=self.service.origin_bets(self.system)[1]
        except ValueError as exc:
            self.filter_feedback.setText(str(exc));self.update_export_controls();return
        self.filter_timer.stop();self.filter_pending=False
        context=(self.filter_epoch,self.system,spec,candidates,self.quick_level)
        job=DataTask(lambda cancel,status:spec.apply(candidates,cancel),self)
        self.filter_job=job
        job.completed.connect(lambda bets:self.live_filter_done(context,bets))
        job.failed.connect(lambda message:self.live_filter_failed(context,message))
        job.finished.connect(lambda:self.live_filter_finished(job))
        job.start();self.refresh()

    def live_filter_done(self,context,bets):
        epoch,system,spec,candidates,level=context
        if self.close_pending or epoch!=self.filter_epoch or self.system!=system:return
        try:
            parameters=json.loads(system.parameters)
            if bets!=system.bets or parameters.get('filter_spec')!=json.loads(json.dumps(spec.parameters())) or parameters.get('quick_level')!=level:
                self.set_system(self.service.save_filtered(system,spec,bets,candidates,quick_level=level,allow_empty=True))
            self.filter_feedback.setText('No quedan apuestas. Sube el nivel o cambia las condiciones.' if not bets else '')
        except ValueError as exc:
            self.filter_feedback.setText(str(exc))

    def live_filter_failed(self,context,message):
        if not self.close_pending and context[0]==self.filter_epoch:
            self.filter_feedback.setText(message)

    def live_filter_finished(self,job):
        if self.filter_job is job:self.filter_job=None
        if job:job.deleteLater()
        if self.close_pending:self.close();return
        self.refresh()
        if self.filter_pending:
            self.filter_pending=False;self.start_live_filter()

    def restore_origin(self):
        if not self.system:raise ValueError('Abre primero un sistema.')
        self.set_system(self.service.restore_origin(self.system))

    def optimize(self):
        if not self.system:raise ValueError('No hay un sistema activo.')
        cents=int(Decimal(self.budget.cleanText().replace(',','.'))*100)
        source=self.system
        bets,base,config,frozen,spec=self.service.optimization_input(source,cents,
            objective=self.portfolio_objective.currentData(),seed=self.portfolio_seed.value(),max_seconds=self.portfolio_time.value(),
            universe_scope=self.portfolio_scope.currentData(),min_per_pleno=self.portfolio_channel.currentData(),
            include_pleno_probability=self.portfolio_pleno_model.isChecked())
        from quiniela_ai_studio.domain.portfolio import optimize_portfolio
        def operation(cancel,status):
            admitted=set(spec.apply(bets,cancel))
            def progress(done,total):
                if done==total or done%max(1,total//100)==0:status(f'Optimización: {done:,}/{total:,} · cálculo real; permite cancelar')
            result=optimize_portfolio(bets,base,config,frozen.snapshot('sport'),public=frozen.snapshot('public'),eligible=lambda b:b in admitted,cancelled=cancel,progress=progress)
            result.report.update(run_id=__import__('uuid').uuid4().hex,created_at=utcnow(),round_key=source.round_key,input_hash=source.hash,
                input_revision=source.revision,base=list(base),filter_spec=spec.parameters(),sources=[asdict(s) for s in frozen.snapshots])
            return result
        self.start_background('portfolio',source,operation)

    def update_budget_capacity(self,*_):
        if not self.round_picker.currentData() or not hasattr(self,'budget_capacity'):return
        price=self.frozen_round().price_cents
        cents=int(Decimal(self.budget.cleanText().replace(',','.'))*100)
        self.budget_capacity.setText(f'Hasta {cents//price} apuestas · {money(price)}/apuesta')

    def open_tulotero(self,bets=None,round_=None):
        if bets is None:
            if self.export_busy() or self.template_timer.isActive():raise ValueError('Espera a que terminen los cálculos antes de preparar las apuestas actuales.')
            if not self.system or not self.system.bets:raise ValueError('Genera o aplica una selección antes de preparar boletos.')
            bets=self.system.bets
        from quiniela_ai_studio.ui.portfolio_dialogs import tulotero_dialog
        self.tulotero_window=tulotero_dialog(self,tuple(bets),round_ or self.frozen_round());self.tulotero_window.show()

    def verify_current_coverage(self):
        if not self.system or not self.system.bets:raise ValueError('Abre apuestas para verificar cobertura.')
        source=self.system
        origin,_=self.service.origin_bets(source)
        base=tuple(json.loads(origin.parameters).get('base',origin.base))
        from quiniela_ai_studio.domain.coverage import make_universe, verify_coverage
        universe=make_universe(base,self.frozen_round().snapshot('sport'),limit=10000,seed=self.portfolio_seed.value())
        self.start_background('verification',source,lambda cancel,status:verify_coverage(source.bets,universe,cancelled=cancel,
            progress=lambda done,total:status(f'Verificando {done}/{total} escenarios')))

    def build_analysis(self):
        layout=self.page_layout(3);self.analysis_info=QLabel();self.analysis_info.setWordWrap(True);layout.addWidget(self.analysis_info)
        self.analysis_view,self.analysis_model=self.table(('Partido','Mercado / fuente deportiva (%)','Popularidad en Quinielista (%)'),layout)
        self.ai_status=QLabel('IA: pendiente. La app todavía no aprende de los resultados ni hace pronósticos propios. Aquí puedes consultar los datos que has descargado.');self.ai_status.setWordWrap(True);layout.addWidget(self.ai_status)
        note=QLabel('Cada grupo muestra 1 / X / 2. Los datos deportivos estiman resultados; las elecciones de otros jugadores muestran qué signos prefieren.');note.setWordWrap(True);layout.addWidget(note)
        self.button('Verificar cobertura de mis apuestas',self.verify_current_coverage,layout)
        self.button('Ver modelo explícito de las 16 parejas del Pleno',self.show_pleno_model,layout)

    def show_pleno_model(self):
        from quiniela_ai_studio.domain.coverage import pleno_joint
        values=pleno_joint(self.frozen_round().snapshot('sport'))
        dialog=QDialog(self);dialog.setWindowTitle('Modelo aproximado del Pleno · independencia de goles');dialog.resize(500,550)
        layout=QVBoxLayout(dialog);label=QLabel('Probabilidades calculadas multiplicando marginales local y visitante. Hipótesis de independencia, no una distribución conjunta observada/calibrada. No modifica tus goles.');label.setWordWrap(True);layout.addWidget(label)
        _,model=self.table(('Goles local','Goles visitante','Probabilidad aproximada'),layout)
        model.update_rows([(pair[0],pair[1],f'{p:.2%}') for pair,p in values.items()]);self.pleno_model_window=dialog;dialog.show()

    def analysis_text(self):
        round_=self.round;system=self.system
        if system and system.round_snapshot: round_=round_from_dict(json.loads(system.round_snapshot))
        lines=[]
        for kind,label in (('sport','Mercado / fuente deportiva'),('public','Popularidad en Quinielista')):
            snap=round_.snapshot(kind)
            lines.append(f'{label}: {snap.source if snap else "sin datos disponibles"}')
        if system:
            params=json.loads(system.parameters)
            if params.get('differentiation_level',0):
                lines.append(f'Diferenciación del público: {params["differentiation_level"]}/10. Selección original con puntuación mercado/popularidad. Los porcentajes deportivos de esta tabla siguen siendo los del proveedor; los pesos no son probabilidades ni premios esperados. Puede reducir aciertos. No hay validación retrospectiva de este criterio.')
            lines.extend((f'Combinaciones de signos diferentes: {len({b.column for b in system.bets}):,}',f'Total de apuestas: {system.quantity:,}','Puedes consultar cómo se creó en el historial de operaciones.'))
            if round_.snapshot('sport') and system.bets:
                lines.append(f'Probabilidad calculada de acertar los 14 con estas combinaciones: {engine.probability_mass(system.bets,round_.snapshot("sport")):.6%} (supone partidos independientes y no incluye el Pleno).')
        lines.append('La app no calcula todavía ganancias previstas ni verifica garantías de aciertos.')
        return '\n\n'.join(lines)

    def build_evaluation(self):
        layout=self.page_layout(4)
        self.live_worker=None;self.live_context=None
        self.live_timer=QTimer(self);self.live_timer.setInterval(60000);self.live_timer.timeout.connect(self.fetch_live_automatically)
        row=QHBoxLayout();self.auto_live=QCheckBox('Marcador automático');self.auto_live.setChecked(self.repository.setting('automatic_live',True));row.addWidget(self.auto_live)
        self.live_interval=QComboBox()
        for seconds in (30,60,120):self.live_interval.addItem(f'Cada {seconds} segundos',seconds)
        saved_interval=self.live_interval.findData(self.repository.setting('live_interval_seconds',60))
        self.live_interval.setCurrentIndex(saved_interval if saved_interval>=0 else 1);row.addWidget(self.live_interval)
        self.manual_mode=QCheckBox('Introducir resultados a mano');row.addWidget(self.manual_mode);layout.addLayout(row)
        self.live_status=QLabel('El marcador se actualizará al abrir esta sección.');self.live_status.setWordWrap(True);layout.addWidget(self.live_status)
        self.live_pleno_summary=QLabel('Pleno actual: pendiente');self.live_pleno_summary.setWordWrap(True);layout.addWidget(self.live_pleno_summary)
        self.live_view,self.live_model=self.table(('Partido','Marcador','Resultado','Tu signo','Acierto / fallo','Estado'),layout)
        self.live_view.verticalHeader().hide();self.live_view.verticalHeader().setDefaultSectionSize(23)
        for column in range(1,6):self.live_view.horizontalHeader().setSectionResizeMode(column,QHeaderView.ResizeMode.ResizeToContents)
        self.manual_container=QScrollArea();self.manual_container.setWidgetResizable(True);manual=QWidget();manual_layout=QGridLayout(manual);self.manual_container.setWidget(manual);self.manual_container.setMaximumHeight(270)
        self.manual_labels=[];self.manual_signs=[]
        for i in range(14):
            label=QLabel();self.manual_labels.append(label);manual_layout.addWidget(label,i,0)
            combo=QComboBox();combo.addItems(['-','1','X','2']);combo.currentIndexChanged.connect(self.manual_results_changed);self.manual_signs.append(combo);manual_layout.addWidget(combo,i,1)
        manual_layout.addWidget(QLabel('Pleno · goles local / visitante'),14,0)
        goal_row=QHBoxLayout();self.manual_goals=[]
        for _ in range(2):
            combo=QComboBox();combo.addItems(['—','0','1','2','M']);combo.currentIndexChanged.connect(self.manual_results_changed);self.manual_goals.append(combo);goal_row.addWidget(combo)
        manual_layout.addLayout(goal_row,14,1)
        self.result_input=QLineEdit('-'*14);self.result_input.setMaxLength(14);self.result_input.hide()
        self.result_pleno=QLineEdit();self.result_pleno.setMaxLength(2);self.result_pleno.hide()
        self.final_check=QCheckBox('Estos resultados son definitivos');manual_layout.addWidget(self.final_check,15,0,1,2)
        self.button('Cargar resultados guardados',self.read_cached_scrutiny,manual_layout)
        layout.addWidget(self.manual_container);self.manual_container.hide()
        self.eval_summary=QLabel('Abre una quiniela con apuestas para ver tus aciertos.');self.eval_summary.setWordWrap(True);self.eval_summary.setMinimumHeight(48);layout.addWidget(self.eval_summary)
        self.eval_view,self.eval_model=self.table(('Apuesta','Pleno','Copias','Aciertos','Fallos','Pendientes','Máximo','Pleno ahora'),layout)
        self.eval_view.verticalHeader().hide()
        for column in range(1,8):self.eval_view.horizontalHeader().setSectionResizeMode(column,QHeaderView.ResizeMode.ResizeToContents)
        self.eval_view.selectionModel().currentRowChanged.connect(self.display_match_comparison)
        self.eval_view.setToolTip('Aciertos y fallos actuales pueden cambiar en partidos en juego. Máximo usa solo fallos definitivos. El Pleno exige 14 aciertos más los goles del partido 15.')
        self.manual_eval_timer=QTimer(self);self.manual_eval_timer.setSingleShot(True);self.manual_eval_timer.setInterval(150);self.manual_eval_timer.timeout.connect(self.refresh_manual_evaluation)
        self.result_input.textChanged.connect(self.schedule_manual_evaluation);self.result_pleno.textChanged.connect(self.schedule_manual_evaluation);self.final_check.toggled.connect(self.schedule_manual_evaluation)
        self.auto_live.toggled.connect(self.ensure_live_updates);self.manual_mode.toggled.connect(self.switch_scrutiny_mode);self.live_interval.currentIndexChanged.connect(self.ensure_live_updates)

    def reset_manual_inputs(self):
        for i,combo in enumerate(self.manual_signs):
            combo.blockSignals(True);combo.setCurrentIndex(0);combo.blockSignals(False)
            match=self.round.matches[i];self.manual_labels[i].setText(f'{i+1:02} · {match.home} – {match.away}')
        for combo in self.manual_goals:combo.blockSignals(True);combo.setCurrentIndex(0);combo.blockSignals(False)

    def set_manual_results(self,result,pleno):
        for i,combo in enumerate(self.manual_signs):
            combo.blockSignals(True);combo.setCurrentText(result[i]);combo.blockSignals(False)
        for i,combo in enumerate(self.manual_goals):
            combo.blockSignals(True);combo.setCurrentText(pleno[i] if len(pleno)==2 else '—');combo.blockSignals(False)
        self.result_input.setText(result);self.result_pleno.setText(pleno)

    def manual_results_changed(self):
        self.result_input.setText(''.join(combo.currentText() for combo in self.manual_signs))
        goals=''.join(combo.currentText() for combo in self.manual_goals)
        self.result_pleno.setText('' if '—' in goals else goals)

    def schedule_manual_evaluation(self):
        if self.manual_mode.isChecked():self.manual_eval_timer.start()

    def refresh_manual_evaluation(self):
        if self.close_pending or not self.manual_mode.isChecked():return
        try:self.evaluate()
        except ValueError as exc:self.eval_summary.setText(str(exc))

    def switch_scrutiny_mode(self):
        manual=self.manual_mode.isChecked();self.manual_container.setVisible(manual);self.live_view.setVisible(not manual)
        self.ensure_live_updates()
        if manual:self.schedule_manual_evaluation()
        elif self.live_matches:self.evaluate_live()

    def render_scrutiny(self,outcome,actual_pleno,pleno_final):
        selected=self.eval_view.currentIndex().row()
        old_key=self.eval_model.rows[selected][:2] if 0<=selected<len(self.eval_model.rows) else None
        if self.manual_mode.isChecked():self.live_pleno_summary.setText('Pleno manual: '+(actual_pleno[0]+'–'+actual_pleno[1] if actual_pleno else 'pendiente'))
        rows=[]
        for r in outcome['rows']:
            if not r['pleno']:p15='Sin selección'
            elif not actual_pleno:p15='Pendiente'
            elif r['full15_hit']:p15='Pleno acertado'
            elif r['pleno_hit']:p15='Goles sí; faltan 14' if outcome['definitive'] and r['hits']<14 else 'Goles coinciden' + ('' if pleno_final else ' (en juego)')
            else:p15='Goles fallados' + ('' if pleno_final else ' (en juego)')
            rows.append((r['column'],r['pleno'] or '—',r['quantity'],r['hits'],r['misses'],r['pending'],r['maximum'],p15))
        self.eval_model.update_rows(rows)
        if old_key:
            selected=next((i for i,row in enumerate(rows) if row[:2]==old_key),0)
            self.eval_view.setCurrentIndex(self.eval_model.index(selected,0))
        self.display_match_comparison()
        best=max((r['hits'] for r in outcome['rows']),default=0)
        self.eval_summary.setText(f'{outcome["known"]} de 14 resultados disponibles · mejor apuesta: {best} aciertos · {outcome["counts"][15]} Plenos confirmados. Marcadores en juego pueden cambiar; sin premios calculados.' if outcome['prize_cents'] is None else f'{outcome["known"]} de 14 resultados disponibles · premio publicado: {money(outcome["prize_cents"])}')

    def evaluate(self,prizes=None):
        if not self.system or not self.system.bets:raise ValueError('Abre una quiniela con apuestas preparadas.')
        result=self.result_input.text().upper();pleno=self.result_pleno.text().upper()
        outcome=engine.evaluate(self.system.bets,result,pleno,finalized=(self.final_check.isChecked(),)*14,
                                prizes=prizes,official=prizes is not None)
        self.render_scrutiny(outcome,pleno,self.final_check.isChecked())

    def read_scrutiny(self):
        path,_=QFileDialog.getOpenFileName(self,'Seleccionar PRE de esta temporada',filter='WIN1X2 (PRE*.txt Pre*.txt)')
        if not path:return
        if Path(path).stem[3:]!=self.round.season:raise ValueError('La temporada del fichero no coincide con la seleccionada.')
        line=next((s for s in text(path).splitlines() if s[:2].strip().isdigit() and int(s[:2])==self.round.number),'')
        scrutiny=scrutiny_record(line)
        if not scrutiny:raise ValueError('No hay escrutinio definitivo para esta jornada.')
        self.manual_mode.setChecked(True)
        self.set_manual_results(scrutiny['result'],scrutiny['pleno']);self.final_check.setChecked(True)
        self.manual_eval_timer.stop();self.evaluate(scrutiny['prizes'])

    def build_systems(self):
        layout=self.page_layout(5)
        note=QLabel('Tus quinielas se guardan automáticamente aquí. Selecciona una fila para abrirla o guardar sus apuestas en un archivo.');note.setWordWrap(True);layout.addWidget(note)
        self.system_view,self.system_model=self.table(('Nombre','Jornada','Guardado','Apuestas','Cómo se creó'),layout)
        row=QHBoxLayout()
        self.button('Abrir',self.open_selected,row);self.button('Duplicar',self.duplicate,row)
        self.button('Abrir apuestas (TXT)',self.import_txt,row);self.button('Abrir quiniela (JSON)',self.import_json,row)
        layout.addLayout(row)
        self.button('Abrir boletos agrupados (CSV/TXT propio)',self.import_ticket_file,layout)
        row=QHBoxLayout()
        self.selected_txt_button=self.button('Guardar apuestas de la fila (TXT)',self.export_selected_txt,row)
        self.selected_json_button=self.button('Guardar copia de la fila (JSON)',self.export_selected_json,row)
        layout.addLayout(row)
        self.import_quantity=QCheckBox('Si una apuesta aparece varias veces en el archivo, contar todas las copias');self.import_quantity.setChecked(True);layout.addWidget(self.import_quantity)
        self.system_view.doubleClicked.connect(lambda _:self.safe(self.open_selected))
        self.system_view.selectionModel().currentChanged.connect(lambda *_:self.update_export_controls())

    def export_busy(self):
        """Avoid saving an older selection while a new calculation is pending."""
        return bool(self.filter_timer.isActive() or self.filter_pending or
                    any(job and job.isRunning() for job in (self.worker,self.data_worker,self.filter_job)))

    def update_export_controls(self):
        busy=self.export_busy() or self.template_timer.isActive()
        ready=bool(self.system and self.system.bets and not busy)
        self.export_button.setEnabled(ready)
        self.export_button.setToolTip('Guarda las apuestas exactas de la quiniela abierta, con sus Plenos.' if ready else 'Espera a que termine el cálculo.' if busy else 'Abre una quiniela con apuestas o pulsa Generar debajo del boleto.')
        index=self.system_view.currentIndex()
        selected=self.listed_systems[index.row()] if index.isValid() and index.row()<len(getattr(self,'listed_systems',())) else None
        self.selected_txt_button.setEnabled(bool(selected and selected.bets and not busy))
        self.selected_json_button.setEnabled(bool(selected and not busy))

    def update_system_list(self):
        self.listed_systems=self.repository.systems(self.round.key)
        names={'manual':'Editada a mano','desarrollo cartesiano exacto':'Todas las combinaciones','selección del desarrollo de origen':'Elegida por presupuesto','filtros básicos de Quiniela Local':'Condiciones aplicadas','actualización explícita de fuentes; apuestas y precio conservados':'Datos actualizados'}
        self.system_model.update_rows([(s.name,s.round_key,s.revision,s.quantity,names.get(s.origin,s.origin)) for s in self.listed_systems])

    def selected_system(self):
        index=self.system_view.currentIndex()
        if not index.isValid():raise ValueError('Selecciona un sistema de la tabla.')
        return self.listed_systems[index.row()]

    def open_selected(self):self.set_system(self.selected_system())
    def duplicate(self):self.set_system(self.service.duplicate(self.selected_system()))

    def import_txt(self):
        path,_=QFileDialog.getOpenFileName(self,f'Importar TXT para {self.round.key}',filter='Apuestas (*.txt)')
        if not path:return
        bets=files.read_txt(path,self.import_quantity.isChecked())
        self.set_system(self.service.imported(self.round,Path(path).stem,bets))

    def import_ticket_file(self):
        from quiniela_ai_studio.domain.tickets import ChannelRules
        from quiniela_ai_studio.infrastructure.ticket_files import read_ticket_file
        path,_=QFileDialog.getOpenFileName(self,'Boletos agrupados de Studio; no formato oficial TuLotero',filter='Archivos propios (*.csv *.txt)')
        if not path:return
        saved=self.repository.setting('tulotero_channel_rules',dict(minimum=2,maximum=8))
        bets=read_ticket_file(path,'csv' if Path(path).suffix.lower()=='.csv' else 'txt',ChannelRules(**saved))
        if QMessageBox.question(self,'Revisar jornada y precio',f'Asignar {len(bets)} apuestas a {self.round.key}, precio actual {money(self.round.price_cents)}?\nEl archivo conserva signos/Plenos pero no certifica jornada, precio vigente ni validación. Verifica correspondencia antes de importar.')!=QMessageBox.StandardButton.Yes:return
        self.set_system(self.service.imported(self.round,Path(path).stem,bets))

    def import_json(self):
        path,_=QFileDialog.getOpenFileName(self,'Importar sistema versionado',filter='Sistema (*.json)')
        if not path:return
        round_,system=files.read_system(path)
        # No reemplazar instantáneas de una jornada existente silenciosamente.
        existing=next((r for r in self.repository.rounds() if r.key==round_.key),None)
        if existing and existing!=round_ and round_.mode!='simulation':raise ValueError('Esta jornada ya tiene otros datos. Importa las apuestas por TXT para revisarlas sin sobrescribir fuentes.')
        if not existing:self.repository.save_round(round_)
        imported=self.service.imported(round_,system.name,system.bets)
        # Conserva base y bloqueos también en sistemas sin generar.
        imported=self.service.version(imported,allow_review=True,base=system.base,locks=system.locks,
                                      pleno=system.pleno,origin='JSON importado',parameters=system.parameters,round_snapshot=system.round_snapshot or json.dumps(__import__('dataclasses').asdict(round_)))
        self.load_rounds(round_.key);self.set_system(imported)

    def export_selected_txt(self):self.export_txt(self.selected_system())

    def export_selected_json(self):self.export_json(self.selected_system())

    def export_filename(self,system,suffix):
        """Suggest a portable name that distinguishes round and saved revision."""
        import re
        name=re.sub(r'[<>:"/\\|?*\x00-\x1f]', '-', f'{system.name}-{system.round_key}-v{system.revision}').strip(' .') or 'quiniela'
        directory=self.repository.setting('export_directory')
        return str(Path(directory)/f'{name}.{suffix}') if directory else f'{name}.{suffix}'

    def show_export_result(self,path,system,round_,quantity):
        from quiniela_ai_studio.ui.export_dialog import build_export_dialog
        build_export_dialog(self,Path(path),system,round_,quantity).exec()

    def export_txt(self,system=None):
        system=system or self.system
        if not system:raise ValueError('Abre primero una quiniela en Mis Sistemas.')
        if self.export_busy():raise ValueError('Espera a que termine el cálculo antes de guardar las apuestas.')
        if not system.bets:raise ValueError('Esta quiniela no tiene apuestas preparadas. Ábrela y pulsa Generar, o cambia las condiciones si has eliminado todas las apuestas.')
        round_=self.repository.round(system.round_key)
        if system.round_snapshot:round_=replace(round_,price_cents=round_from_dict(json.loads(system.round_snapshot)).price_cents)
        path,_=QFileDialog.getSaveFileName(self,f'Guardar apuestas de {system.name}',self.export_filename(system,'txt'),'Apuestas (*.txt)')
        if not path:return
        if not Path(path).suffix:path+='.txt'
        files.write_txt(path,system.bets)
        self.repository.set_setting('export_directory',str(Path(path).resolve().parent))
        self.repository.record_event('export_txt',dict(system_id=system.system_id,revision=system.revision,quantity=system.quantity,file=str(Path(path).resolve())))
        self.statusBar().showMessage(f'{system.quantity:,} apuestas guardadas en {path}',15000)
        self.show_export_result(path,system,round_,system.quantity)

    def export_json(self,system=None):
        system=system or self.system
        if not system:raise ValueError('Abre primero una quiniela en Mis Sistemas.')
        if self.export_busy():raise ValueError('Espera a que termine el cálculo antes de guardar la quiniela.')
        path,_=QFileDialog.getSaveFileName(self,f'Guardar copia de {system.name}',self.export_filename(system,'json'),'Sistema (*.json)')
        if path:
            if not Path(path).suffix:path+='.json'
            files.write_system(path,system,self.repository.round(system.round_key))
            self.repository.set_setting('export_directory',str(Path(path).resolve().parent))
            self.statusBar().showMessage(f'Copia de {system.name} guardada en {path}',15000)

    def build_settings(self):
        outer=self.page_layout(6)
        scroll=QScrollArea();scroll.setWidgetResizable(True)
        content=QWidget();layout=QVBoxLayout(content);scroll.setWidget(content);outer.addWidget(scroll)
        label=QLabel(f'Tus datos se guardan en este equipo:\n{self.repository.path}\n\nPuedes trabajar sin Internet con los datos guardados. La app no envía ni paga apuestas.\nEl precio sirve para calcular el coste; comprueba el precio real antes de jugar.')
        label.setWordWrap(True);layout.addWidget(label)
        self.data_info=QLabel();self.data_info.setWordWrap(True);layout.addWidget(self.data_info)
        self.data_message=QLabel('Descarga los partidos o abre una carpeta con datos que ya tengas.');self.data_message.setWordWrap(True);layout.addWidget(self.data_message)
        self.data_button('Descargar partidos y porcentajes',self.download_data,layout,primary=True)
        self.data_button('Importar carpeta WIN1X2 / Datosg',self.import_win1x2,layout)
        self.data_button('Importar ZIP WIN1X2',self.import_data_zip,layout)
        self.data_button('Abrir elecciones de jugadores (XML)',self.import_public_xml,layout)
        self.data_cancel=self.button('Cancelar descarga / importación',self.cancel_data,layout);self.data_cancel.setEnabled(False)
        self.button('Importar jornada JSON',self.import_round_json,layout)
        rules=QGroupBox('Precio por apuesta · solo para quinielas nuevas');rules_layout=QHBoxLayout(rules)
        self.rule_price=QSpinBox();self.rule_price.setRange(1,100000);self.rule_price.setSuffix(' céntimos');rules_layout.addWidget(self.rule_price)
        self.button('Guardar precio',self.change_rules,rules_layout);layout.addWidget(rules)
        self.data_button('Recuperar quinielas de Quiniela Local',self.import_pc_systems,layout)
        self.button('Crear copia de seguridad',self.backup,layout)
        self.button('Recuperar pronósticos de la app anterior',self.migrate,layout)
        self.button('Ver historial de operaciones',self.show_audit,layout)
        layout.addStretch()

    def import_win1x2(self):
        path=QFileDialog.getExistingDirectory(self,'Seleccionar carpeta Datosg')
        if not path:return
        self.start_data_import(folder=path)

    def data_button(self,label,fn,layout,primary=False):
        button=self.button(label,fn,layout,primary=primary)
        self.data_buttons.append(button)
        return button

    def update_data_buttons(self):
        busy=bool((self.data_worker and self.data_worker.isRunning()) or (self.worker and self.worker.isRunning()))
        for button in self.data_buttons:button.setEnabled(not busy and (button is not self.full_export_button or not self.export_busy()))
        self.data_cancel.setEnabled(bool(self.data_worker and self.data_worker.isRunning()))

    def move_round(self,delta):
        keys=[r.key for r in sorted(self.repository.rounds(),key=lambda r:(r.season,r.number))]
        index=keys.index(self.round.key)+delta
        if 0<=index<len(keys):self.load_rounds(keys[index])

    def go_current(self):
        current=next((r for r in self.repository.rounds() if r.mode=='current'),None)
        if not current:raise ValueError('Importa o descarga datos para identificar la jornada en curso.')
        self.load_rounds(current.key)

    def download_data(self):self.start_data_import(online=True)

    def import_data_zip(self):
        path,_=QFileDialog.getOpenFileName(self,'Importar ZIP de datos WIN1X2',filter='Paquete WIN1X2 (*.zip)')
        if path:self.start_data_import(zip_path=path)

    def start_data_import(self,**options):
        cache=self.repository.path.parent/'data-cache'
        self.start_background('import',None,lambda cancel,status:prepare_data(cache,cancelled=cancel,progress=status,**options))

    def start_background(self,kind,context,operation):
        if (self.data_worker and self.data_worker.isRunning()) or (self.worker and self.worker.isRunning()):
            raise ValueError('Espera o cancela la operación actual.')
        self.data_kind,self.data_context=kind,context
        self.data_worker=DataTask(operation,self)
        self.data_worker.completed.connect(self.background_done)
        self.data_worker.failed.connect(self.background_error)
        self.data_worker.status.connect(self.background_status)
        self.data_worker.finished.connect(self.background_finished)
        self.data_worker.start();self.refresh()

    def background_finished(self):
        if self.close_pending:QTimer.singleShot(0,self.close)
        else:self.refresh()

    def background_status(self,message):
        self.data_message.setText(message);self.statusBar().showMessage(message)

    def background_error(self,message):
        self.background_status(message)
        if not self.close_pending and not (self.data_worker and self.data_worker.cancel_event.is_set()):
            QMessageBox.warning(self,'Datos anteriores conservados',message)

    def cancel_data(self):
        if self.data_worker:
            self.data_worker.cancel_event.set()
            self.background_status('Cancelando… Se espera a que termine la petición en curso (máximo 30 s).')

    def confirm_data(self,prepared):
        dialog=QDialog(self);dialog.setWindowTitle('Revisar importación de datos');dialog.resize(780,580)
        layout=QVBoxLayout(dialog)
        current=next((r for r in prepared.rounds if r.key==prepared.preferred),prepared.rounds[-1])
        label=QLabel(f'{len(prepared.rounds)} jornadas · {current.key}\nSe actualizan datos para nuevos sistemas. Las versiones y apuestas guardadas conservan sus fuentes.');label.setWordWrap(True);layout.addWidget(label)
        picker=QComboBox();picker.addItems([r.key for r in prepared.rounds]);picker.setCurrentText(current.key);layout.addWidget(picker)
        _,model=self.table(('Nº','Local','Visitante','Hora'),layout)
        def show_round(index):
            model.update_rows([(m.number,m.home,m.away,m.kickoff) for m in prepared.rounds[index].matches])
        picker.currentIndexChanged.connect(show_round);show_round(picker.currentIndex())
        warnings=QLabel('\n'.join(prepared.warnings[:8]) or 'Temporadas, jornadas y equipos validados.');warnings.setWordWrap(True);layout.addWidget(warnings)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Importar datos revisados')
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
        return dialog.exec()==QDialog.DialogCode.Accepted

    def background_done(self,result):
        if self.close_pending:
            if hasattr(result,'directory'):shutil.rmtree(result.directory)
            return
        if self.data_kind=='reduction':
            source,plan=self.data_context
            if self.system!=source:
                self.background_status('La quiniela cambió; la reducción no se ha aplicado.');return
            bets=result['bets'];verification=result['verification']
            self.set_system(self.service.reduced_copy(source,plan,bets,verification=verification));self.background_status('Reducida creada y verificada sobre '+str(verification['universe_total'])+' resultados; premio económico no garantizado.');return
        if self.data_kind=='portfolio':
            source=self.data_context
            self.repository.record_event('optimization_run',result.report)
            if self.system!=source or self.round.key!=source.round_key:
                self.background_status('Cálculo registrado para su jornada; la quiniela abierta cambió y no se modifica.');return
            self.optimization_result=result;self.optimization_source=source
            from quiniela_ai_studio.ui.portfolio_dialogs import result_dialog
            self.optimization_dialog=result_dialog(self,result,source);self.optimization_dialog.show()
            self.portfolio_summary.setText(f'Propuesta: {result.report["selected"]} apuestas · {money(result.report["cost_cents"])} · {result.report["optimality"]}. Revisa la ventana antes de aplicar.')
            return
        if self.data_kind=='verification':
            self.repository.record_event('coverage_verification',dict(round_key=self.data_context.round_key,revision=self.data_context.revision,**result))
            dialog=QDialog(self);dialog.setWindowTitle('Cobertura verificada · '+self.data_context.round_key);dialog.resize(700,500);layout=QVBoxLayout(dialog)
            label=QLabel(f'Universo {result["universe_total"]} · {result["universe"]}\nCobertura {result["status"]} · mínimo {result["minimum_hits"] if result["minimum_hits"] is not None else "NO VERIFICADO"}. Garantía condicional, no premio económico.');label.setWordWrap(True);layout.addWidget(label)
            _,model=self.table(('Aciertos','Uniforme','Ponderada'),layout)
            model.update_rows([(k,f'{result["uniform"][k]:.2%}',f'{result["weighted"][k]:.2%}' if result['weighted'] else 'No disponible') for k in ('14','13','12','11','10')]);self.coverage_window=dialog;dialog.show();return
        if self.data_kind=='sources':
            source=self.data_context
            if self.data_worker.cancel_event.is_set():return
            if self.system!=source or self.round.key!=source.round_key:
                self.background_status('La quiniela cambió durante la descarga; no se han aplicado los porcentajes. Vuelve a descargarlos en la jornada que deseas.');return
            try:
                self.repository.save_round(result)
                self.set_system(self.service.refresh_sources(source))
                missing=' Mercado no publicado para esta jornada.' if not result.snapshot('sport') else ''
                self.background_status('Porcentajes descargados y guardados. Tus signos, apuestas y precio no cambian.'+missing+' Pulsa Cambiar el boleto para aplicar la fuente elegida.')
            except (ValueError,OSError,sqlite3.Error) as exc:self.background_error(str(exc))
            return
        if self.data_kind=='export':
            self.repository.record_event('export_development',{**self.data_context, 'file':result['file'],'quantity':result['quantity']})
            self.background_status(f'{result["quantity"]:,} apuestas exportadas a {result["file"]}. El sistema de origen se conserva.')
            if result['format']=='txt':
                self.repository.set_setting('export_directory',str(Path(result['file']).resolve().parent))
                self.show_export_result(result['file'],result['system'],result['round'],result['quantity'])
            return
        if self.close_pending or self.data_worker.cancel_event.is_set():
            if hasattr(result,'directory'):shutil.rmtree(result.directory)
            return
        if self.data_kind=='import':
            try:
                prepared=reconcile_import(result,self.repository.rounds())
                if not self.confirm_data(prepared):
                    self.background_status('Importación descartada; se conservan los datos anteriores.');return
                self.repository.import_rounds(prepared.rounds,prepared.directory)
                preferred=self.round.key if self.round.season!='DEMO' else prepared.preferred
                previous=self.system
                self.load_rounds(preferred)
                if previous and previous.round_key==self.round.key:self.set_system(self.repository.load(previous.system_id))
                self.background_status(f'{len(prepared.rounds)} jornadas importadas. '+ ('\n'.join(prepared.warnings) if prepared.warnings else 'Datos disponibles sin conexión.'))
            except (ValueError,OSError,sqlite3.Error) as exc:
                self.background_error(str(exc))
            finally:
                if self.repository.setting('data_directory')!=str(result.directory):shutil.rmtree(result.directory)
        elif self.data_kind=='live':
            context=self.data_context
            self.repository.set_setting('live:'+context.key,dict(captured_at=utcnow(),matches=[asdict(m) for m in result]))
            if self.round.key==context.key:
                self.safe(lambda:self.display_live(result,utcnow(),cached=False))
            else:self.background_status(f'Marcador guardado para {context.key}; la jornada seleccionada no cambia.')
        elif self.data_kind=='legacy':
            prepared,warnings=result
            if not prepared:
                self.background_error('No hay sistemas recuperables. '+'\n'.join(warnings[:8]));return
            if QMessageBox.question(self,'Copiar sistemas antiguos',f'{len(prepared)} versiones como copias independientes. La base original no cambia.\n'+'\n'.join(warnings[:8]))!=QMessageBox.StandardButton.Yes:return
            try:
                count=self.repository.import_system_copies(prepared)
                self.refresh();self.background_status(f'{count} versiones antiguas recuperadas; sin duplicar copias ya importadas.')
            except (ValueError,sqlite3.Error) as exc:self.background_error(str(exc))

    def import_public_xml(self):
        if self.round.season=='DEMO':raise ValueError('Selecciona una jornada real antes de importar porcentajes.')
        path,_=QFileDialog.getOpenFileName(self,'Porcentajes jugados de esta jornada',filter='Quinielista (*.xml)')
        if not path:return
        updated=public_snapshot(self.round,files.read_bytes(path))
        if QMessageBox.question(self,'Revisar porcentajes',f'Incorporar porcentajes jugados de {updated.key}?\nLas quinielas ya guardadas mantienen los datos que usaron.')!=QMessageBox.StandardButton.Yes:return
        self.repository.save_round(updated);self.refresh()

    def frozen_round(self):
        return round_from_dict(json.loads(self.system.round_snapshot)) if self.system and self.system.round_snapshot else self.round

    def read_cached_scrutiny(self):
        directory=self.repository.setting('data_directory')
        if not directory:raise ValueError('Importa o descarga primero los datos de WIN1X2.')
        scrutiny=scrutiny_from_cache(Path(directory),self.frozen_round())
        if not scrutiny:raise ValueError('Todavía no hay escrutinio definitivo guardado para esta jornada.')
        self.manual_mode.setChecked(True)
        self.set_manual_results(scrutiny['result'],scrutiny['pleno']);self.final_check.setChecked(True)
        self.manual_eval_timer.stop();self.evaluate(scrutiny['prizes'])

    def ensure_live_updates(self,*_):
        if self.close_pending:return
        active=self.auto_live.isChecked() and not self.manual_mode.isChecked() and self.navigation.currentRow()==4 and self.round_picker.currentData() and self.round.season!='DEMO'
        self.repository.set_setting('automatic_live',self.auto_live.isChecked())
        self.repository.set_setting('live_interval_seconds',self.live_interval.currentData())
        self.live_timer.stop()
        if active:
            self.live_timer.setInterval(self.live_interval.currentData()*1000);self.live_timer.start();self.fetch_live_automatically()
        else:
            if self.live_worker:self.live_worker.cancel_event.set()
            if self.manual_mode.isChecked():self.live_status.setText('Resultados introducidos a mano.')
            elif not self.auto_live.isChecked():self.live_status.setText('Actualización automática desactivada.')
            if self.round_picker.currentData() and self.round.season=='DEMO':self.live_status.setText('Demo ficticia: activa Introducir resultados a mano para probar los aciertos.')

    def fetch_live_automatically(self):
        if self.close_pending or not self.auto_live.isChecked() or self.manual_mode.isChecked() or self.navigation.currentRow()!=4:return
        self.fetch_live()

    def fetch_live(self):
        if self.live_worker is not None or self.round.season=='DEMO':return
        context=self.frozen_round();self.live_context=context
        job=DataTask(lambda cancel,status:live_for_round(context),self);self.live_worker=job
        self.live_status.setText('Actualizando marcador…')
        job.completed.connect(lambda matches:self.live_received(context,matches))
        job.failed.connect(lambda message:self.live_error(context,message))
        job.finished.connect(lambda:self.live_finished(job))
        job.start()

    def live_received(self,context,matches):
        if self.close_pending or (self.live_worker and self.live_worker.cancel_event.is_set()):return
        from quiniela_ai_studio.infrastructure.integration import validate_teams
        try:validate_teams(context,[(m.home,m.away) for m in matches])
        except ValueError as exc:
            self.live_error(context,str(exc));return
        captured=utcnow()
        self.repository.set_setting('live:'+context.key,dict(captured_at=captured,matches=[asdict(m) for m in matches]))
        if self.round.key==context.key and not self.manual_mode.isChecked():
            try:self.display_live(matches,captured,cached=False)
            except ValueError as exc:self.live_status.setText(str(exc))

    def live_error(self,context,message):
        if self.live_worker and self.live_worker.cancel_event.is_set():return
        if not self.close_pending and self.round.key==context.key:
            self.live_status.setText(f'No se pudo actualizar: {message}. Se mantiene el último marcador; se volverá a intentar automáticamente.')

    def live_finished(self,job):
        if self.live_worker is job:self.live_worker=None
        job.deleteLater()
        if self.close_pending:self.close();return
        if self.live_context and self.round.key!=self.live_context.key:self.ensure_live_updates()
        elif job.cancel_event.is_set():QTimer.singleShot(0,self.fetch_live_automatically)

    def display_live(self,matches,captured_at,cached):
        from quiniela_ai_studio.infrastructure.integration import validate_teams
        validate_teams(self.frozen_round(),[(m.home,m.away) for m in matches])
        self.live_matches=tuple(matches)
        last=self.live_matches[14]
        self.live_pleno_summary.setText(f'Pleno actual: {last.score} · {last.status} · M = 3 o más goles')
        self.display_match_comparison()
        queried=datetime.fromisoformat(captured_at).astimezone().strftime('%d/%m %H:%M:%S')
        self.live_status.setText(f'{"Marcador guardado" if cached else "Última consulta"}: {queried} · Quinielista / Dataradar')
        self.evaluate_live()

    def display_match_comparison(self,*_):
        if not self.live_matches:return
        index=self.eval_view.currentIndex().row()
        chosen=self.eval_model.rows[index if 0<=index<len(self.eval_model.rows) else 0] if self.eval_model.rows else None
        rows=[]
        for m in self.live_matches:
            actual=(m.pleno or '—') if m.number==15 else m.sign or '—'
            predicted=(chosen[1] if m.number==15 else chosen[0][m.number-1]) if chosen else '—'
            state='Pendiente'
            if chosen and actual!='—':
                state=('Goles coinciden' if predicted==actual else 'Goles fallados') if m.number==15 else ('Acierto' if predicted==actual else 'Fallo')
            rows.append((f'{m.number:02} · {m.home} – {m.away}',m.score,actual,predicted,state,m.status))
        self.live_model.update_rows(rows)

    def restore_live(self):
        cached=self.repository.setting('live:'+self.round.key)
        if not cached:raise ValueError('No hay directo guardado para esta jornada.')
        from quiniela_ai_studio.infrastructure.integration import validate_teams
        matches=tuple(LiveMatch(**m) for m in cached['matches'])
        validate_teams(self.frozen_round(),[(m.home,m.away) for m in matches])
        self.display_live(matches,cached['captured_at'],cached=True)

    def evaluate_live(self):
        if not self.live_matches:raise ValueError('Actualiza o recupera primero el marcador de esta jornada.')
        if not self.system or not self.system.bets:
            self.eval_model.update_rows([]);self.eval_summary.setText('Abre una quiniela con apuestas para compararla con los resultados.');return
        from quiniela_ai_studio.infrastructure.integration import validate_teams
        validate_teams(self.frozen_round(),[(m.home,m.away) for m in self.live_matches])
        result=''.join(m.sign or '-' for m in self.live_matches[:14])
        finalized=tuple(bool(m.final and m.sign) for m in self.live_matches[:14])
        last=self.live_matches[14]
        outcome=engine.evaluate(self.system.bets,result,last.pleno,finalized=finalized,pleno_final=last.final)
        self.render_scrutiny(outcome,last.pleno,last.final)

    def import_pc_systems(self):
        path,_=QFileDialog.getOpenFileName(self,'Base de Quiniela Local (desktop_data/systems.sqlite3)',filter='SQLite (*.sqlite3 *.db)')
        if not path:return
        rounds=self.repository.rounds()
        self.start_background('legacy',None,lambda cancel,status:read_legacy_systems(Path(path),rounds,cancelled=cancel))

    def import_round_json(self):
        path,_=QFileDialog.getOpenFileName(self,'Importar jornada con fuentes normalizadas',filter='Jornada (*.json)')
        if path:
            round_=files.read_round(path);self.repository.save_round(round_);self.load_rounds(round_.key)

    def change_rules(self):
        version=('demo' if self.round.mode=='simulation' else 'regla-local-no-verificada')+'-'+datetime.now().strftime('%Y%m%dT%H%M%S')
        self.repository.change_rules(replace(self.round,price_cents=self.rule_price.value(),rules_version=version))
        self.refresh();self.statusBar().showMessage('Precio guardado para nuevas quinielas. Las anteriores mantienen su precio.',12000)

    def export_development(self):
        if not self.system:raise ValueError('Crea o abre primero un sistema.')
        if self.export_busy():raise ValueError('Espera a que termine el cálculo antes de guardar las apuestas.')
        if not self.system.bets and not self.system.plenos:raise ValueError('Completa el Pleno antes de exportar.')
        path,selected=QFileDialog.getSaveFileName(self,'Guardar todas las combinaciones',self.export_filename(self.system,'txt'),'TXT (*.txt);;JSON (*.json)')
        if not path:return
        system=self.system;round_=self.round
        if system.round_snapshot:round_=replace(round_,price_cents=round_from_dict(json.loads(system.round_snapshot)).price_cents)
        format='json' if Path(path).suffix.lower()=='.json' or selected.startswith('JSON') else 'txt'
        def operation(cancel,status):
            quantity=files.write_development(path,system,round_,format=format,cancelled=cancel,
                                            progress=lambda done,total:status(f'Exportación: {done:,} / {total:,} apuestas'))
            return dict(file=path,quantity=quantity,published=True,format=format,system=system,round=round_)
        self.start_background('export',dict(system_id=system.system_id,revision=system.revision,input_hash=system.hash,format=format),operation)

    def backup(self):
        path,_=QFileDialog.getSaveFileName(self,'Crear archivo nuevo de copia',f'studio-copia-{datetime.now():%Y%m%d-%H%M%S}.sqlite3','SQLite (*.sqlite3)')
        if path:self.repository.backup(path);self.statusBar().showMessage('Copia de seguridad creada.',10000)

    def migrate(self):
        path,_=QFileDialog.getOpenFileName(self,'Seleccionar pronosticos.json; se copiará el original',filter='Pronósticos (*.json)')
        if not path:return
        count,target=migrate_legacy(path,self.repository,self.service)
        self.refresh();QMessageBox.information(self,'Recuperación',f'{count} sistemas recuperados.\nCopia y columnas sin asignar:\n{target}\nLas apuestas sin jornada quedan en la copia para que puedas revisarlas.')

    def build_reductions(self):
        from quiniela_ai_studio.domain.reduction_tables import TABLES
        outer=self.page_layout(7)
        note=QLabel('Base independiente de Normal. Elige tipo y fuente: se proponen fijos, dobles y triples propios. Puedes ajustar las casillas.');note.setWordWrap(True);note.setToolTip('Matrices BOE 2009; no es una apuesta validada ni un envío oficial.');outer.addWidget(note)
        self.reduction_picker=QComboBox()
        for table in TABLES:
            self.reduction_picker.addItem(f'Reducida {table.number}: {table.widths.count(2)} dobles + {table.widths.count(3)} triples → {len(table.patterns)} columnas',table.number)
        self.reduction_picker.currentIndexChanged.connect(self.reduction_type_changed);outer.addWidget(self.reduction_picker)
        row=QHBoxLayout();self.reduction_source=QComboBox();self.reduction_source.addItem('Mercado: casas de apuestas','sport');self.reduction_source.addItem('Popularidad: Quinielista','public');self.reduction_source.currentIndexChanged.connect(self.ranking_source.setCurrentIndex);row.addWidget(self.reduction_source,1)
        self.button('Descargar porcentajes',self.refresh_system_sources,row,editable=True);outer.addLayout(row)
        row=QHBoxLayout();row.addWidget(QLabel('Diferenciación del público'));self.reduction_differentiation=QSlider(Qt.Orientation.Horizontal);self.reduction_differentiation.setRange(0,10);self.reduction_differentiation.valueChanged.connect(self.differentiation.setValue);row.addWidget(self.reduction_differentiation,1);self.reduction_diff_label=QLabel('0');row.addWidget(self.reduction_diff_label);outer.addLayout(row)
        note=QLabel('0: seguir la fuente elegida. Subir requiere Mercado + popularidad: favorece signos relativamente poco jugados. No garantiza más aciertos ni premios; puede perder más. Popularidad de Quinielista, no SELAE.');note.setWordWrap(True);note.setObjectName('muted');outer.addWidget(note)
        row=QHBoxLayout();row.addWidget(QLabel('Cobertura del Pleno (0–10)'));self.reduction_pleno_level=QSlider(Qt.Orientation.Horizontal);self.reduction_pleno_level.setRange(0,10);self.reduction_pleno_level.valueChanged.connect(self.schedule_template);row.addWidget(self.reduction_pleno_level,1);self.reduction_level_label=QLabel('0');row.addWidget(self.reduction_level_label);outer.addLayout(row)
        self.reduction_options_view,self.reduction_options_model=self.table(('Tipo','Base específica','Columnas','Con Pleno / coste'),outer)
        self.reduction_options_view.setMaximumHeight(205)
        self.reduction_options_view.verticalHeader().hide()
        self.reduction_options_view.verticalHeader().setMinimumSectionSize(20)
        self.reduction_options_view.verticalHeader().setDefaultSectionSize(23)
        self.reduction_options_view.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
        self.reduction_options_view.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents)
        self.reduction_options_view.clicked.connect(lambda index:self.reduction_picker.setCurrentIndex(index.row()) if self.round.editable else None)
        positions_toggle=QCheckBox('Ajustar posiciones de la reducción manualmente');outer.addWidget(positions_toggle)
        scroll=QScrollArea();scroll.setWidgetResizable(True);content=QWidget();layout=QVBoxLayout(content);scroll.setWidget(content);outer.addWidget(scroll,1);scroll.hide();positions_toggle.toggled.connect(scroll.setVisible)
        self.reduction_checks=[]
        for i in range(14):
            check=QCheckBox();check.toggled.connect(self.refresh_reduction);layout.addWidget(check);self.reduction_checks.append(check)
        self.reduction_info=QLabel();self.reduction_info.setWordWrap(True);outer.addWidget(self.reduction_info)
        actions=QHBoxLayout();self.reduction_apply=self.button('Generar apuestas reducidas',self.apply_reduction,actions,primary=True)
        self.button('Cancelar cálculo',self.cancel_data,actions);outer.addLayout(actions)
        self.button('Proponer base según porcentajes',self.rebuild_reduced_template,outer)
        self.choose_reduction_positions()

    def reduction_type_changed(self,*_):
        if self.system and self.construction_mode()=='reduced' and self.navigation.currentRow()==7:self.schedule_template()
        else:self.choose_reduction_positions()

    def choose_reduction_positions(self):
        from quiniela_ai_studio.domain.reduction_tables import TABLES
        table=TABLES[self.reduction_picker.currentData()-1]
        selected=set()
        if self.system:
            for width in (2,3):
                selected.update([i for i,mask in enumerate(self.system.base) if len(mask)==width][:table.widths.count(width)])
            params=json.loads(self.system.parameters)
            if params.get('reduction_choice',params.get('reduction'))==table.number and 'positions' in params:selected=set(params['positions'])
        for i,check in enumerate(self.reduction_checks):
            check.blockSignals(True);check.setChecked(i in selected);check.blockSignals(False)
        self.refresh_reduction()

    def refresh_reduction(self):
        if not hasattr(self,'reduction_apply') or not self.round_picker.currentData():return
        from quiniela_ai_studio.domain.reductions import plan_reduction
        enabled=bool(self.system and self.construction_mode()=='reduced')
        self.reduction_picker.setEnabled(enabled and self.round.editable and not self.export_busy())
        self.reduction_source.setEnabled(enabled)
        self.reduction_differentiation.setEnabled(enabled and self.round.editable and not self.export_busy())
        self.reduction_pleno_level.setEnabled(enabled and self.round.editable and not self.export_busy() and self.pleno_mode.currentData()=='auto')
        from quiniela_ai_studio.domain.reduction_tables import TABLES
        rows=[]
        for table in TABLES:
            count=len(table.patterns)*len(self.system.plenos) if self.system else 0
            rows.append((table.number,f'{table.widths.count(2)} dobles / {table.widths.count(3)} triples',len(table.patterns),f'{count} / {money(count*self.frozen_round().price_cents)}' if count else 'Elige el Pleno'))
        self.reduction_options_model.update_rows(rows)
        self.reduction_options_view.selectRow(self.reduction_picker.currentIndex())
        self.generate_button.setText('Generar reducida' if enabled else 'Generar')
        for i,check in enumerate(self.reduction_checks):
            check.setText(f'{i+1:02} · {self.round.matches[i].home} – {self.round.matches[i].away} · {self.system.base[i] if self.system else "sin boleto"}')
            check.setEnabled(bool(enabled and self.system and len(self.system.base[i])>1))
        self.reduction_apply.setEnabled(False)
        if not enabled:
            self.reduction_info.setText('Entra en Reducidas para crear su propia base. La quiniela normal no se modifica.');return
        try:
            plan=plan_reduction(self.system.base,self.system.plenos,self.reduction_picker.currentData(),[i for i,c in enumerate(self.reduction_checks) if c.isChecked()])
            price=self.frozen_round().price_cents
            self.builder_info.setText(f'Base propia: {sum(len(s)==1 for s in self.system.base)} fijos / {sum(len(s)==2 for s in self.system.base)} dobles / {sum(len(s)==3 for s in self.system.base)} triples\nReducida {plan.table.number}: {plan.after:,} apuestas · {money(plan.after*price)} · guardadas: {self.system.quantity:,}')
            columns=plan.after//len(self.system.plenos)
            self.pleno_selection_info.setText(f'{columns:,} columnas reducidas × {len(self.system.plenos)} Plenos = {plan.after:,} apuestas\nCoste de la reducida: {money(plan.after*price)} · {len(self.system.plenos)} parejas de goles')
            self.reduction_info.setText(f'Al generar esta tabla: {plan.before:,} → {plan.after:,} apuestas · coste {money(plan.after*price)}\nCondicional a acertar toda esta base: al menos {plan.table.minimum_hits} en los 14. No garantiza el Pleno ni dinero. Si después quitas apuestas en Optimizar, esta cobertura ya no está verificada.')
            busy=bool((self.data_worker and self.data_worker.isRunning()) or (self.worker and self.worker.isRunning()) or (self.filter_job and self.filter_job.isRunning()))
            self.reduction_apply.setEnabled(enabled and self.round.editable and plan.after<=engine.MAX_GENERATED and not busy)
        except ValueError as exc:self.reduction_info.setText(str(exc))

    def apply_reduction(self):
        if self.construction_mode()!='reduced':raise ValueError('Crea la base independiente en Reducidas.')
        pending=self.template_timer.isActive();self.template_timer.stop()
        if pending:self.apply_pending_template()
        from quiniela_ai_studio.domain.reductions import plan_reduction, reduced_bets
        system=self.system
        plan=plan_reduction(system.base,system.plenos,self.reduction_picker.currentData(),[i for i,c in enumerate(self.reduction_checks) if c.isChecked()])
        from quiniela_ai_studio.domain.coverage import make_universe, verify_coverage
        universe=make_universe(plan.selection.base,self.frozen_round().snapshot('sport'),limit=10000,seed=0)
        def operation(cancel,status):
            bets=reduced_bets(plan,cancel)
            status('Verificando las columnas reales generadas…')
            verification=verify_coverage(bets,universe,cancelled=cancel,progress=lambda done,total:status(f'Verificación: {done}/{total}'))
            return dict(bets=bets,verification=verification)
        self.start_background('reduction',(system,plan),operation)

    def show_audit(self):
        rows=self.repository.audit()
        names={'edit':'Boleto modificado','create':'Quiniela creada','generate':'Apuestas generadas','filter':'Condiciones aplicadas','optimize':'Apuestas elegidas','import':'Archivo abierto','export_txt':'Apuestas guardadas en TXT','export_development':'Archivo guardado','change_rules':'Precio cambiado','restore_origin':'Apuestas recuperadas','undo':'Último cambio deshecho','refresh_sources':'Datos actualizados'}
        dialog=QMessageBox(self);dialog.setWindowTitle('Qué has hecho');dialog.setText('\n'.join(f'{date} · {names.get(action, "Quiniela o datos guardados")} · guardado {revision}' for date,action,revision,detail in rows) or 'Todavía no hay operaciones.')
        dialog.setDetailedText('\n'.join(f'{date} · {action} · {detail}' for date,action,revision,detail in rows));dialog.exec()

    def closeEvent(self,event):
        self.template_timer.stop()
        self.live_timer.stop();self.manual_eval_timer.stop()
        if self.live_worker and self.live_worker.isRunning():
            self.close_pending=True;self.live_worker.cancel_event.set();event.ignore();return
        self.filter_timer.stop();self.filter_epoch+=1
        if self.filter_job and self.filter_job.isRunning():
            self.close_pending=True;self.filter_job.cancel_event.set();event.ignore();return
        if self.data_worker and self.data_worker.isRunning():
            self.close_pending=True
            self.cancel_data()
            self.statusBar().showMessage('Cerrando al terminar la petición cancelada…')
            event.ignore();return
        if self.worker and self.worker.isRunning():
            self.worker.cancel_event.set()
            if not self.worker.wait(3000):
                event.ignore();return
        self.close_pending=True
        self.repository.close();event.accept()
