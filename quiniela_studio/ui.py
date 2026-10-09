"""Escritorio Qt en español: siete secciones y un sistema activo."""
from datetime import datetime
from dataclasses import asdict
from decimal import Decimal
from functools import partial
from pathlib import Path
import json
import threading
import shutil
import sqlite3

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QThread, Signal, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QListWidget, QStackedWidget, QComboBox,
    QTableView, QHeaderView, QLineEdit, QSpinBox, QDoubleSpinBox, QSlider,
    QCheckBox, QFileDialog, QMessageBox, QScrollArea, QProgressBar, QAbstractItemView,
    QDialog, QDialogButtonBox, QGroupBox)
from . import __version__
from .domain import utcnow, round_from_dict
from . import engine, files
from .services import SystemService
from .providers import migrate_legacy, scrutiny_record, text
from .integration import (prepare_data, reconcile_import, public_snapshot, live_for_round,
                          read_legacy_systems, scrutiny_from_cache)
from live_results import LiveMatch

STYLE = '''
QWidget {font-family: "DejaVu Sans", "Segoe UI"; font-size: 13px; color: #173050; background: #f2f5fa;}
QMainWindow {background: #f2f5fa;}
QLabel#brand {font-size: 24px; font-weight: bold; color: #0c3454;}
QLabel#title {font-size: 22px; font-weight: bold; color: #0c3454;}
QLabel#muted {color: #586b80;}
QListWidget {background: #0c2440; color: #dce8f5; border: none; padding: 8px; font-size: 14px;}
QListWidget::item {padding: 13px 7px; border-radius: 6px;}
QListWidget::item:selected {background: #146a8c; color: white;}
QPushButton {background: white; border: 1px solid #c8d3df; border-radius: 5px; padding: 7px 11px;}
QPushButton:hover {border-color: #1682a4; background: #e6f5fb;}
QPushButton:checked {background: #dc4b62; color: white; border: 2px solid #9c2440; font-weight: bold;}
QPushButton#primary {background: #097860; color: white; border-color: #097860; font-weight: bold;}
QPushButton:disabled {color: #8896a6; background: #e6ebf1; border-color: #d4dce6;}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {background: white; border: 1px solid #c8d3df; padding: 5px; border-radius: 4px;}
QTableView {background: white; alternate-background-color: #eef3f8; gridline-color: #dae3ed; border: 1px solid #c4d2e0;}
QHeaderView::section {background: #e6edf5; padding: 7px; border: none; font-weight: bold;}
QScrollArea {border: none;}
QProgressBar {border: 1px solid #c8d3df; border-radius: 4px; text-align: center;}
QProgressBar::chunk {background: #159881;}
'''


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
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.rows[index.row()][index.column()])

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
            result = engine.generate(self.version.base, self.version.pleno,
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
            if self.cancel_event.is_set():
                if hasattr(result, 'directory'): shutil.rmtree(result.directory)
                raise engine.Cancelled('Operación cancelada; los datos anteriores se conservan.')
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    SECTIONS = ('Inicio', 'Crear Quiniela', 'Optimizar', 'Análisis', 'Escrutinio', 'Mis Sistemas', 'Configuración')

    def __init__(self, repository):
        super().__init__()
        self.repository = repository
        self.service = SystemService(repository)
        self.system = None
        self.worker = None
        self.data_worker = None
        self.data_buttons = []
        self.live_matches = None
        self.close_pending = False
        self.edit_buttons = []
        self.setWindowTitle(f'Quiniela AI Studio · v{__version__}')
        self.resize(1200, 820)
        self.setMinimumSize(760, 540)
        body = QWidget(); self.setCentralWidget(body)
        root = QHBoxLayout(body); root.setContentsMargins(0, 0, 0, 0)
        sidebar = QWidget(); sidebar.setFixedWidth(184)
        side = QVBoxLayout(sidebar)
        logo = QLabel('QUINIELA\nAI STUDIO'); logo.setObjectName('brand'); logo.setStyleSheet('color:#dce8f5; background:#0c2440; font-size:21px; padding:12px;')
        sidebar.setStyleSheet('background:#0c2440;')
        side.addWidget(logo)
        self.navigation = QListWidget(); self.navigation.addItems(self.SECTIONS)
        side.addWidget(self.navigation)
        tag = QLabel(f'v{__version__} · Escritorio local'); tag.setStyleSheet('color:#aec2d9; background:#0c2440; font-size:11px;')
        side.addWidget(tag); root.addWidget(sidebar)
        right = QWidget(); layout = QVBoxLayout(right); layout.setContentsMargins(18, 12, 18, 10)
        bar = QHBoxLayout()
        self.round_picker = QComboBox(); self.round_picker.setMinimumWidth(180)
        bar.addWidget(QLabel('Temporada / jornada')); bar.addWidget(self.round_picker); bar.addStretch()
        self.system_label = QLabel(); bar.addWidget(self.system_label)
        layout.addLayout(bar)
        self.metadata = QLabel(); self.metadata.setObjectName('muted'); self.metadata.setWordWrap(True); layout.addWidget(self.metadata)
        self.pages = QStackedWidget(); layout.addWidget(self.pages, 1)
        for name in self.SECTIONS:
            page = QWidget(); page_layout = QVBoxLayout(page)
            title = QLabel(name); title.setObjectName('title'); page_layout.addWidget(title)
            self.pages.addWidget(page)
        self.footer = QLabel(); self.footer.setWordWrap(True); layout.addWidget(self.footer)
        root.addWidget(right, 1)
        self.build_home(); self.build_builder(); self.build_optimize(); self.build_analysis()
        self.build_evaluation(); self.build_systems(); self.build_settings()
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
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
        systems = self.repository.systems(self.round.key)
        self.system = systems[-1] if systems else None
        self.result_input.setText('-'*14)
        self.result_pleno.clear()
        self.final_check.setChecked(False)
        self.eval_model.update_rows([])
        self.eval_summary.setText('Selecciona resultados para esta jornada.')
        self.live_matches = None
        self.live_model.update_rows([])
        cached = self.repository.setting('live:' + self.round.key)
        self.live_status.setText(f'Última consulta guardada: {cached["captured_at"]} · pulsa «Ver directo guardado».' if cached else 'Sin marcador guardado para esta jornada.')
        self.refresh()

    def refresh(self):
        round_ = self.round
        view_round = round_from_dict(json.loads(self.system.round_snapshot)) if self.system and self.system.round_snapshot else round_
        self.system_label.setText(f'{self.system.name} · v{self.system.revision}' if self.system else 'Sin sistema activo')
        modes = dict(simulation='SIMULACIÓN · datos de ejemplo', current='EN CURSO · editable', past='HISTÓRICA · consulta', future='FUTURA · consulta')
        mode_label = modes[round_.mode] if round_.mode != 'current' or round_.editable else 'CONSULTA · fecha nominal vencida'
        self.metadata.setText(f'{mode_label} · {view_round.source}\nDatos congelados: {datetime.fromisoformat(view_round.captured_at).astimezone():%d/%m/%Y %H:%M} · Regla de precio: {view_round.rules_version}')
        quantity = self.system.quantity if self.system else 0
        pending = sum(b.quantity for b in self.system.bets if not b.pleno) if self.system else 0
        self.footer.setText(f'{quantity:,} apuestas exactas · coste {money(self.system.cost(round_) if self.system else 0)} · {pending} Plenos pendientes · Desarrollo / selección, sin garantía de reducción')
        self.home_info.setText(f'{round_.key}\n15 partidos disponibles · {len(self.repository.systems(round_.key))} sistemas guardados\nPrecio configurado: {money(round_.price_cents)} por apuesta. Exportar no valida ni paga apuestas.')
        self.data_info.setText('Datos guardados: ' + (self.repository.setting('data_directory') or 'ninguna importación todavía') + '\nWIN1X2: jornadas/calendario/premios. Quinielista: porcentajes jugados y marcador; no son probabilidades deportivas.')
        busy = bool((self.worker and self.worker.isRunning()) or (self.data_worker and self.data_worker.isRunning()))
        for button in self.edit_buttons:
            button.setEnabled(round_.editable and not busy)
        system = self.system
        for i, match in enumerate(view_round.matches[:14]):
            kickoff=match.kickoff[:10]+' '+match.kickoff[10:] if len(match.kickoff)==15 else match.kickoff
            self.match_labels[i].setText(f'{i+1:02}  {match.home} – {match.away}\n{kickoff}' if kickoff else f'{i+1:02}  {match.home} – {match.away}')
            snapshot = view_round.snapshot('sport'); public = view_round.snapshot('public')
            fmt = lambda snap: ' / '.join(f'{100*v:.0f}' for v in snap.values[i]) if snap else 'Sin datos'
            self.prob_labels[i].setText(f'{fmt(snapshot)}   |   {fmt(public)}')
            for sign, button in self.sign_buttons[i].items():
                button.blockSignals(True); button.setChecked(bool(system and sign in system.base[i])); button.blockSignals(False)
                button.setEnabled(bool(system and round_.editable and not system.locks[i] and not busy))
            lock = self.lock_buttons[i]; lock.blockSignals(True)
            lock.setChecked(bool(system and system.locks[i])); lock.setText('Bloqueado' if lock.isChecked() else 'Bloquear')
            lock.setEnabled(bool(system and round_.editable and not busy)); lock.blockSignals(False)
        for i, combo in enumerate(self.pleno_combos):
            combo.blockSignals(True); combo.setCurrentText(system.pleno[i] if system and len(system.pleno)==2 else '—')
            combo.setEnabled(bool(system and round_.editable and not busy)); combo.blockSignals(False)
        pleno_match=view_round.matches[14]
        self.pleno_match_label.setText(f'Pleno al 15 · {pleno_match.home} – {pleno_match.away}')
        self.name_input.blockSignals(True); self.name_input.setText(system.name if system else ''); self.name_input.blockSignals(False)
        self.name_input.setEnabled(bool(system and round_.editable and not busy))
        self.builder_info.setText(f'Base visible: {engine.size(system.base):,} combinaciones · columnas activas: {system.quantity:,}. Editar signos crea un borrador sin apuestas.' if system else 'Crea un sistema para seleccionar signos.')
        self.update_system_list()
        self.analysis_info.setText(self.analysis_text())
        self.optimize_info.setText(f'Origen: {system.name} v{system.revision}\n{system.quantity:,} apuestas · hash {system.hash[:16]}\nLa selección crea una nueva versión. El origen sigue guardado.' if system else 'Abre o genera primero un sistema.')
        self.update_data_buttons()

    def build_home(self):
        layout = self.page_layout(0)
        self.home_info = QLabel(); self.home_info.setWordWrap(True); layout.addWidget(self.home_info)
        row = QHBoxLayout()
        self.button('Crear sistema manual', self.new_system, row, primary=True, editable=True)
        self.button('Probar ejemplo de 6 columnas', self.example_system, row, editable=True)
        self.button('Consultar aciertos', lambda: self.navigation.setCurrentRow(4), row)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.data_button('Descargar / actualizar datos', self.download_data, row, primary=True)
        self.data_button('Importar datos locales', self.import_win1x2, row)
        self.button('En curso', self.go_current, row)
        layout.addLayout(row)
        note = QLabel('v0.1 · Constructor, versiones, archivos y cálculo verificable.\nIA entrenada, rentabilidad, simulaciones, garantías y peñas quedan para fases posteriores.\nEl ejemplo inicial es sintético y funciona sin conexión.')
        note.setWordWrap(True); layout.addWidget(note); layout.addStretch()

    def new_system(self):
        if not self.round.editable: raise ValueError('Jornada de consulta.')
        self.system = self.service.new(self.round)
        self.navigation.setCurrentRow(1); self.refresh()

    def example_system(self):
        self.new_system()
        self.system = self.service.edit(self.system, ('1X','1','1X2')+('1',)*11, (False,)*14, 'M1')
        self.refresh(); self.start_generation()

    def build_builder(self):
        layout = self.page_layout(1)
        row = QHBoxLayout(); self.name_input = QLineEdit(); self.name_input.setPlaceholderText('Nombre del sistema')
        self.name_input.editingFinished.connect(lambda: self.safe(self.rename))
        row.addWidget(self.name_input)
        self.button('Nuevo', self.new_system, row, editable=True)
        self.button('Deshacer', self.undo, row, editable=True); layout.addLayout(row)
        self.builder_info = QLabel(); self.builder_info.setWordWrap(True); layout.addWidget(self.builder_info)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        grid_widget = QWidget(); grid = QGridLayout(grid_widget); grid.setSpacing(3)
        for col, title in enumerate(('Partidos', 'Deportiva | Público (%)', '1', 'X', '2', 'Bloqueo')):
            grid.addWidget(QLabel(title), 0, col)
        self.match_labels=[]; self.prob_labels=[]; self.sign_buttons=[]; self.lock_buttons=[]
        for i in range(14):
            label=QLabel(); label.setMinimumWidth(160); label.setWordWrap(True); self.match_labels.append(label); grid.addWidget(label,i+1,0)
            prob=QLabel(); prob.setObjectName('muted'); self.prob_labels.append(prob); grid.addWidget(prob,i+1,1)
            signs={}
            for j, sign in enumerate('1X2'):
                button=QPushButton(sign); button.setCheckable(True); button.setFixedSize(35,24); button.setStyleSheet("padding: 1px;")
                button.setAccessibleName(f'Partido {i+1}, signo {sign}')
                button.clicked.connect(partial(self.toggle_sign,i,sign)); grid.addWidget(button,i+1,j+2); signs[sign]=button
            self.sign_buttons.append(signs)
            lock=QPushButton('Bloquear');lock.setCheckable(True);lock.setFixedHeight(24);lock.setStyleSheet('padding:1px 5px;')
            lock.clicked.connect(partial(self.toggle_lock,i));grid.addWidget(lock,i+1,5);self.lock_buttons.append(lock)
        grid.setColumnStretch(0,1)
        scroll.setWidget(grid_widget);layout.addWidget(scroll,1)
        row=QHBoxLayout();self.pleno_match_label=QLabel();self.pleno_match_label.setWordWrap(True);row.addWidget(self.pleno_match_label)
        self.pleno_combos=[]
        for _ in range(2):
            combo=QComboBox();combo.addItems(['—','0','1','2','M']);combo.currentIndexChanged.connect(self.change_pleno)
            row.addWidget(combo);self.pleno_combos.append(combo)
        row.addStretch();layout.addLayout(row)
        row=QHBoxLayout();row.addWidget(QLabel('Cobertura 0–10'))
        self.coverage=QSlider(Qt.Orientation.Horizontal);self.coverage.setRange(0,10);row.addWidget(self.coverage,1)
        self.coverage_label=QLabel('0');row.addWidget(self.coverage_label);self.coverage.valueChanged.connect(lambda v:self.coverage_label.setText(str(v)))
        self.button('Aplicar plantilla', self.apply_template, row, editable=True);layout.addLayout(row)
        note=QLabel('Nivel 10: 3 triples + 7 dobles + 4 fijos = 3.456. Respeta bloqueos. Sin deportiva usa orden 1/X/2; no usa porcentajes públicos como modelo.')
        note.setWordWrap(True);note.setObjectName('muted');layout.addWidget(note)
        row=QHBoxLayout();row.addWidget(QLabel('Fuente para plantilla / presupuesto'))
        self.ranking_source=QComboBox();self.ranking_source.addItem('Deportiva (o orden 1/X/2 si falta)','sport');self.ranking_source.addItem('Público: popularidad, sin probabilidad deportiva','public');row.addWidget(self.ranking_source,1)
        self.button('Actualizar fuentes del sistema',self.refresh_system_sources,row,editable=True);layout.addLayout(row)
        row=QHBoxLayout();self.generate_button=self.button('Generar columnas exactas',self.start_generation,row,primary=True,editable=True)
        self.cancel_button=self.button('Cancelar',self.cancel_generation,row);self.cancel_button.setEnabled(False)
        self.progress=QProgressBar();self.progress.setValue(0);row.addWidget(self.progress,1);layout.addLayout(row)

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

    def change_pleno(self,*_):
        if not self.system:return
        pleno=''.join(c.currentText() for c in self.pleno_combos)
        if '—' in pleno:pleno=''
        self.safe(lambda:self.set_system(self.service.edit(self.system,self.system.base,self.system.locks,pleno)))

    def set_system(self,system):
        self.system=system;self.refresh()

    def undo(self):
        if self.system:self.set_system(self.service.undo(self.system))

    def apply_template(self):
        if not self.system:raise ValueError('Crea primero un sistema.')
        kind=self.ranking_source.currentData()
        if kind=='public' and not self.frozen_round().snapshot(kind):raise ValueError('Actualiza las fuentes del sistema para incorporar los porcentajes jugados.')
        self.set_system(self.service.template(self.system,self.coverage.value(),kind))

    def refresh_system_sources(self):
        if not self.system:raise ValueError('Crea primero un sistema.')
        self.set_system(self.service.refresh_sources(self.system))

    def start_generation(self):
        if not self.system:raise ValueError('Crea primero un sistema.')
        if self.worker and self.worker.isRunning():return
        if self.data_worker and self.data_worker.isRunning():raise ValueError('Espera a que termine la actualización de datos.')
        if not self.system.pleno:raise ValueError('Selecciona los dos valores del Pleno antes de generar.')
        if engine.size(self.system.base)>engine.MAX_GENERATED:raise ValueError('La base supera el límite de v0.1: 100.000 columnas. Reduce dobles o triples.')
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
        self.statusBar().showMessage(f'{len(bets):,} columnas guardadas en {created.round_key}.',10000)

    def generation_finished(self):
        self.cancel_button.setEnabled(False);self.refresh()

    def cancel_generation(self):
        if self.worker:self.worker.cancel_event.set()

    def build_optimize(self):
        outer=self.page_layout(2)
        scroll=QScrollArea();scroll.setWidgetResizable(True)
        content=QWidget();layout=QVBoxLayout(content);scroll.setWidget(content);outer.addWidget(scroll)
        self.optimize_info=QLabel();self.optimize_info.setWordWrap(True);layout.addWidget(self.optimize_info)
        row=QHBoxLayout();row.addWidget(QLabel('Presupuesto máximo (€)'))
        self.budget=QDoubleSpinBox();self.budget.setRange(0,100000);self.budget.setDecimals(2);self.budget.setValue(10);row.addWidget(self.budget)
        self.button('Seleccionar apuestas del origen',self.optimize,row,primary=True,editable=True);layout.addLayout(row)
        self.button('Restaurar desarrollo de origen',self.restore_origin,layout,editable=True)
        label=QLabel('Con deportiva: orden por probabilidad bajo independencia. Sin deportiva: orden lexicográfico explícito.\nNo es un reductor con garantía, ni una estimación de rentabilidad. El presupuesto nunca aumenta automáticamente.')
        label.setWordWrap(True);layout.addWidget(label)
        self.filter_group=QGroupBox('Filtros de Quiniela Local · activar y revisar límites')
        self.filter_group.setCheckable(True);self.filter_group.setChecked(False)
        grid=QGridLayout(self.filter_group);self.filter_ranges={}
        for i,(key,label_text,lower,upper) in enumerate((('variants','Variantes X+2',0,14),('x_count','Cantidad de X',0,14),('two_count','Cantidad de 2',0,14),('x_distance','Distancia entre X',1,13),('coincidences','Coincidencias con referencia',0,14))):
            grid.addWidget(QLabel(label_text),i,0)
            minimum=QSpinBox();minimum.setRange(lower,upper);minimum.setValue(lower)
            maximum=QSpinBox();maximum.setRange(lower,upper);maximum.setValue(upper)
            self.filter_ranges[key]=(minimum,maximum)
            grid.addWidget(QLabel('Mín.'),i,1);grid.addWidget(minimum,i,2);grid.addWidget(QLabel('Máx.'),i,3);grid.addWidget(maximum,i,4)
        self.filter_max_x=QSpinBox();self.filter_max_x.setRange(1,14);self.filter_max_x.setValue(14)
        self.filter_max_two=QSpinBox();self.filter_max_two.setRange(1,14);self.filter_max_two.setValue(14)
        grid.addWidget(QLabel('Racha máxima X / 2'),5,0);grid.addWidget(self.filter_max_x,5,2);grid.addWidget(self.filter_max_two,5,4)
        self.filter_reference=QLineEdit();self.filter_reference.setMaxLength(14);self.filter_reference.setPlaceholderText('14 signos; vacío = sin referencia')
        grid.addWidget(QLabel('Referencia'),6,0);grid.addWidget(self.filter_reference,6,1,1,4)
        filter_note=QLabel('Límites inclusivos. Si hay menos de dos X, distancia satisfecha. Se conservan apuestas exactas, Plenos y cantidades. No se generan garantías.');filter_note.setWordWrap(True);grid.addWidget(filter_note,7,0,1,5)
        button=QPushButton('Aplicar filtros al desarrollo');button.clicked.connect(lambda:self.safe(self.apply_filters));grid.addWidget(button,8,0,1,5)
        self.edit_buttons.append(button)
        layout.addWidget(self.filter_group);layout.addStretch()

    def apply_filters(self):
        if not self.filter_group.isChecked():raise ValueError('Activa los filtros y revisa sus límites antes de aplicarlos.')
        if not self.system:raise ValueError('Abre primero un sistema.')
        from .filters import BasicFilters
        spec=BasicFilters(**{key:(a.value(),b.value()) for key,(a,b) in self.filter_ranges.items()},
                          max_x_run=self.filter_max_x.value(),max_two_run=self.filter_max_two.value(),
                          reference=self.filter_reference.text().upper())
        before=self.system.quantity
        self.set_system(self.service.filtered(self.system,spec))
        self.statusBar().showMessage(f'Filtros: {before} → {self.system.quantity} apuestas. El desarrollo de origen sigue guardado.',15000)

    def restore_origin(self):
        if not self.system:raise ValueError('Abre primero un sistema.')
        self.set_system(self.service.restore_origin(self.system))

    def optimize(self):
        if not self.system:raise ValueError('No hay un sistema activo.')
        cents=int(Decimal(self.budget.cleanText().replace(',','.'))*100)
        self.set_system(self.service.optimized(self.system,cents,self.ranking_source.currentData()))

    def build_analysis(self):
        layout=self.page_layout(3);self.analysis_info=QLabel();self.analysis_info.setWordWrap(True);layout.addWidget(self.analysis_info);layout.addStretch()

    def analysis_text(self):
        round_=self.round;system=self.system
        if system and system.round_snapshot: round_=round_from_dict(json.loads(system.round_snapshot))
        lines=[]
        for kind,label in (('sport','Probabilidad deportiva'),('public','Porcentaje jugado')):
            snap=round_.snapshot(kind)
            lines.append(f'{label}: {snap.source if snap else "sin datos disponibles"}')
        if system:
            lines.extend((f'Columnas distintas de 14: {len({b.column for b in system.bets}):,}',f'Apuestas con cantidad: {system.quantity:,}',f'Hash: {system.hash}'))
            if round_.snapshot('sport') and system.bets:
                lines.append(f'Masa P14 de columnas únicas: {engine.probability_mass(system.bets,round_.snapshot("sport")):.6%} (independencia; no incluye Pleno).')
        lines.append('Garantías, beneficio esperado y modelos entrenados: pendientes de fases posteriores.')
        return '\n\n'.join(lines)

    def build_evaluation(self):
        layout=self.page_layout(4)
        row=QHBoxLayout();self.result_input=QLineEdit('-'*14);self.result_input.setMaxLength(14);row.addWidget(QLabel('Resultado 1/X/2 · - pendiente'));row.addWidget(self.result_input)
        self.result_pleno=QLineEdit();self.result_pleno.setMaxLength(2);self.result_pleno.setMaximumWidth(70);row.addWidget(QLabel('P15'));row.addWidget(self.result_pleno);layout.addLayout(row)
        row=QHBoxLayout();self.final_check=QCheckBox('Los 14 resultados son definitivos');row.addWidget(self.final_check)
        self.button('Comprobar',self.evaluate,row,primary=True);self.button('Leer escrutinio PRE',self.read_scrutiny,row);self.button('Premios guardados',self.read_cached_scrutiny,row);layout.addLayout(row)
        self.eval_summary=QLabel();self.eval_summary.setWordWrap(True);layout.addWidget(self.eval_summary)
        self.eval_view,self.eval_model=self.table(('Columna','Pleno','Cantidad','Ahora','Confirmados','Máximo'),layout)
        row=QHBoxLayout()
        self.data_button('Actualizar marcador',self.fetch_live,row)
        self.button('Ver directo guardado',self.restore_live,row)
        self.button('Comprobar con el directo',self.evaluate_live,row);layout.addLayout(row)
        self.live_status=QLabel();self.live_status.setWordWrap(True);layout.addWidget(self.live_status)
        self.live_view,self.live_model=self.table(('Nº','Partido','Marcador','Estado'),layout)
        note=QLabel('El directo distingue pendientes, provisionales y finalizados. No calcula premios económicos. «Premios guardados» utiliza el PRE de los datos importados, si contiene escrutinio definitivo.')
        note.setWordWrap(True);layout.addWidget(note)

    def evaluate(self,prizes=None):
        if not self.system or not self.system.bets:raise ValueError('Genera o importa apuestas para comprobarlas.')
        result=self.result_input.text().upper();pleno=self.result_pleno.text().upper()
        outcome=engine.evaluate(self.system.bets,result,pleno,finalized=(self.final_check.isChecked(),)*14,
                                prizes=prizes,official=prizes is not None)
        self.eval_model.update_rows([(r['column'],r['pleno'] or '—',r['quantity'],r['hits'],r['confirmed'],r['maximum']) for r in outcome['rows']])
        prize=f' · premio bruto {money(outcome["prize_cents"])}' if outcome['prize_cents'] is not None else ' · premios no disponibles'
        categories=' · '.join(f'{c}: {n}' for c,n in outcome['counts'].items() if n)
        self.eval_summary.setText(f'{outcome["known"]}/14 resultados conocidos · {"definitivos" if outcome["definitive"] else "provisionales"}{prize}\nCategorías acumulables: {categories or "sin categorías definitivas"}')

    def read_scrutiny(self):
        path,_=QFileDialog.getOpenFileName(self,'Seleccionar PRE de esta temporada',filter='WIN1X2 (PRE*.txt Pre*.txt)')
        if not path:return
        if Path(path).stem[3:]!=self.round.season:raise ValueError('La temporada del fichero no coincide con la seleccionada.')
        line=next((s for s in text(path).splitlines() if s[:2].strip().isdigit() and int(s[:2])==self.round.number),'')
        scrutiny=scrutiny_record(line)
        if not scrutiny:raise ValueError('No hay escrutinio definitivo para esta jornada.')
        self.result_input.setText(scrutiny['result']);self.result_pleno.setText(scrutiny['pleno']);self.final_check.setChecked(True)
        self.evaluate(scrutiny['prizes'])

    def build_systems(self):
        layout=self.page_layout(5);self.system_view,self.system_model=self.table(('Nombre','Jornada','Versión','Apuestas','Origen'),layout)
        row=QHBoxLayout()
        self.button('Abrir',self.open_selected,row);self.button('Duplicar',self.duplicate,row)
        self.button('Importar TXT',self.import_txt,row);self.button('Importar JSON',self.import_json,row)
        self.button('Exportar TXT',self.export_txt,row);self.button('Exportar JSON',self.export_json,row);layout.addLayout(row)
        self.import_quantity=QCheckBox('Conservar repetidos como cantidad al importar TXT');self.import_quantity.setChecked(True);layout.addWidget(self.import_quantity)
        self.system_view.doubleClicked.connect(lambda _:self.safe(self.open_selected))

    def update_system_list(self):
        self.listed_systems=self.repository.systems(self.round.key)
        self.system_model.update_rows([(s.name,s.round_key,s.revision,s.quantity,s.origin) for s in self.listed_systems])

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

    def import_json(self):
        path,_=QFileDialog.getOpenFileName(self,'Importar sistema versionado',filter='Sistema (*.json)')
        if not path:return
        round_,system=files.read_system(path)
        # No reemplazar instantáneas de una jornada existente silenciosamente.
        existing=next((r for r in self.repository.rounds() if r.key==round_.key),None)
        if existing and existing!=round_:raise ValueError('Esta jornada ya tiene otros datos. Importa las apuestas por TXT para revisarlas sin sobrescribir fuentes.')
        if not existing:self.repository.save_round(round_)
        imported=self.service.imported(round_,system.name,system.bets)
        # Conserva base y bloqueos también en sistemas sin generar.
        imported=self.service.version(imported,allow_review=True,base=system.base,locks=system.locks,
                                      pleno=system.pleno,origin='JSON importado',parameters=system.parameters,round_snapshot=system.round_snapshot or json.dumps(__import__('dataclasses').asdict(round_)))
        self.load_rounds(round_.key);self.set_system(imported)

    def export_txt(self):
        if not self.system:raise ValueError('No hay sistema activo.')
        path,_=QFileDialog.getSaveFileName(self,'Exportar apuestas; no valida ni paga',self.system.name+'.txt','Apuestas (*.txt)')
        if path:files.write_txt(path,self.system.bets)

    def export_json(self):
        if not self.system:raise ValueError('No hay sistema activo.')
        path,_=QFileDialog.getSaveFileName(self,'Exportar sistema completo',self.system.name+'.json','Sistema (*.json)')
        if path:files.write_system(path,self.system,self.round)

    def build_settings(self):
        outer=self.page_layout(6)
        scroll=QScrollArea();scroll.setWidgetResizable(True)
        content=QWidget();layout=QVBoxLayout(content);scroll.setWidget(content);outer.addWidget(scroll)
        label=QLabel(f'Almacenamiento SQLite local:\n{self.repository.path}\n\nDatos y cálculos disponibles sin conexión. No se envían apuestas ni credenciales.\nv0.1 utiliza precio configurado por jornada; confirma el precio del canal antes de jugar.')
        label.setWordWrap(True);layout.addWidget(label)
        self.data_info=QLabel();self.data_info.setWordWrap(True);layout.addWidget(self.data_info)
        self.data_message=QLabel('Elige una fuente para incorporar datos reales.');self.data_message.setWordWrap(True);layout.addWidget(self.data_message)
        self.data_button('Descargar partidos y porcentajes',self.download_data,layout,primary=True)
        self.data_button('Importar carpeta WIN1X2 / Datosg',self.import_win1x2,layout)
        self.data_button('Importar ZIP WIN1X2',self.import_data_zip,layout)
        self.data_button('Importar porcentajes públicos XML',self.import_public_xml,layout)
        self.data_cancel=self.button('Cancelar descarga / importación',self.cancel_data,layout);self.data_cancel.setEnabled(False)
        self.button('Importar jornada JSON',self.import_round_json,layout)
        self.data_button('Recuperar sistemas SQLite de Quiniela Local',self.import_pc_systems,layout)
        self.button('Crear copia de seguridad SQLite',self.backup,layout)
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
        for button in self.data_buttons:button.setEnabled(not busy)
        self.data_cancel.setEnabled(bool(self.data_worker and self.data_worker.isRunning()))

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
        if QMessageBox.question(self,'Revisar porcentajes',f'Incorporar porcentajes jugados de {updated.key}?\nLas fuentes congeladas de sistemas existentes no cambian.')!=QMessageBox.StandardButton.Yes:return
        self.repository.save_round(updated);self.refresh()

    def frozen_round(self):
        return round_from_dict(json.loads(self.system.round_snapshot)) if self.system and self.system.round_snapshot else self.round

    def read_cached_scrutiny(self):
        directory=self.repository.setting('data_directory')
        if not directory:raise ValueError('Importa o descarga primero los datos de WIN1X2.')
        scrutiny=scrutiny_from_cache(Path(directory),self.frozen_round())
        if not scrutiny:raise ValueError('Todavía no hay escrutinio definitivo guardado para esta jornada.')
        self.result_input.setText(scrutiny['result']);self.result_pleno.setText(scrutiny['pleno']);self.final_check.setChecked(True)
        self.evaluate(scrutiny['prizes'])

    def fetch_live(self):
        context=self.frozen_round()
        self.start_background('live',context,lambda cancel,status:live_for_round(context))

    def display_live(self,matches,captured_at,cached):
        from .integration import validate_teams
        validate_teams(self.frozen_round(),[(m.home,m.away) for m in matches])
        self.live_matches=tuple(matches)
        self.live_model.update_rows([(m.number,f'{m.home} – {m.away}',m.score,m.status) for m in matches])
        self.live_status.setText(f'Quinielista / Dataradar · {"consulta guardada" if cached else "última consulta"}: {captured_at}\nMarcador provisional; sin importes económicos.')

    def restore_live(self):
        cached=self.repository.setting('live:'+self.round.key)
        if not cached:raise ValueError('No hay directo guardado para esta jornada.')
        from .integration import validate_teams
        matches=tuple(LiveMatch(**m) for m in cached['matches'])
        validate_teams(self.frozen_round(),[(m.home,m.away) for m in matches])
        self.display_live(matches,cached['captured_at'],cached=True)

    def evaluate_live(self):
        if not self.live_matches:raise ValueError('Actualiza o recupera primero el marcador de esta jornada.')
        if not self.system or not self.system.bets:raise ValueError('Abre un sistema con apuestas para comprobarlo.')
        from .integration import validate_teams
        validate_teams(self.frozen_round(),[(m.home,m.away) for m in self.live_matches])
        result=''.join(m.sign or '-' for m in self.live_matches[:14])
        finalized=tuple(bool(m.final and m.sign) for m in self.live_matches[:14])
        pleno=self.live_matches[14].pleno if self.live_matches[14].final else ''
        outcome=engine.evaluate(self.system.bets,result,pleno,finalized=finalized)
        self.eval_model.update_rows([(r['column'],r['pleno'] or '—',r['quantity'],r['hits'],r['confirmed'],r['maximum']) for r in outcome['rows']])
        self.eval_summary.setText(f'Directo: {outcome["known"]}/14 conocidos. Confirmados y máximo posible por apuesta; sin premios económicos.\nPleno: {self.live_matches[14].pleno or "pendiente"} · {"final" if self.live_matches[14].final else "provisional"}.')

    def import_pc_systems(self):
        path,_=QFileDialog.getOpenFileName(self,'Base de Quiniela Local (desktop_data/systems.sqlite3)',filter='SQLite (*.sqlite3 *.db)')
        if not path:return
        rounds=self.repository.rounds()
        self.start_background('legacy',None,lambda cancel,status:read_legacy_systems(Path(path),rounds,cancelled=cancel))

    def import_round_json(self):
        path,_=QFileDialog.getOpenFileName(self,'Importar jornada con fuentes normalizadas',filter='Jornada (*.json)')
        if path:
            round_=files.read_round(path);self.repository.save_round(round_);self.load_rounds(round_.key)

    def backup(self):
        path,_=QFileDialog.getSaveFileName(self,'Crear archivo nuevo de copia',f'studio-copia-{datetime.now():%Y%m%d-%H%M%S}.sqlite3','SQLite (*.sqlite3)')
        if path:self.repository.backup(path);self.statusBar().showMessage('Copia de seguridad creada.',10000)

    def migrate(self):
        path,_=QFileDialog.getOpenFileName(self,'Seleccionar pronosticos.json; se copiará el original',filter='Pronósticos (*.json)')
        if not path:return
        count,target=migrate_legacy(path,self.repository,self.service)
        self.refresh();QMessageBox.information(self,'Recuperación',f'{count} sistemas recuperados.\nCopia y columnas sin asignar:\n{target}\nLas columnas globales no se atribuyen automáticamente a una jornada.')

    def show_audit(self):
        rows=self.repository.audit()
        QMessageBox.information(self,'Últimas operaciones','\n'.join(f'{date} · {action} · v{revision} · {detail}' for date,action,revision,detail in rows) or 'Sin operaciones.')

    def closeEvent(self,event):
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
