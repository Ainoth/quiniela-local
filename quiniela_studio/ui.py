"""Escritorio Qt en español: siete secciones y un sistema activo."""
from datetime import datetime
from decimal import Decimal
from functools import partial
from pathlib import Path
import json
import threading

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QListWidget, QStackedWidget, QComboBox,
    QTableView, QHeaderView, QLineEdit, QSpinBox, QDoubleSpinBox, QSlider,
    QCheckBox, QFileDialog, QMessageBox, QScrollArea, QProgressBar, QAbstractItemView)
from . import __version__
from .domain import Bet, utcnow, round_from_dict
from . import engine, files
from .services import SystemService
from .providers import load_win1x2, migrate_legacy, scrutiny_record, text

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


class MainWindow(QMainWindow):
    SECTIONS = ('Inicio', 'Crear Quiniela', 'Optimizar', 'Análisis', 'Escrutinio', 'Mis Sistemas', 'Configuración')

    def __init__(self, repository):
        super().__init__()
        self.repository = repository
        self.service = SystemService(repository)
        self.system = None
        self.worker = None
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
        except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
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
        index = self.round_picker.findData(preferred) if preferred else 0
        self.round_picker.setCurrentIndex(max(0, index)); self.round_picker.blockSignals(False)
        self.select_round()

    @property
    def round(self):
        return self.repository.round(self.round_picker.currentData())

    def select_round(self, *_):
        if not self.round_picker.currentData(): return
        systems = self.repository.systems(self.round.key)
        self.system = systems[-1] if systems else None
        self.result_input.setText('-'*14)
        self.result_pleno.clear()
        self.final_check.setChecked(False)
        self.eval_model.update_rows([])
        self.eval_summary.setText('Selecciona resultados para esta jornada.')
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
        busy = bool(self.worker and self.worker.isRunning())
        for button in self.edit_buttons:
            button.setEnabled(round_.editable and not busy)
        system = self.system
        for i, match in enumerate(view_round.matches[:14]):
            self.match_labels[i].setText(f'{i+1:02}  {match.home} – {match.away}')
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
        self.name_input.blockSignals(True); self.name_input.setText(system.name if system else ''); self.name_input.blockSignals(False)
        self.name_input.setEnabled(bool(system and round_.editable and not busy))
        self.builder_info.setText(f'Base visible: {engine.size(system.base):,} combinaciones · columnas activas: {system.quantity:,}. Editar signos crea un borrador sin apuestas.' if system else 'Crea un sistema para seleccionar signos.')
        self.update_system_list()
        self.analysis_info.setText(self.analysis_text())
        self.optimize_info.setText(f'Origen: {system.name} v{system.revision}\n{system.quantity:,} apuestas · hash {system.hash[:16]}\nLa selección crea una nueva versión. El origen sigue guardado.' if system else 'Abre o genera primero un sistema.')

    def build_home(self):
        layout = self.page_layout(0)
        self.home_info = QLabel(); self.home_info.setWordWrap(True); layout.addWidget(self.home_info)
        row = QHBoxLayout()
        self.button('Crear sistema manual', self.new_system, row, primary=True, editable=True)
        self.button('Probar ejemplo de 6 columnas', self.example_system, row, editable=True)
        self.button('Consultar aciertos', lambda: self.navigation.setCurrentRow(4), row)
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
        row=QHBoxLayout();row.addWidget(QLabel('Pleno al 15 · Local / Visitante'))
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
        self.set_system(self.service.template(self.system,self.coverage.value()))

    def start_generation(self):
        if not self.system:raise ValueError('Crea primero un sistema.')
        if self.worker and self.worker.isRunning():return
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
        layout=self.page_layout(2);self.optimize_info=QLabel();self.optimize_info.setWordWrap(True);layout.addWidget(self.optimize_info)
        row=QHBoxLayout();row.addWidget(QLabel('Presupuesto máximo (€)'))
        self.budget=QDoubleSpinBox();self.budget.setRange(0,100000);self.budget.setDecimals(2);self.budget.setValue(10);row.addWidget(self.budget)
        self.button('Seleccionar apuestas del origen',self.optimize,row,primary=True,editable=True);layout.addLayout(row)
        label=QLabel('Con deportiva: orden por probabilidad bajo independencia. Sin deportiva: orden lexicográfico explícito.\nNo es un reductor con garantía, ni una estimación de rentabilidad. El presupuesto nunca aumenta automáticamente.')
        label.setWordWrap(True);layout.addWidget(label);layout.addStretch()

    def optimize(self):
        if not self.system:raise ValueError('No hay un sistema activo.')
        cents=int(Decimal(self.budget.cleanText().replace(',','.'))*100)
        self.set_system(self.service.optimized(self.system,cents))

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
        self.button('Comprobar',self.evaluate,row,primary=True);self.button('Leer escrutinio PRE',self.read_scrutiny,row);layout.addLayout(row)
        self.eval_summary=QLabel();self.eval_summary.setWordWrap(True);layout.addWidget(self.eval_summary)
        self.eval_view,self.eval_model=self.table(('Columna','Pleno','Cantidad','Ahora','Confirmados','Máximo'),layout)
        note=QLabel('Entrada manual: escenario de comprobación, sin consulta en vivo en v0.1. No introduce empates en partidos pendientes. Los importes solo aparecen al importar escrutinio PRE definitivo.')
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
        layout=self.page_layout(6)
        label=QLabel(f'Almacenamiento SQLite local:\n{self.repository.path}\n\nDatos y cálculos disponibles sin conexión. No se envían apuestas ni credenciales.\nv0.1 utiliza precio configurado por jornada; confirma el precio del canal antes de jugar.')
        label.setWordWrap(True);layout.addWidget(label)
        self.button('Importar carpeta WIN1X2 / Datosg',self.import_win1x2,layout)
        self.button('Importar jornada JSON',self.import_round_json,layout)
        self.button('Crear copia de seguridad SQLite',self.backup,layout)
        self.button('Recuperar pronósticos de la app anterior',self.migrate,layout)
        self.button('Ver historial de operaciones',self.show_audit,layout)
        layout.addStretch()

    def import_win1x2(self):
        path=QFileDialog.getExistingDirectory(self,'Seleccionar carpeta Datosg')
        if not path:return
        rounds=load_win1x2(path)
        for round_ in rounds:self.repository.save_round(round_)
        self.load_rounds(rounds[-1].key)
        self.statusBar().showMessage(f'{len(rounds)} jornadas locales importadas.',15000)

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
        if self.worker and self.worker.isRunning():
            self.worker.cancel_event.set()
            if not self.worker.wait(3000):
                event.ignore();return
        self.repository.close();event.accept()
