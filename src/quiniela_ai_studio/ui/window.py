"""Escritorio Qt en español con navegación modular y un sistema activo."""
import json
import re
import shutil
import sqlite3
import threading
import time
import uuid
from dataclasses import asdict, replace
from datetime import datetime
from decimal import Decimal
from functools import partial
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QIntValidator, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
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
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabBar,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
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
from quiniela_ai_studio.infrastructure.published_scrutiny import fetch_published_scrutiny
from quiniela_ai_studio.infrastructure.providers import (
    migrate_legacy,
)
from quiniela_ai_studio.ui.classic_reductions import (
    ClassicContextHeader,
    ClassicReductionsCanvas,
    ClassicTotalList,
    emboss_symbol,
)
from quiniela_ai_studio.ui.normal_generator import NormalGenerator


def coverage_footer(verification):
    """Describe either saved coverage-report schema without claiming a prize.

    Coverage reductions store the verifier under ``coverage``; ordinary
    reductions and optimization copies store the verifier at the top level.
    Incomplete historical reports are treated as unverified.
    """
    if not isinstance(verification,dict):
        return ' · cobertura aún no verificada'
    measured=verification.get('coverage',verification)
    if not isinstance(measured,dict) or measured.get('status') not in ('exacta','estimada por muestreo'):
        return ' · cobertura aún no verificada'
    minimum=measured.get('minimum_hits')
    return (f' · cobertura {measured["status"]}, mínimo '
            f'{minimum if type(minimum) is int else "NO VERIFICADO"} dentro del universo')


STYLE = """
QWidget {font-family: "DejaVu Sans", "Segoe UI"; font-size: 12px; color: #eaf4ff; background: #071a33;}
QLabel#brand {font-size:24px; font-weight:bold; color:#49dbff; background:#0b315c;}
QLabel#title {font-size:20px; font-weight:bold; color:#ffc83d;}
QLabel#muted {color:#8fb5d8;}
QWidget#plenoPanel {background:#f6f7fb; border:1px solid #9bb9d4; border-radius:2px;}
QLabel#plenoTeam {background:transparent; color:#082b70; font-weight:bold;}
QLabel#plenoBadge {background:#e87583; color:white; font-weight:bold; font-size:14px;}
QLabel#plenoPercentage {background:#d8eafb; color:#28577d; font-size:10px; padding:1px;}
QWidget#plenoPanel QPushButton {background:#fffafa; color:#b33448; border:1px solid #ffaaaa; border-radius:0; padding:1px;}
QWidget#plenoPanel QPushButton:checked {background:#d82848; color:white; border-color:#b12038; font-weight:bold;}
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
QTabWidget#reductionTabs::pane {border:1px solid #2787bb; background:#0b2544; top:-1px;}
QTabWidget#reductionTabs QTabBar::tab {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #28658d,stop:1 #123b65); border:1px solid #48bce8; padding:5px 3px 5px 7px; margin-right:1px; font-size:10px;}
QTabWidget#reductionTabs QTabBar::tab:selected {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #44d7ff,stop:1 #087fbe); color:#062442;}
QWidget#groupMatrixFrame {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #174b7b,stop:0.55 #0d3159,stop:1 #164676); border:2px solid #45bce8; border-radius:4px;}
QGroupBox#reductionGroupCard {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #103b67,stop:1 #09213d); border:1px solid #48bce8; border-radius:3px; margin-top:0; padding:5px;}
QLabel#reductionGroupTitle {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #3aa9d5,stop:1 #14517d); color:white; font-weight:bold; padding:4px; border:1px solid #66d9ff;}
QLabel#reductionGroupIndex {color:#75dfff; font-weight:bold;}
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
QFrame#prizeCard {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #123d40,stop:0.55 #10354e,stop:1 #163554); border:2px solid #e4bd43; border-radius:7px;}
QFrame#prizeCard QLabel {background:transparent;}
QFrame#prizeBreakdownCard {background:#0d2946; border:1px solid #62a9c5; border-radius:5px;}
QFrame#prizeBreakdownCard QLabel {background:transparent; border:none;}
QLabel#prizeTableGroup {color:#75e5ec; font-weight:bold; font-size:10px;}
QLabel#prizeTableHeader {color:#a9d8e5; font-size:10px;}
QLabel#prizeTableValue {color:#e7f5fa; font-size:10px;}
QLabel#prizeTableOwn {color:#ffe17a; font-size:10px; font-weight:bold;}
QLabel#prizeTableTotal {color:#ffe17a; font-size:13px; font-weight:bold;}
QLabel#prizeHeadline {font-size:18px; font-weight:bold; color:#ffe17a;}
QLabel#prizeTotal {font-size:32px; font-weight:bold; color:#ffe17a;}
QLabel#prizeFinePrint {font-size:10px; color:#b9dfdf;}
QLabel#prizeCategoryHeading {font-size:10px; color:#8fe6e1; font-weight:bold;}
QLabel#prizeCategoryValue {font-size:11px; color:#fff2b8;}
QWidget#ballot QLabel {color:#082b70; background:#f6f7fb;}
QWidget#ballot {background:#f6f7fb; border-radius:5px;}
QWidget#ballot QLabel[ballotShade="even"] {background:#cde9fc;}
QWidget#ballot QLabel[ballotShade="odd"] {background:#eef6fd;}
QWidget#ballot QLabel[ballotHeader="data"] {background:#e7edf4; border:1px solid #afc2d4; font-size:10px; font-weight:bold;}
QWidget#ballot QLabel[ballotHeader="sign"] {background:#fff0f0; color:#b33448; border:1px solid #ffaaaa; font-weight:bold;}
QWidget#ballot QPushButton {background:#fffafa; color:#b33448; border:1px solid #ffaaaa; border-radius:0;}
QWidget#ballot QPushButton:checked {background:#d82848; color:white; border-color:#b12038;}
QWidget#ballot QPushButton:disabled {color:#a0a9b3; background:#edf0f4;}
"""



def money(cents):
    return f'{cents // 100},{cents % 100:02} €'


def prize_money(cents: int) -> str:
    """Format a published monetary amount in Spanish, without floating point."""
    euros,centimos=divmod(cents,100)
    return f'{euros:,}'.replace(',','.')+f',{centimos:02} €'


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


class SignMatrixWidget(QWidget):
    """Compact 1/X/2 selector matching the manual's ballot-like controls."""

    changed = Signal()

    def __init__(self, rows=14, *, parent=None):
        super().__init__(parent)
        self.rows=rows;self._loading=False;self.buttons=[]
        grid=QGridLayout(self);grid.setContentsMargins(2,2,2,2);grid.setHorizontalSpacing(2);grid.setVerticalSpacing(1)
        grid.addWidget(QLabel('#'),0,0)
        for column,sign in enumerate('1X2',1):
            label=QLabel(sign);label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setStyleSheet('font-weight:bold;color:#ffc83d;')
            grid.addWidget(label,0,column)
        for row in range(rows):
            label=QLabel(f'{row+1:02}');label.setAlignment(Qt.AlignmentFlag.AlignCenter);grid.addWidget(label,row+1,0)
            group=QButtonGroup(self);group.setExclusive(True);row_buttons=[]
            for column,sign in enumerate('1X2',1):
                button=QPushButton(sign);button.setCheckable(True);button.setFixedSize(28,21)
                button.setStyleSheet('QPushButton{padding:0;border-radius:2px;background:#f3f6fb;color:#16406a;border:1px solid #9bb9d4;} QPushButton:checked{background:#d82848;color:white;border:1px solid #ff6678;font-weight:bold;}')
                button.toggled.connect(self._button_changed);group.addButton(button,column-1);grid.addWidget(button,row+1,column);row_buttons.append(button)
            self.buttons.append(row_buttons)
        self.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Fixed)

    def _button_changed(self,checked):
        if checked and not self._loading:self.changed.emit()

    def column(self):
        signs=[]
        for row in self.buttons:
            selected=next((sign for sign,button in zip('1X2',row,strict=True) if button.isChecked()),'')
            if not selected:return ''
            signs.append(selected)
        return ''.join(signs)

    def set_column(self,value):
        if value and (len(value)!=self.rows or any(sign not in '1X2' for sign in value)):
            raise ValueError(f'La referencia debe tener {self.rows} signos 1/X/2.')
        self._loading=True
        try:
            for index,row in enumerate(self.buttons):
                for sign,button in zip('1X2',row,strict=True):button.setChecked(bool(value) and value[index]==sign)
        finally:self._loading=False


class SelectionSquare(QPushButton):
    """Accessible white/green binary control without a checkmark glyph."""

    def __init__(self, name, *, size=18, parent=None):
        super().__init__(parent)
        self.setObjectName('selectionSquare')
        self.setCheckable(True)
        self.setFixedSize(size, size)
        self.setText('')
        self.setAccessibleName(name)
        self.setAccessibleDescription('Verde: seleccionado. Blanco: desactivado.')
        self.setToolTip(name)
        self.setStyleSheet(
            'QPushButton#selectionSquare{padding:0;background:#f3f6fb;color:transparent;'
            'border:1px solid #8eb1cd;border-radius:0;} '
            'QPushButton#selectionSquare:checked{background:#62c515;border:1px solid #b6f45d;} '
            'QPushButton#selectionSquare:focus{border:2px solid #ffc83d;} '
            'QPushButton#selectionSquare:disabled{background:#8b98a6;border-color:#59718d;}'
        )


class SelectionValueSquare(SelectionSquare):
    """Tiny white/green historical-frequency cell with its count inside."""

    def __init__(self, name, *, parent=None):
        super().__init__(name, size=24, parent=parent)
        self.setFixedSize(24, 14)
        self.setStyleSheet(
            'QPushButton#selectionSquare{padding:0;background:#f3f6fb;color:#10243b;'
            'border:1px solid #8eb1cd;border-radius:1px;font-size:7px;} '
            'QPushButton#selectionSquare:checked{background:#62c515;color:#062442;'
            'border:1px solid #b6f45d;font-weight:bold;} '
            'QPushButton#selectionSquare:focus{border:2px solid #ffc83d;} '
            'QPushButton#selectionSquare:disabled{background:#d7e0e9;border-color:#879aaa;}'
        )


class InterruptionMatrix(QWidget):
    """Green/white transition-count matrix for total and longest change run."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        grid=QGridLayout(self);grid.setContentsMargins(2,2,2,2);grid.setHorizontalSpacing(1);grid.setVerticalSpacing(1)
        grid.addWidget(QLabel('Interr.'),0,0)
        caption=QLabel('Seguidas · racha máxima de cambios consecutivos')
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter);caption.setStyleSheet('color:#35d9f4;font-weight:bold;font-size:9px;')
        grid.addWidget(caption,0,1,1,14)
        grid.addWidget(QLabel('#'),1,0)
        for length in range(14):
            label=QLabel(str(length));label.setFixedWidth(14);label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet('font-size:8px;color:#ffc83d;');grid.addWidget(label,1,length+1)
        self.buttons={};self._selected=set();self._reachable=set()
        for total in range(14):
            label=QLabel(str(total));label.setFixedWidth(18);label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet('font-size:8px;color:#ffc83d;');grid.addWidget(label,total+2,0)
            for longest in range(14):
                button=SelectionSquare(f'{total} interrupciones; racha máxima {longest}',size=14)
                button.setProperty('interruptionPair',(total,longest))
                button.toggled.connect(lambda checked,pair=(total,longest):self._toggled(pair,checked))
                self.buttons[(total,longest)]=button;grid.addWidget(button,total+2,longest+1)
        self.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Fixed)
        self.set_reachable({(total,longest) for total in range(14) for longest in range(total+1)})

    def _toggled(self,pair,checked):
        if checked:self._selected.add(pair)
        else:self._selected.discard(pair)
        self.changed.emit()

    def selected_pairs(self):
        return set(self._selected)

    def set_selected_pairs(self,pairs):
        self._selected={tuple(pair) for pair in pairs}
        for pair,button in self.buttons.items():
            button.blockSignals(True);button.setChecked(pair in self._selected);button.blockSignals(False)

    def set_reachable(self,pairs):
        self._reachable=set(pairs)
        for pair,button in self.buttons.items():
            reachable=pair in self._reachable
            selected=pair in self._selected
            button.setEnabled(reachable or selected)
            button.setToolTip(f'{pair[0]} cambios; mayor racha {pair[1]}.'+
                (' Alcanzable desde la base actual.' if reachable else ' No alcanzable desde la base actual; se conserva si estaba elegido.'))


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
    SECTIONS = ('Inicio', 'Normal', 'Optimizar', 'Análisis', 'Escrutinio', 'Mis Sistemas', 'Configuración', 'Reducidas', 'Reducciones')
    # Inicio llevaba a un panel redundante. Normal queda como primera entrada;
    # la página interna Inicio se conserva para no alterar índices persistidos.
    TAB_ORDER = ('Normal', 'Reducciones', 'Optimizar', 'Análisis', 'Escrutinio', 'Mis Sistemas', 'Configuración', 'Reducidas')

    def __init__(self, repository):
        super().__init__()
        self.repository = repository
        self.service = SystemService(repository)
        self._startup_system_id = repository.setting('last_open_system')
        self._startup_prompt_done = False
        self._startup_new_pending = False
        self._initializing = True
        self.system = None
        self.worker = None
        self.data_worker = None
        self.data_kind = None
        self.data_buttons = []
        self.template_timer=QTimer(self);self.template_timer.setSingleShot(True);self.template_timer.setInterval(150);self.template_timer.timeout.connect(self.apply_pending_template)
        self.template_context=None
        self.optimization_result=None;self.optimization_source=None;self.optimization_dialog=None
        self.live_matches = None
        self.published_worker = None
        self.published_attempts = {}
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
        for name in self.TAB_ORDER:self.tabs.addTab(name)
        root.addWidget(self.tabs)
        self.navigation = QListWidget(); self.navigation.addItems(self.SECTIONS); self.navigation.hide()
        self.navigation.currentRowChanged.connect(self.sync_tab_from_page)
        self.tabs.currentChanged.connect(self.sync_page_from_tab)
        bar = QHBoxLayout()
        self.button('‹ Anterior', lambda:self.move_round(-1), bar)
        self.round_picker = QComboBox(); self.round_picker.setMinimumWidth(150)
        bar.addWidget(self.round_picker)
        self.button('Siguiente ›', lambda:self.move_round(1), bar)
        self.button('En curso',self.go_current,bar);bar.addStretch()
        self.system_label = QLabel(); bar.addWidget(self.system_label);root.addLayout(bar)
        self.metadata = QLabel(); self.metadata.setObjectName('muted'); self.metadata.setWordWrap(True); root.addWidget(self.metadata)
        self.splitter=QSplitter(Qt.Orientation.Horizontal)
        self.ballot=QWidget();self.ballot.setFixedWidth(550);QVBoxLayout(self.ballot)
        self.ballot.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.ballot)
        self.pages=QStackedWidget();self.pages.setMinimumWidth(360);self.splitter.addWidget(self.pages)
        self.splitter.setStretchFactor(0,0);self.splitter.setStretchFactor(1,1)
        self.splitter.setSizes([550,700]);root.addWidget(self.splitter,1)
        for name in self.SECTIONS:
            page=QWidget();page_layout=QVBoxLayout(page)
            if name == 'Normal':
                scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                content=QWidget();content_layout=QVBoxLayout(content);content_layout.setContentsMargins(5,4,5,5);content_layout.setSpacing(5)
                title=QLabel(name);title.setObjectName('title');content_layout.addWidget(title)
                scroll.setWidget(content);page_layout.addWidget(scroll,1);page._normal_content=content
            else:
                title=QLabel(name);title.setObjectName('title');page_layout.addWidget(title)
            self.pages.addWidget(page)
        self.footer = QLabel();self.footer.setObjectName('footer');self.footer.setWordWrap(True);root.addWidget(self.footer)
        self.build_home(); self.build_builder(); self.build_optimize(); self.build_analysis()
        self.build_evaluation(); self.build_systems(); self.build_settings();self.build_reductions();self.build_advanced_conditions()
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.currentRowChanged.connect(self.ensure_live_updates)
        self.navigation.currentRowChanged.connect(self.construction_page_changed)
        self.navigation.currentRowChanged.connect(lambda index:QTimer.singleShot(0,self.fit_scrutiny_tables) if index==4 else None)
        self.navigation.currentRowChanged.connect(lambda index:QTimer.singleShot(0,self.refresh_scrutiny_page) if index==4 else None)
        self.round_picker.currentIndexChanged.connect(self.select_round)
        self.navigation.setCurrentRow(0)
        self.load_rounds()
        self._initializing = False
        QShortcut(QKeySequence('Ctrl+Z'), self, activated=lambda: self.safe(self.undo))

    def page_layout(self, index):
        page=self.pages.widget(index)
        return getattr(page,'_normal_content',page).layout()

    def sync_page_from_tab(self, tab_index):
        if 0 <= tab_index < len(self.TAB_ORDER):
            self.navigation.setCurrentRow(self.SECTIONS.index(self.TAB_ORDER[tab_index]))

    def sync_tab_from_page(self, page_index):
        if 0 <= page_index < len(self.SECTIONS):
            section=self.SECTIONS[page_index]
            self.tabs.setCurrentIndex(self.TAB_ORDER.index(section) if section in self.TAB_ORDER else 0)

    def build_advanced_conditions(self):
        """Pestañas de reducción compactas, inspiradas en WIN1X2 y nativas Qt."""
        outer = self.page_layout(8)
        scroll=QScrollArea();scroll.setWidgetResizable(True)
        content=QWidget();layout=QVBoxLayout(content);scroll.setWidget(content);outer.addWidget(scroll,1)
        intro = QLabel('Elige un método y marca sus condiciones. El boleto base queda fijo a la izquierda; las reducciones se aplican a sus columnas.')
        intro.setWordWrap(True);layout.addWidget(intro)
        names=('Cuenta','Racha','Cambio','Patrón','Pareja','Trío','Cuart.','Quint.','Acier.','Grupo','Relac.','Frec.','Suma','Colum.','IF/THEN','Reserva','Atenea','FSSeguidos','Interrupciones')
        self.reduction_tabs=QTabWidget();self.reduction_tabs.setObjectName('reductionTabs');self.reduction_tabs.setDocumentMode(True);self.reduction_tabs.setUsesScrollButtons(True)
        self.reduction_tab_pages=[];self.reduction_tab_layouts=[]
        descriptions=('Cantidad de signos','Rachas máximas','Cambios entre partidos','Patrones repetidos','Parejas de signos','Patrones de tres partidos','Patrones de cuatro partidos','Patrones de cinco partidos','Coincidencias con referencia','Grupos gráficos','Relación entre grupos','Frecuencia de columnas','Sumas y rangos','Columnas por grupos','Condición entre grupos','Columnas de reserva','Reducción de cobertura Atenea','Figuras exactas de signos seguidos','Totales y figuras de cambios entre partidos')
        visible_reductions={0,1,9,17,18}
        self.reduction_visible_indexes={}
        self.classic_reduction_canvases={}
        self.classic_headers={}
        for index,(name,description) in enumerate(zip(names,descriptions)):
            page=QWidget();page_layout=QVBoxLayout(page);page_layout.setContentsMargins(8,8,8,8)
            if index in visible_reductions:
                visible_name='Grupo' if index==9 else 'SSeguidos' if index==1 else name
                visible_index=self.reduction_tabs.addTab(page,visible_name)
                tooltip='Rachas consecutivas de 1/X/2/V; comparte el filtro histórico Racha.' if index==1 else description
                self.reduction_tabs.setTabToolTip(visible_index,tooltip)
                self.reduction_visible_indexes[index]=visible_index
                canvas_width={0:700,1:960,9:720,17:590,18:600}[index]
                canvas_height={0:650,1:730,9:610,17:625,18:640}[index]
                # Cuenta and SSeguidos use the same plain dark workspace;
                # the old ornamental texture obscured their dense controls.
                canvas=ClassicReductionsCanvas(canvas_width,canvas_height,decorative=index not in (0,1))
                canvas_layout=QVBoxLayout(canvas)
                canvas_layout.setContentsMargins(8,4,8,10)
                canvas_layout.setSpacing(3)
                header=ClassicContextHeader(canvas)
                canvas_layout.addWidget(header)
                self.classic_reduction_canvases[index]=canvas
                self.classic_headers[index]=header
                page_layout.addWidget(canvas,0,Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)
                page_layout.addStretch(1)
                page_layout=canvas_layout
            self.reduction_tab_pages.append(page);self.reduction_tab_layouts.append(page_layout)
        layout.addWidget(self.reduction_tabs,1)
        self.reduction_active={index:False for index in range(len(names))}
        self.reduction_activation_buttons={}
        for index in sorted(visible_reductions):
            name='Grupo' if index==9 else 'SSeguidos' if index==1 else names[index]
            square=SelectionSquare(f'Aplicar condiciones de {name}',size=14,parent=self.reduction_tabs.tabBar())
            square.toggled.connect(partial(self.reduction_tab_toggled,index))
            self.reduction_tabs.tabBar().setTabButton(self.reduction_visible_indexes[index],QTabBar.ButtonPosition.RightSide,square)
            self.reduction_activation_buttons[index]=square
        # Redistribuye el editor histórico ya existente: cada condición vive en
        # una sola pestaña, sin duplicar filtros rápidos de Optimizar.
        self._place_existing_filter_rows()
        group_bar=QHBoxLayout();group_bar.addWidget(QLabel('Grupos · marca los signos aceptados por partido'))
        self.advanced_add_group=QPushButton('+ Añadir grupo');self.advanced_remove_group=QPushButton('Quitar último')
        group_bar.addWidget(self.advanced_add_group);group_bar.addWidget(self.advanced_remove_group);group_bar.addStretch();self.reduction_tab_layouts[9].addLayout(group_bar)
        self.advanced_group_scroll=QScrollArea();self.advanced_group_scroll.setObjectName('groupMatrixScroll');self.advanced_group_scroll.setWidgetResizable(True)
        self.advanced_group_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.advanced_group_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.advanced_group_canvas=QWidget();self.advanced_group_canvas.setObjectName('groupMatrixFrame');self.advanced_group_layout=QHBoxLayout(self.advanced_group_canvas)
        self.advanced_group_layout.setContentsMargins(8,8,8,8);self.advanced_group_layout.setSpacing(7)
        self.advanced_group_layout.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.advanced_group_scroll.setWidget(self.advanced_group_canvas)
        self.advanced_group_scroll.setMinimumHeight(390);self.reduction_tab_layouts[9].addWidget(self.advanced_group_scroll)
        self.advanced_groups = []
        self.advanced_add_group.clicked.connect(self.add_advanced_group)
        self.advanced_remove_group.clicked.connect(self.remove_advanced_group)
        relation_box=QGroupBox('Relación entre los grupos');relation=QGridLayout(relation_box)
        self.advanced_relation_enabled=QCheckBox('Usar una relación entre dos grupos')
        self.advanced_relation_groups=QComboBox()
        self.advanced_operation=QComboBox();self.advanced_operation.addItem('Diferencia absoluta', 'difference')
        self.advanced_relation_min=QSpinBox();self.advanced_relation_min.setRange(0,28)
        self.advanced_relation_max=QSpinBox();self.advanced_relation_max.setRange(0,28);self.advanced_relation_max.setValue(28)
        relation.addWidget(self.advanced_relation_enabled,0,0,1,5)
        relation.addWidget(self.advanced_relation_groups,1,0);relation.addWidget(self.advanced_operation,1,1);relation.addWidget(QLabel('Desde'),1,2);relation.addWidget(self.advanced_relation_min,1,3);relation.addWidget(QLabel('hasta'),1,4);relation.addWidget(self.advanced_relation_max,1,5)
        self.advanced_relation_enabled.toggled.connect(self.advanced_conditions_changed)
        self.advanced_operation.currentIndexChanged.connect(self.advanced_conditions_changed)
        self.advanced_relation_groups.currentIndexChanged.connect(self.advanced_conditions_changed)
        self.advanced_relation_min.valueChanged.connect(self.advanced_conditions_changed);self.advanced_relation_max.valueChanged.connect(self.advanced_conditions_changed)
        self.advanced_relation_min.valueChanged.connect(self.advanced_relation_max.setMinimum)
        self.advanced_relation_max.valueChanged.connect(self.advanced_relation_min.setMaximum)
        self.reduction_tab_layouts[10].addWidget(relation_box)
        # Keep group-to-group rules accessible in the retained Grupo tab.
        self.reduction_tab_layouts[9].addWidget(relation_box)
        self._build_if_then_tab()
        failures=QHBoxLayout();failures.addWidget(QLabel('¿Cuántas condiciones puede incumplir cada apuesta?'))
        self.advanced_failures=QSpinBox();self.advanced_failures.setRange(0,9);failures.addWidget(self.advanced_failures);failures.addStretch();self.reduction_tab_layouts[16].addLayout(failures)
        self.advanced_failures.valueChanged.connect(self.advanced_conditions_changed)
        self._build_pattern_tabs()
        self._build_reference_tabs()
        self._build_weighted_tab()
        self._build_columns_tabs()
        self._build_athena_tab()
        self._install_count_streak_modes()
        self._connect_reduction_controls()
        for _ in range(6):self.add_advanced_group()
        help_text=QLabel('Marca «Usar» y pulsa 1, X o 2 en cada partido. Si marcas varios signos, cualquiera de ellos sirve.')
        help_text.setWordWrap(True);self.reduction_tab_layouts[9].addWidget(help_text)
        self.advanced_feedback=QLabel();self.advanced_feedback.setWordWrap(True);self.reduction_tab_layouts[9].addWidget(self.advanced_feedback)
        layout.addWidget(self.filter_feedback);layout.addWidget(self.filter_reset)
        self._make_reduction_numeric_graphical()
        self.update_advanced_enabled()

    def _make_reduction_numeric_graphical(self):
        """Keep numeric arrows, remove free typing from all reduction controls."""
        for widget in (*self.reduction_tabs.findChildren(QSpinBox),*self.reduction_tabs.findChildren(QDoubleSpinBox)):
            widget.lineEdit().setReadOnly(True)
            widget.setMaximumWidth(72 if isinstance(widget,QSpinBox) else 110)
        for widget in self.reduction_tabs.findChildren(SignMatrixWidget):
            widget.setStyleSheet('QLabel{font-size:11px;}')

    def _place_existing_filter_rows(self):
        """Move existing controls into their one canonical reduction tab."""
        source=self.filter_group.layout()
        targets={0:0,1:0,2:0,3:2,4:2,5:8,6:1,7:1,8:1,9:8}
        boxes={}
        for tab,title in ((0,'Recuento de signos y variantes'),(1,'Rachas máximas'),(2,'Interrupciones y distancias'),(8,'Coincidencias con otra quiniela')):
            group=QGroupBox(title);grid=QGridLayout(group);boxes[tab]=(group,grid);self.reduction_tab_layouts[tab].addWidget(group)
        self._existing_filter_boxes=boxes
        row_counts={key:0 for key in boxes}
        for index in reversed(range(source.count())):
            item=source.itemAt(index);widget=item.widget()
            if widget is None:continue
            row,column,row_span,column_span=source.getItemPosition(index)
            tab=targets.get(row)
            if tab is None:continue
            source.removeWidget(widget);widget.setParent(None)
            new_row=row_counts[tab]
            boxes[tab][1].addWidget(widget,new_row,column,row_span,column_span)
            if column==0:row_counts[tab]+=1
        self.filter_group.hide()
        for tab in boxes:self.reduction_tab_layouts[tab].addStretch()

    def _build_count_profile_panel(self):
        """Compact joint V/X/2 history table; profile rows use the domain rule."""
        panel=QGroupBox('Figuras')
        panel.setObjectName('countProfilesPanel');panel.setFixedWidth(152)
        panel.setStyleSheet('QGroupBox{border:1px solid #86bfdf;border-radius:0;margin-top:9px;padding-top:2px;} QGroupBox::title{subcontrol-origin:margin;left:4px;padding:0 3px;color:#ffc83d;font-weight:bold;}')
        layout=QVBoxLayout(panel);layout.setContentsMargins(4,4,4,4);layout.setSpacing(2)
        header=QHBoxLayout();header.addWidget(QLabel('Aplicar'))
        apply_button=SelectionSquare('Aplicar perfiles conjuntos de Cuenta',size=14)
        apply_button.setChecked(self.count_profile_active)
        apply_button.toggled.connect(self._count_profile_apply_toggled)
        self.count_profile_apply_buttons.append(apply_button)
        header.addWidget(apply_button);header.addStretch(1)
        layout.addLayout(header)
        host=QWidget();host.setStyleSheet('background:#f7f7f7;color:#173c75;')
        table=QGridLayout(host);table.setContentsMargins(0,0,0,0);table.setHorizontalSpacing(2);table.setVerticalSpacing(0)
        for col,label in enumerate(('','Veces','V','X','2')):
            cell=QLabel(label);cell.setAlignment(Qt.AlignmentFlag.AlignCenter);cell.setStyleSheet('font-size:8px;color:#173c75;background:#d9e8f4;font-weight:bold;')
            table.addWidget(cell,0,col)

        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName('countFiguresList');scroll.setFixedHeight(244);scroll.setWidget(host);layout.addWidget(scroll)
        self.count_profile_panels=getattr(self,'count_profile_panels',[])
        self.count_profile_panels.append((table,host,scroll))
        self._refresh_count_profiles()
        summary=QLabel('')
        summary.setWordWrap(True);summary.setStyleSheet('font-size:8px;color:#173c75;background:#f7f7f7;')
        self.count_profile_summaries.append(summary);layout.addWidget(summary)
        return panel

    def _build_count_distribution_panel(self):
        panel=QGroupBox('Distribución Signos')
        panel.setFixedWidth(152)
        grid=QGridLayout(panel);grid.setContentsMargins(4,4,4,4);grid.setHorizontalSpacing(2);grid.setVerticalSpacing(1)
        for col,label in enumerate(('Signo','Veces','%')):
            item=QLabel(label);item.setAlignment(Qt.AlignmentFlag.AlignCenter);item.setStyleSheet('font-size:8px;color:#39d9f4;font-weight:bold;');grid.addWidget(item,0,col)
        for row,sign in enumerate(('1','X','2'),1):
            grid.addWidget(QLabel(sign),row,0)
            count=QLabel('—');percent=QLabel('—');count.setAlignment(Qt.AlignmentFlag.AlignRight);percent.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid.addWidget(count,row,1);grid.addWidget(percent,row,2)
            self.count_distribution_labels[sign]=(count,percent)
        self.count_distribution_total=QLabel('Sin temporadas seleccionadas')
        self.count_distribution_total.setWordWrap(True);self.count_distribution_total.setStyleSheet('font-size:8px;color:#a9cbe4;')
        grid.addWidget(self.count_distribution_total,4,0,1,3)
        self._refresh_count_profiles()
        return panel

    def _build_count_classic_right_panel(self,filter_panel):
        """Build Cuenta's dense seasonal distribution, filters and legacy summary."""
        panel=QWidget();panel.setObjectName('countClassicRightPanel');panel.setFixedWidth(250)
        root=QVBoxLayout(panel);root.setContentsMargins(1,0,1,0);root.setSpacing(2)
        heading=QLabel('Distribución Signos');heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet('font-size:11px;font-weight:bold;color:#62e957;padding:0;')
        root.addWidget(heading)
        self.count_season_table=QTableWidget(0,4);self.count_season_table.setObjectName('countSeasonDistribution')
        self.count_season_table.setHorizontalHeaderLabels(('1','X','2','Temporadas'))
        self.count_season_table.verticalHeader().hide()
        self.count_season_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.count_season_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.count_season_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.count_season_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.count_season_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.count_season_table.setFixedHeight(176)
        for column,width in enumerate((29,29,29,153)):self.count_season_table.setColumnWidth(column,width)
        self.count_season_table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Fixed)
        self.count_season_table.verticalHeader().setDefaultSectionSize(14)
        self.count_season_table.setStyleSheet('QTableWidget{background:#f7f7f7;color:#173c75;gridline-color:#9eb6cd;border:1px solid #8eb1cd;font-size:8px;} QHeaderView::section{background:#315b80;color:#fff;font-size:8px;padding:0;border:1px solid #7fabc9;} QTableWidget::item{padding:0 2px;}')
        self.count_season_table.itemChanged.connect(self._count_season_table_changed)
        root.addWidget(self.count_season_table)

        filters=QGroupBox('FILTROS');filters.setObjectName('countLegacyFilters')
        filters.setStyleSheet('QGroupBox{border:1px solid #9bc9e4;border-radius:0;margin-top:8px;padding:2px;color:#55e6eb;font-weight:bold;} QGroupBox::title{subcontrol-origin:margin;left:4px;padding:0 2px;}')
        filter_grid=QGridLayout(filters);filter_grid.setContentsMargins(3,3,3,3);filter_grid.setHorizontalSpacing(4);filter_grid.setVerticalSpacing(0)
        self.count_filters_layout=filter_grid
        self.count_apply_filters=SelectionSquare('Aplicar filtros históricos de Cuenta (no disponible)',size=12);self.count_apply_filters.setEnabled(False)
        self.count_obtain_percent=QPushButton('Obtener %');self.count_obtain_percent.setEnabled(False);self.count_obtain_percent.setToolTip('El cálculo de reservas y medias de WIN1X2 aún no está definido en el motor.')
        self.count_legacy_apply=SelectionSquare('Aplicar resumen de sumas (no disponible)',size=12);self.count_legacy_apply.setEnabled(False)
        filter_grid.addWidget(QLabel('Ap. Filtros'),0,0);filter_grid.addWidget(self.count_apply_filters,0,1)
        filter_grid.addWidget(self.count_obtain_percent,1,0,1,2)
        filter_grid.addWidget(QLabel('Aplicar'),2,0);filter_grid.addWidget(self.count_legacy_apply,2,1)
        filter_grid.addWidget(filter_panel,3,0,1,2)
        root.addWidget(filters)

        sums=QTableWidget(10,5);sums.setObjectName('countLegacySums');sums.setHorizontalHeaderLabels(('Condición','Valor','Reserva','Resultado','Media'))
        sums.verticalHeader().hide();sums.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        sums.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection);sums.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        sums.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        for column,width in enumerate((82,35,40,44,42)):sums.setColumnWidth(column,width)
        sums.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sums.verticalHeader().setDefaultSectionSize(18);sums.setFixedHeight(210)
        sums.setStyleSheet('QTableWidget{background:#12395d;color:#f4f8ff;gridline-color:#5692b4;border:1px solid #75b7d6;font-size:7px;} QHeaderView::section{background:#147e89;color:#fff;font-size:7px;padding:0;border:1px solid #55c8d1;} QTableWidget::item{padding:0 2px;}')
        for row,label in enumerate(('Suma Mínima','Suma Máxima','Suma Mín. (1)','Suma Máx. (1)','Suma Mín. (X)','Suma Máx. (X)','Suma Mín. (2)','Suma Máx. (2)','Suma Mín. (V)','Suma Máx. (V)')):
            sums.setRowHeight(row,18)
            label_item=QTableWidgetItem(label);label_item.setBackground(QColor('#0d6680'));sums.setItem(row,0,label_item)
            value=QTableWidgetItem('');value.setBackground(QColor('#f7f7f7'));value.setForeground(QColor('#173c75'));sums.setItem(row,1,value)
            reserve=QTableWidgetItem('');reserve.setBackground(QColor('#efc51f'));reserve.setForeground(QColor('#173c75'));sums.setItem(row,2,reserve)
            result=QTableWidgetItem('');result.setBackground(QColor('#244d79'));sums.setItem(row,3,result)
            average=QTableWidgetItem('');average.setBackground(QColor('#2879a4'));sums.setItem(row,4,average)
        root.addWidget(sums)
        self.count_legacy_sums=sums
        mark=QLabel('Reservas y medias: sin cálculo disponible');mark.setStyleSheet('font-size:7px;color:#a9cbe4;')
        root.addWidget(mark)
        self._refresh_count_season_table()
        return panel

    def _refresh_count_season_table(self):
        """Show real per-season 1/X/2 shares and mirror the automatic selector."""
        if not hasattr(self,'count_season_table') or not hasattr(self,'historical_reduction_results'):
            return
        from collections import Counter

        table=self.count_season_table;table.blockSignals(True);table.setRowCount(0)
        seasons=sorted({str(row.get('season')) for row in self.historical_reduction_results if row.get('season')},reverse=True)
        for row_index,season in enumerate(seasons):
            rounds=[item for item in self.historical_reduction_results if str(item.get('season'))==season and item.get('results14')]
            totals=Counter(sign for item in rounds for sign in item['results14']);total=sum(totals.values())
            table.insertRow(row_index)
            for column,sign in enumerate(('1','X','2')):
                item=QTableWidgetItem(f'{100*totals[sign]/total:.0f}' if total else '—')
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter);table.setItem(row_index,column,item)
            season_item=QTableWidgetItem(season);season_item.setFlags(Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsUserCheckable)
            square=self.history_season_squares.get('Cuenta',{}).get(season)
            season_item.setCheckState(Qt.CheckState.Checked if square and square.isChecked() else Qt.CheckState.Unchecked)
            table.setItem(row_index,3,season_item)
        table.blockSignals(False)

    def _count_season_table_changed(self,item):
        if item.column()!=3:return
        square=self.history_season_squares.get('Cuenta',{}).get(item.text())
        if square is not None and square.isChecked()!=(item.checkState()==Qt.CheckState.Checked):
            square.setChecked(item.checkState()==Qt.CheckState.Checked)

    def _sync_count_season_table_checks(self):
        if not hasattr(self,'count_season_table'):return
        table=self.count_season_table;table.blockSignals(True)
        for row in range(table.rowCount()):
            item=table.item(row,3)
            square=self.history_season_squares.get('Cuenta',{}).get(item.text()) if item else None
            if item and square:
                item.setCheckState(Qt.CheckState.Checked if square.isChecked() else Qt.CheckState.Unchecked)
        table.blockSignals(False)

    def _build_count_filter_panel(self):
        """Expose Cuenta's existing X-distance filter without duplicating its logic."""
        panel=QGroupBox('Distancia X')
        panel.setObjectName('countDistanceFilter');panel.setFixedWidth(240)
        panel.setToolTip('Distancia entre equis; el filtro conserva su cálculo existente.')
        row=QHBoxLayout(panel);row.setContentsMargins(4,3,4,3);row.setSpacing(4)
        check=self.filter_checks['x_distance'];check.hide()
        apply=SelectionSquare('Aplicar filtro distancia entre equis',size=14)
        apply.setChecked(check.isChecked());apply.toggled.connect(check.setChecked);check.toggled.connect(apply.setChecked)
        self.count_distance_apply=apply
        row.addWidget(apply)
        minimum,maximum=self.filter_ranges['x_distance']
        for widget in (minimum,maximum):
            parent_layout=widget.parentWidget().layout() if widget.parentWidget() else None
            if parent_layout:parent_layout.removeWidget(widget)
            widget.setParent(panel);row.addWidget(widget)
        row.addWidget(QLabel('mín.'));row.addWidget(minimum);row.addWidget(QLabel('máx.'));row.addWidget(maximum);row.addStretch(1)
        self.count_distance_filter=panel
        return panel

    def _selected_count_history_rows(self):
        selected={season for season,square in self.history_season_squares.get('Cuenta',{}).items() if square.isChecked()}
        return [row for row in self.historical_reduction_results if row.get('season') in selected and row.get('results14')]

    def _refresh_count_profiles(self):
        """Rebuild historical joint profiles and the 1/X/2 sign distribution."""
        if not hasattr(self,'historical_reduction_results') or not hasattr(self,'count_profile_panels'):
            return
        from collections import Counter

        from quiniela_ai_studio.domain.streak_statistics import count_profile
        rows=self._selected_count_history_rows()
        profiles=Counter(count_profile(row['results14']) for row in rows)
        # The classic panel lists observed joint figures only; category squares
        # still allow any manual count, including combinations absent in history.
        available=set(profiles)
        self.count_profile_squares={}
        for panel_index,(_table,_host,scroll) in enumerate(self.count_profile_panels):
            old_host=scroll.takeWidget()
            if old_host:old_host.deleteLater()
            host=QWidget();host.setStyleSheet('background:#f7f7f7;color:#173c75;')
            table=QGridLayout(host);table.setContentsMargins(0,0,0,0);table.setHorizontalSpacing(2);table.setVerticalSpacing(0)
            for column,label in enumerate(('','Veces','V','X','2')):
                cell=QLabel(label);cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setStyleSheet('font-size:8px;color:#173c75;background:#d9e8f4;font-weight:bold;')
                table.addWidget(cell,0,column)
            scroll.setWidget(host)
            self.count_profile_panels[panel_index]=(table,host,scroll)
            for row_index,profile in enumerate(sorted(available,key=lambda p:(-profiles[p],p)),1):
                variants,x_count,two_count=profile
                square=SelectionSquare(f'Permitir perfil histórico V {variants}, X {x_count}, 2 {two_count}',size=12)
                square.setChecked(profile in self.count_profiles_selected)
                square.toggled.connect(lambda checked,p=profile:self._count_profile_toggled(p,checked))
                self.count_profile_squares.setdefault(profile,[]).append(square)
                occurrences=QLabel(str(profiles[profile]));occurrences.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                table.addWidget(square,row_index,0);table.addWidget(occurrences,row_index,1)
                for col,value in enumerate(profile,2):
                    cell=QLabel(str(value));cell.setAlignment(Qt.AlignmentFlag.AlignCenter);cell.setStyleSheet('font-size:8px;')
                    table.addWidget(cell,row_index,col)
            host.setMinimumHeight(max(scroll.viewport().height(),18*(len(available)+1)))
            host.updateGeometry()
        if hasattr(self,'count_distribution_labels') and self.count_distribution_labels:
            totals=Counter(sign for row in rows for sign in row['results14'])
            total=sum(totals.values())
            for sign,(count_label,percent_label) in self.count_distribution_labels.items():
                count_label.setText(str(totals[sign]));percent_label.setText(f'{100*totals[sign]/total:.1f}%' if total else '—')
            if hasattr(self,'count_distribution_total'):
                self.count_distribution_total.setText(f'{len(rows):,} jornadas · {total:,} signos'.replace(',','.'))
        for summary in getattr(self,'count_profile_summaries',()):
            summary.setText(f'{len(rows):,} jornadas · {len(available)} perfiles históricos'.replace(',','.'))
        for _table,_host,scroll in getattr(self,'count_profile_panels',()):
            scroll.verticalScrollBar().setValue(0)

    def _count_profile_toggled(self,profile,checked):
        if checked:self.count_profiles_selected.add(profile)
        else:self.count_profiles_selected.discard(profile)
        for button in self.count_profile_squares.get(profile,()):
            if button.isChecked()!=checked:
                button.blockSignals(True);button.setChecked(checked);button.blockSignals(False)
        if not self.configuring_filters:self._manual_mode_edited('Cuenta')

    def _count_profile_apply_toggled(self,checked):
        self.count_profile_active=bool(checked)
        for button in self.count_profile_apply_buttons:
            if button.isChecked()!=checked:
                button.blockSignals(True);button.setChecked(checked);button.blockSignals(False)
        if not self.configuring_filters:self._manual_mode_edited('Cuenta')

    def _count_apply_all_toggled(self,checked):
        for button in self.count_apply.values():
            if button.isChecked()!=checked:button.setChecked(checked)

    def _sync_count_apply_all(self):
        if not hasattr(self,'count_apply_all'):return
        checked=all(button.isChecked() for button in self.count_apply.values())
        self.count_apply_all.blockSignals(True);self.count_apply_all.setChecked(checked);self.count_apply_all.blockSignals(False)

    def _count_mark_all(self):
        """Select every mathematically reachable 0–14 count in Cuenta."""
        for sign in ('V','X','2'):
            self.count_values[sign]=set(range(15))
            self.count_apply[sign].setChecked(True)
            for value in range(15):self.count_squares[(sign,value)].setChecked(True)
        self.count_apply_all.setChecked(True)
        self._manual_mode_edited('Cuenta')

    def _count_initialize(self):
        """Clear only the count matrix and its apply switches."""
        for sign in ('V','X','2'):
            self.count_values[sign].clear();self.count_apply[sign].setChecked(False)
            for value in range(15):self.count_squares[(sign,value)].setChecked(False)
        self.count_apply_all.setChecked(False)
        self._manual_mode_edited('Cuenta')

    def _count_figures_mark_all(self):
        self.count_profiles_selected=set(self.count_profile_squares)
        for buttons in self.count_profile_squares.values():
            for button in buttons:button.setChecked(True)
        self._count_profile_apply_toggled(True)
        if not self.configuring_filters:self._manual_mode_edited('Cuenta')

    def _count_figures_initialize(self):
        self.count_profiles_selected.clear()
        for buttons in self.count_profile_squares.values():
            for button in buttons:button.setChecked(False)
        self._count_profile_apply_toggled(False)
        if not self.configuring_filters:self._manual_mode_edited('Cuenta')

    def _install_count_streak_modes(self):
        """Install Cuenta unchanged and build SSeguidos from one shared state."""
        self.count_values={sign:set() for sign in ('V','X','2')}
        self.count_profiles_selected=set()
        self.count_profile_squares={}
        self.count_profile_active=False;self.count_profile_apply_buttons=[]
        self.count_profile_summaries=[]
        self.count_distribution_labels={}
        self.run_lengths={sign:set() for sign in ('1','X','2','V')}
        self.run_minmax_values={sign:{'minimum':None,'maximum':None} for sign in ('1','X','2','V')}
        self.run_count_values={sign:{} for sign in ('1','X','2','V')}
        self.run_figure_values={sign:{} for sign in ('1','X','2','V')}
        self.run_figure_totals={sign:set() for sign in ('1','X','2','V')}
        self.count_squares={};self.run_squares={};self.run_count_squares={}
        self.count_apply={sign:SelectionSquare(f'Aplicar límite {sign}',size=14) for sign in ('V','X','2')}
        self.run_apply={sign:SelectionSquare(f'Aplicar rachas de {sign}',size=14) for sign in ('1','X','2','V')}
        self.run_figure_apply={sign:SelectionSquare(f'Aplicar figuras de {sign}',size=12) for sign in ('1','X','2','V')}
        for sign,button in self.count_apply.items():
            button.toggled.connect(lambda checked,title='Cuenta':self._manual_mode_edited(title))
            button.toggled.connect(lambda _checked:self._sync_count_apply_all())
        for sign,button in self.run_apply.items():button.toggled.connect(lambda checked,title='Racha':self._manual_mode_edited(title))
        self.run_frequency_controls={}
        self.run_minmax_controls={}
        self.run_minmax_labels={}
        self.run_possible_bounds={sign:(0,14) for sign in ('1','X','2','V')}
        self.run_possible_counts={}
        self.run_possible_figures={sign:{} for sign in ('1','X','2','V')}
        self.run_count_rows={}
        self.run_figure_total_squares={}
        self.run_figure_focus={sign:None for sign in ('1','X','2','V')}
        self.run_figure_host={}
        self.run_figure_apply_labels={}
        self.run_auto_minmax_controls={}
        self.run_validation_label=None
        self.legacy_streak_rules=[]
        self.streak_risk_groups={}
        self.run_generation_metadata={}
        self.automatic_profile_rules={}
        self.random_reduction_metadata={}
        from quiniela_ai_studio.infrastructure.historical_results import bundled_results
        bundled=bundled_results()
        saved_history=self.repository.setting('reduction_historical_results',None)
        if saved_history is None:
            self.historical_reduction_results=bundled
        else:
            merged={(str(row.get('season')),str(row.get('round'))):dict(row) for row in bundled}
            for row in saved_history:
                key=(str(row.get('season')),str(row.get('round')))
                target=merged.setdefault(key,{})
                # A user's imported outcomes take precedence, while empty
                # optional markers never erase verified bundled scorelines.
                target.update({field:value for field,value in row.items() if value not in (None,'')})
            self.historical_reduction_results=list(merged.values())
        self.repository.set_setting('reduction_historical_results',self.historical_reduction_results)
        self.history_season_squares={}
        self.history_season_hosts={}
        self.history_season_grids={}
        self.history_season_select_all={}
        self.history_season_select_none={}
        self.history_season_summaries={}
        self.count_frequency_labels={};self.run_frequency_labels={}
        self.mode_azar_controls={};self.mode_automatic_controls={}
        self.mode_tabs={}
        for outer_index,title,signs,selection_map,button_map in (
            (0,'Cuenta',('V','X','2'),self.count_values,self.count_squares),
        ):
            original=self.reduction_tab_layouts[outer_index]
            manual=QWidget();manual_layout=QVBoxLayout(manual);manual_layout.setContentsMargins(4,4,4,4);manual_layout.setSpacing(3)
            classic_header=original.takeAt(0).widget() if outer_index in self.classic_headers else None
            while original.count():
                item=original.takeAt(0);widget=item.widget()
                if widget is not None:
                    widget.setParent(manual);manual_layout.addWidget(widget)
            if classic_header is not None:original.addWidget(classic_header)
            # The interval editors are superseded by the classic graphical
            # count/length grid. Keep their values in the model for migrations.
            old_box=self._existing_filter_boxes[outer_index][0]
            old_box.hide()
            if title=='Racha':
                # The legacy spin boxes remain part of filter persistence even
                # though SSeguidos now exposes only its automatic page. Keep
                # their hidden owner alive on the outer page; letting the
                # unused Manual page go out of scope would delete them in Qt.
                manual_layout.removeWidget(old_box)
                old_box.setParent(self.reduction_tab_pages[outer_index])
                old_box.hide()
            hint=('Selecciona los valores permitidos. Si una columna queda vacía, esa cuenta no limita.'
                  if title=='Cuenta' else
                  'Fija el rango de la racha máxima; 0 significa que no aparece. En V, X y 2 forman una sola racha.')
            note=QLabel(hint);note.setWordWrap(True);manual_layout.addWidget(note)
            if title=='Cuenta':note.hide()
            board=QWidget();board.setObjectName('streakSelectionBoard' if title=='Racha' else 'countSelectionBoard')
            applies=self.count_apply if title=='Cuenta' else self.run_apply
            if title=='Racha':
                # WIN1X2 presents four narrow sign columns. Keep the run values
                # and their exact-figure controls together, instead of placing
                # a second row of four wide forms below the board.
                board_layout=QHBoxLayout(board);board_layout.setContentsMargins(1,1,1,1);board_layout.setSpacing(3)
                board.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
                for sign in signs:
                    panel=QGroupBox();panel.setObjectName('streakSignPanel');panel.setFixedWidth(144)
                    panel_layout=QVBoxLayout(panel);panel_layout.setContentsMargins(3,3,3,3);panel_layout.setSpacing(2)
                    header=QHBoxLayout();header.setContentsMargins(0,0,0,0);header.setSpacing(3)
                    sign_title=QLabel(sign);sign_title.setStyleSheet('font-size:15px;font-weight:bold;color:#ffc83d;')
                    header.addWidget(sign_title);header.addStretch(1);header.addWidget(QLabel('Aplicar'));header.addWidget(applies[sign])
                    panel_layout.addLayout(header)
                    minimum=QSpinBox();minimum.setRange(0,14);minimum.setFixedWidth(38)
                    minimum.setFixedHeight(18)
                    maximum=QSpinBox();maximum.setRange(0,14);maximum.setValue(14);maximum.setFixedWidth(38)
                    maximum.setFixedHeight(18)
                    minimum.valueChanged.connect(maximum.setMinimum);maximum.valueChanged.connect(minimum.setMaximum)
                    minimum.valueChanged.connect(lambda _value,s=sign:self._streak_range_edited(s))
                    maximum.valueChanged.connect(lambda _value,s=sign:self._streak_range_edited(s))
                    minimum_label=QLabel('Mín. 0–14');maximum_label=QLabel('Máx. 0–14')
                    minimum_row=QHBoxLayout();minimum_row.setContentsMargins(0,0,0,0);minimum_row.setSpacing(2)
                    minimum_row.addWidget(minimum_label);minimum_row.addStretch(1);minimum_row.addWidget(minimum)
                    maximum_row=QHBoxLayout();maximum_row.setContentsMargins(0,0,0,0);maximum_row.setSpacing(2)
                    maximum_row.addWidget(maximum_label);maximum_row.addStretch(1);maximum_row.addWidget(maximum)
                    panel_layout.addLayout(minimum_row);panel_layout.addLayout(maximum_row)
                    self.run_minmax_controls[sign]=(minimum,maximum)
                    self.run_minmax_labels[sign]=(minimum_label,maximum_label)
                    values_table=QGridLayout();values_table.setContentsMargins(0,0,0,0)
                    values_table.setHorizontalSpacing(2);values_table.setVerticalSpacing(0)
                    for group in range(3):
                        number_heading=QLabel('N');number_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        history_heading=QLabel('Hist.');history_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        number_heading.setStyleSheet('font-size:8px;padding:0;')
                        history_heading.setStyleSheet('font-size:8px;padding:0;')
                        values_table.addWidget(number_heading,0,group*2)
                        values_table.addWidget(history_heading,0,group*2+1)
                    for value in range(15):
                        number=QLabel(str(value));number.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        number.setStyleSheet('font-size:8px;padding:0;')
                        square=SelectionValueSquare(f'Signos seguidos: {sign}, racha máxima {value}')
                        square.setFixedSize(24,13);square.setProperty('reductionValue',(sign,value));square.setText('—')
                        square.toggled.connect(lambda checked,values=selection_map,all_buttons=button_map,selected_sign=sign,selected_value=value:
                                               self._mode_square_toggled(values,all_buttons,selected_sign,selected_value,checked))
                        row=value%5+1;column=(value//5)*2
                        values_table.addWidget(number,row,column)
                        values_table.addWidget(square,row,column+1,Qt.AlignmentFlag.AlignCenter)
                        button_map[(sign,value)]=square
                        self.run_frequency_labels[(sign,value)]=square
                    panel_layout.addLayout(values_table)
                    figure_title=QLabel('Figuras · veces exactas');figure_title.setStyleSheet('font-size:9px;color:#56d8ff;')
                    panel_layout.addWidget(figure_title)
                    figure_rows=QWidget();rows_grid=QGridLayout(figure_rows)
                    rows_grid.setContentsMargins(0,0,0,0);rows_grid.setHorizontalSpacing(2);rows_grid.setVerticalSpacing(0)
                    for column,label_text in enumerate(('Usa','Fig.','Mín.','Máx.')):
                        label=QLabel(label_text);label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setStyleSheet('font-size:8px;')
                        rows_grid.addWidget(label,0,column)
                    figure_controls={}
                    for length in range(1,15):
                        enabled=SelectionSquare(f'Aplicar figura de {length} {sign} seguidos',size=11)
                        minimum_count=QSpinBox();minimum_count.setRange(0,14);minimum_count.setFixedWidth(28);minimum_count.setFixedHeight(15)
                        maximum_count=QSpinBox();maximum_count.setRange(0,14);maximum_count.setValue(14);maximum_count.setFixedWidth(28);maximum_count.setFixedHeight(15)
                        minimum_count.valueChanged.connect(maximum_count.setMinimum);maximum_count.valueChanged.connect(minimum_count.setMaximum)
                        for control in (enabled,minimum_count,maximum_count):
                            signal=getattr(control,'toggled',None) or getattr(control,'valueChanged',None)
                            signal.connect(lambda _value,title='Racha':self._manual_mode_edited(title))
                        figure_label=QLabel(f'{length}×{sign}')
                        figure_label.setStyleSheet('font-size:8px;padding:0;')
                        rows_grid.addWidget(enabled,length,0,Qt.AlignmentFlag.AlignCenter)
                        rows_grid.addWidget(figure_label,length,1)
                        rows_grid.addWidget(minimum_count,length,2)
                        rows_grid.addWidget(maximum_count,length,3)
                        figure_controls[length]=(enabled,minimum_count,maximum_count)
                    self.run_frequency_controls[sign]=figure_controls
                    figure_scroll=QScrollArea();figure_scroll.setWidgetResizable(True)
                    figure_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    figure_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                    figure_scroll.setFixedHeight(82);figure_scroll.setWidget(figure_rows)
                    panel_layout.addWidget(figure_scroll)
                    board_layout.addWidget(panel)
                board_layout.addStretch(1)
            else:
                board_layout=QGridLayout(board);board_layout.setContentsMargins(2,0,2,0);board_layout.setHorizontalSpacing(1);board_layout.setVerticalSpacing(0)
                board.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
                headers={'V':'V','X':'X','2':'2'}
                row_number=QLabel('');row_number.setFixedWidth(15);board_layout.addWidget(row_number,0,0)
                for column,sign in enumerate(signs,1):
                    head=QWidget();head.setStyleSheet('background:#e8c329;');head_layout=QHBoxLayout(head);head_layout.setContentsMargins(1,0,1,0);head_layout.setSpacing(1)
                    label=QLabel(headers[sign]);label.setFixedWidth(14);label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setStyleSheet('font-weight:bold;color:#173c75;font-size:9px;background:#e8c329;')
                    head_layout.addWidget(label);head_layout.addWidget(applies[sign]);board_layout.addWidget(head,0,column)
                for value in range(16 if title=='Cuenta' else 15):
                    number=QLabel(str(value));number.setFixedWidth(15);number.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter);number.setStyleSheet('font-size:9px;')
                    board_layout.addWidget(number,value+1,0,Qt.AlignmentFlag.AlignRight)
                    for column,sign in enumerate(signs,1):
                        square=SelectionValueSquare(f'{title}: {sign}, valor {value}')
                        square.setProperty('reductionValue',(sign,value))
                        if title=='Cuenta' and value==15:
                            square.setText('—');square.setEnabled(False)
                        else:
                            square.toggled.connect(lambda checked,values=selection_map,all_buttons=button_map,selected_sign=sign,selected_value=value:
                                                   self._mode_square_toggled(values,all_buttons,selected_sign,selected_value,checked))
                            square.setText('—')
                        board_layout.addWidget(square,value+1,column,Qt.AlignmentFlag.AlignCenter)
                        button_map[(sign,value)]=square
                        if title=='Cuenta' and value<15:self.count_frequency_labels[(sign,value)]=square
            if title=='Cuenta':
                profile_panel=self._build_count_profile_panel()
                filter_panel=self._build_count_filter_panel()
                manual_row=QWidget();manual_row.setObjectName('countManualRow')
                manual_row_layout=QHBoxLayout(manual_row);manual_row_layout.setContentsMargins(0,0,0,0);manual_row_layout.setSpacing(4)
                count_left_panel=QWidget();count_left_panel.setObjectName('countLeftPanel');count_left_panel.setFixedWidth(174)
                left_layout=QVBoxLayout(count_left_panel);left_layout.setContentsMargins(1,1,1,1);left_layout.setSpacing(2)
                count_heading=QLabel('Variantes, Equis, Doses');count_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
                count_heading.setStyleSheet('font-size:10px;font-weight:bold;color:#62e957;padding:0;');left_layout.addWidget(count_heading)
                count_action_row=QHBoxLayout();count_action_row.setContentsMargins(0,0,0,0);count_action_row.setSpacing(3)
                count_action_row.addWidget(QLabel('Aplicar'))
                self.count_apply_all=SelectionSquare('Aplicar valores de V, X y 2',size=12)
                self.count_apply_all.toggled.connect(self._count_apply_all_toggled);count_action_row.addWidget(self.count_apply_all)
                histogram=QLabel('▂ ▅ ▇');histogram.setObjectName('countHistogramIcon');histogram.setAlignment(Qt.AlignmentFlag.AlignCenter)
                histogram.setStyleSheet('font-size:15px;font-weight:bold;color:#77d94c;');histogram.setToolTip('Frecuencias históricas por cantidad')
                count_action_row.addStretch(1);count_action_row.addWidget(histogram);left_layout.addLayout(count_action_row)
                left_layout.addWidget(board,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
                count_buttons=QHBoxLayout();count_buttons.setContentsMargins(0,0,0,0);count_buttons.setSpacing(3)
                mark_counts=QPushButton('Marcar Todos');mark_counts.setObjectName('countMarkAll');mark_counts.setMaximumHeight(19)
                reset_counts=QPushButton('Inicializar');reset_counts.setObjectName('countInitialize');reset_counts.setMaximumHeight(19)
                mark_counts.clicked.connect(self._count_mark_all);reset_counts.clicked.connect(self._count_initialize)
                count_buttons.addWidget(mark_counts);count_buttons.addWidget(reset_counts);left_layout.addLayout(count_buttons)
                manual_row_layout.addWidget(count_left_panel,0,Qt.AlignmentFlag.AlignTop)
                manual_row_layout.addWidget(profile_panel,0,Qt.AlignmentFlag.AlignTop)
                figure_buttons=QHBoxLayout();figure_buttons.setContentsMargins(0,0,0,0);figure_buttons.setSpacing(3)
                mark_figures=QPushButton('Marcar Todos');mark_figures.setObjectName('countFiguresMarkAll');mark_figures.setMaximumHeight(19)
                reset_figures=QPushButton('Inicializar');reset_figures.setObjectName('countFiguresInitialize');reset_figures.setMaximumHeight(19)
                mark_figures.clicked.connect(self._count_figures_mark_all);reset_figures.clicked.connect(self._count_figures_initialize)
                figure_actions=QWidget();figure_actions.setObjectName('countFiguresActions');figure_actions_layout=QHBoxLayout(figure_actions)
                figure_actions_layout.setContentsMargins(0,0,0,0);figure_actions_layout.setSpacing(3);figure_actions_layout.addWidget(mark_figures);figure_actions_layout.addWidget(reset_figures)
                # Keep the two classic buttons directly under their own table.
                profile_panel.layout().addWidget(figure_actions)
                right_host=QWidget();right_host.setObjectName('countRightHost');right_host_layout=QVBoxLayout(right_host);right_host_layout.setContentsMargins(0,0,0,0);right_host_layout.setSpacing(0)
                manual_row_layout.addWidget(right_host,0,Qt.AlignmentFlag.AlignTop)
                manual_layout.addWidget(manual_row,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
            else:
                manual_layout.addWidget(board,0,Qt.AlignmentFlag.AlignLeft if title=='Cuenta' else Qt.AlignmentFlag.AlignTop)
            if title=='Racha':
                self.run_figures_note=QLabel('Hist. = jornadas con esa racha máxima. Las figuras cuentan rachas exactas, sin solapamiento.')
                self.run_figures_note.setWordWrap(True)
                self.run_figures_note.setStyleSheet('font-size:9px;color:#91c7ee;')
                manual_layout.addWidget(self.run_figures_note)
            if title!='Racha':manual_layout.addStretch()
            methods=QTabWidget();methods.setObjectName('reductionModeTabs');methods.setDocumentMode(True)
            if title=='Cuenta':methods.addTab(manual,'Manual')
            random_page=QWidget();random_layout=QVBoxLayout(random_page);random_layout.setContentsMargins(8,8,8,8)
            random_layout.addWidget(QLabel('Azar · crea una selección reproducible a partir de las apuestas disponibles.'))
            controls=QHBoxLayout();risk=QComboBox()
            for label,value in (('Mínimo',0),('Bajo',1),('Medio',2),('Alto',3)):risk.addItem(label,value)
            seed=QSpinBox();seed.setRange(0,2_000_000_000);seed.setValue(1)
            calculate=QPushButton('Calcular selección');controls.addWidget(QLabel('Riesgo'));controls.addWidget(risk);controls.addWidget(QLabel('Semilla'));controls.addWidget(seed);controls.addWidget(calculate);controls.addStretch()
            random_layout.addLayout(controls)
            if title=='Cuenta':
                random_row=QWidget();random_row.setObjectName('countRandomRow');random_row_layout=QHBoxLayout(random_row);random_row_layout.setContentsMargins(0,0,0,0);random_row_layout.setSpacing(4)
                random_layout.addWidget(random_row,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
            random_summary=QLabel('Los resultados se calculan sobre las apuestas del desarrollo de origen.');random_summary.setWordWrap(True);random_layout.addWidget(random_summary)
            if title!='Racha':random_layout.addStretch()
            if title=='Cuenta':methods.addTab(random_page,'Azar')
            self.mode_azar_controls[title]=(risk,seed,random_summary)
            automatic_page=QWidget();automatic_layout=QVBoxLayout(automatic_page);automatic_layout.setContentsMargins(8,8,8,8)
            mode_description=QLabel('Automática · analiza resultados finales históricos; no predice el siguiente resultado.')
            mode_description.setWordWrap(True)
            automatic_layout.addWidget(mode_description)
            imported_count=QLabel();self.history_season_summaries[title]=imported_count;automatic_layout.addWidget(imported_count)
            seasons={str(row.get('season','')) for row in self.historical_reduction_results if row.get('season')}
            season_group=QGroupBox('Temporadas a analizar');season_group.setFixedWidth(355 if title=='Racha' else 225)
            season_group_layout=QVBoxLayout(season_group);season_group_layout.setContentsMargins(5,4,5,4);season_group_layout.setSpacing(3)
            season_actions=QHBoxLayout();select_all=QPushButton('Todas');select_none=QPushButton('Ninguna')
            select_all.setMaximumWidth(68);select_none.setMaximumWidth(75);season_actions.addWidget(select_all);season_actions.addWidget(select_none);season_actions.addStretch();season_group_layout.addLayout(season_actions)
            season_host=QWidget();season_grid=QGridLayout(season_host);season_grid.setContentsMargins(1,1,1,1);season_grid.setHorizontalSpacing(3);season_grid.setVerticalSpacing(1)
            season_scroll=QScrollArea();season_scroll.setWidgetResizable(True);season_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);season_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            season_scroll.setFixedSize(335 if title=='Racha' else 205,100 if title=='Racha' else 320)
            season_scroll.setWidget(season_host);season_group_layout.addWidget(season_scroll)
            self.history_season_squares[title]={};self.history_season_hosts[title]=season_host;self.history_season_grids[title]=season_grid
            self.history_season_select_all[title]=select_all;self.history_season_select_none[title]=select_none
            self._populate_history_seasons(title,seasons,{season:True for season in seasons})
            select_all.clicked.connect(lambda _checked=False,t=title:self._set_history_seasons(t,True))
            select_none.clicked.connect(lambda _checked=False,t=title:self._set_history_seasons(t,False))
            scored=sum(bool(row.get('score_01')) for row in self.historical_reduction_results)
            self.history_season_summaries[title].setText(f'{len(seasons)} temp. · {len(self.historical_reduction_results):,} jornadas · {scored} con marcador'.replace(',','.'))
            if title=='Cuenta':
                right_panel=self._build_count_classic_right_panel(filter_panel)
                right_host_layout.addWidget(right_panel)
            auto_controls=QHBoxLayout();auto_risk=QComboBox()
            for label,value in (('Mínimo',0),('Bajo',1),('Medio',2),('Alto',3)):auto_risk.addItem(label,value)
            auto_calculate=QPushButton('Calcular');auto_controls.addWidget(QLabel('Riesgo'));auto_controls.addWidget(auto_risk);auto_controls.addWidget(auto_calculate);auto_controls.addStretch()
            auto_calculate.setEnabled(bool(seasons))
            auto_summary=QLabel('No hay resultados históricos importados.' if not seasons else 'Elige las temporadas que quieras incluir y pulsa Calcular.');auto_summary.setWordWrap(True)
            auto_panel=QGroupBox('Recomendación automática');auto_panel.setFixedWidth(230 if title=='Racha' else 205);auto_panel_layout=QVBoxLayout(auto_panel);auto_panel_layout.setContentsMargins(6,5,6,5);auto_panel_layout.setSpacing(5);auto_panel_layout.addLayout(auto_controls);auto_panel_layout.addWidget(auto_summary);auto_panel_layout.addStretch(1)
            automatic_row=QHBoxLayout();automatic_row.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop);automatic_row.setSpacing(5)
            if title=='Cuenta':
                auto_board_host=QWidget();auto_board_layout=QVBoxLayout(auto_board_host)
                auto_board_layout.setContentsMargins(0,0,0,0);auto_board_layout.setSpacing(1)
                auto_board_host.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
                auto_board_host.setFixedWidth(178)
                automatic_row.addWidget(auto_board_host,0,Qt.AlignmentFlag.AlignTop)
                if title=='Cuenta':
                    automatic_row.addWidget(profile_panel,0,Qt.AlignmentFlag.AlignTop)
                    automatic_row.addWidget(self._build_count_distribution_panel(),0,Qt.AlignmentFlag.AlignTop)
                    season_group.setFixedWidth(218)
                    season_scroll.setFixedSize(198,270)
                    automatic_row.addWidget(season_group,0,Qt.AlignmentFlag.AlignTop)
                    automatic_row.addWidget(auto_panel,0,Qt.AlignmentFlag.AlignTop)
                    automatic_layout.addLayout(automatic_row)
                    auto_filter_row=QHBoxLayout();auto_filter_row.setContentsMargins(0,0,0,0)
                    auto_filter_row.addSpacing(312);auto_filter_row.addWidget(filter_panel,0,Qt.AlignmentFlag.AlignTop);auto_filter_row.addStretch(1)
                    automatic_layout.addLayout(auto_filter_row)
                else:
                    automatic_row.addWidget(season_group,0,Qt.AlignmentFlag.AlignTop);automatic_row.addWidget(auto_panel,0,Qt.AlignmentFlag.AlignTop);automatic_row.addStretch(1);automatic_layout.addLayout(automatic_row)
            if title=='Racha':
                automatic_layout.setContentsMargins(2,2,2,2);automatic_layout.setSpacing(3)
                automatic_layout.addWidget(self.run_figures_note)
                automatic_layout.addWidget(board,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
            else:automatic_layout.addStretch(1)
            methods.addTab(automatic_page,'Automática')
            self.mode_automatic_controls[title]=(auto_risk,auto_summary,auto_calculate)
            if title=='Racha':
                # SSeguidos offers only the historical automatic method. Its
                # board is built once here; no widget is reparented on tab
                # changes, which also keeps Cuenta's board isolated.
                original.addWidget(methods)
            else:
                # Keep Cuenta's matrix inside its selected method page. Placing
                # it after an expanding QTabWidget pushed it to the bottom of
                # the window and left a large empty gap above it.
                for page in (manual,random_page,automatic_page):
                    page.layout().setContentsMargins(3,3,3,3)
                    page.layout().setSpacing(2)
                count_canvas=self.classic_reduction_canvases[0]
                def show_count_method(index,mode_widget=methods,shared_board=count_left_panel,shared_profile=profile_panel,
                                      shared_filter=filter_panel,auto_host_layout=auto_board_layout,
                                      auto_row=automatic_row,auto_filter_row=auto_filter_row,
                                      manual_row_layout=manual_row_layout,random_row_layout=random_row_layout,
                                      count_filter_layout=self.count_filters_layout,canvas=count_canvas):
                    canvas.setFixedWidth(1140 if index==2 else 700)
                    if index==2:
                        self._move_reduction_widget(shared_board,auto_host_layout)
                        self._move_reduction_widget(shared_profile,auto_row,1)
                        self._move_reduction_widget(shared_filter,auto_filter_row)
                    else:
                        row_layout=manual_row_layout if index==0 else random_row_layout
                        target_layout=mode_widget.widget(index).layout()
                        self._move_reduction_widget(shared_board,row_layout,0)
                        self._move_reduction_widget(shared_profile,row_layout,1)
                        self._move_reduction_widget(shared_filter,count_filter_layout if index==0 else target_layout)
                methods.currentChanged.connect(show_count_method)
                original.addWidget(methods)
                show_count_method(0)
            self.mode_tabs[title]=methods
            if title=='Racha':self.mode_tabs['SSeguidos']=methods
            calculate.clicked.connect(lambda _checked=False,args=(title,signs,selection_map,button_map,risk,seed,random_summary):self.safe(lambda:self.calculate_random_mode(*args)))
            auto_calculate.clicked.connect(lambda _checked=False,args=(title,signs,selection_map,button_map,auto_risk,auto_summary):self.safe(lambda:self.calculate_automatic_mode(*args)))
            if title=='Cuenta':self.count_random_summary=random_summary
            else:self.streak_random_summary=random_summary

        self._build_sseguidos_modes()
        self._build_fssiguedos_modes()
        self._build_interruption_modes()

    @staticmethod
    def _move_reduction_widget(widget,target_layout,position=None):
        """Move one shared Account control between Manual/Azar/Automática."""
        previous=widget.parentWidget();previous_layout=previous.layout() if previous else None
        if previous_layout:previous_layout.removeWidget(widget)
        widget.setParent(None)
        if position is None:target_layout.addWidget(widget,0,Qt.AlignmentFlag.AlignTop)
        else:target_layout.insertWidget(position,widget,0,Qt.AlignmentFlag.AlignTop)

    def _build_sseguidos_modes(self):
        """Build WIN1X2-like Manual/Azar/Automática pages over one state."""
        page=self.reduction_tab_pages[1]
        legacy_box=self._existing_filter_boxes[1][0]
        legacy_box.hide();legacy_box.setParent(page)
        old_layout=self.reduction_tab_layouts[1]
        classic_header=old_layout.takeAt(0).widget()
        while old_layout.count():
            item=old_layout.takeAt(0)
            if item.widget():item.widget().setParent(None)
        old_layout.addWidget(classic_header)

        methods=QTabWidget();methods.setObjectName('reductionModeTabs');methods.setDocumentMode(True)
        methods.setUsesScrollButtons(False)
        self.mode_tabs['Racha']=methods;self.mode_tabs['SSeguidos']=methods
        self.run_mode_pages={}
        self.run_minmax_widgets={sign:{} for sign in ('1','X','2','V')}

        manual=QWidget();manual_layout=QVBoxLayout(manual)
        manual_layout.setContentsMargins(3,3,3,3);manual_layout.setSpacing(3)
        heading=QLabel('Signos Seguidos · 14 partidos (Pleno al 15 excluido)')
        heading.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        heading.setStyleSheet('font-weight:bold;color:#39d9bf;font-size:12px;')
        manual_layout.addWidget(heading)
        board=QWidget();board.setObjectName('streakSelectionBoard')
        board_layout=QHBoxLayout(board);board_layout.setContentsMargins(1,1,1,1);board_layout.setSpacing(3)
        self.run_validation_label=QLabel('')
        self.run_validation_label.setWordWrap(True)
        self.run_validation_label.setStyleSheet('font-size:9px;color:#ffc83d;')
        for sign in ('1','X','2','V'):
            panel=QGroupBox();panel.setObjectName('streakSignPanel');panel.setFixedWidth(166)
            box=QVBoxLayout(panel);box.setContentsMargins(3,3,3,3);box.setSpacing(1)

            sign_header=QHBoxLayout();sign_header.setContentsMargins(0,0,0,0);sign_header.setSpacing(2)
            sign_label=QLabel(sign);sign_label.setObjectName('classicSign');sign_label.setFixedWidth(59);emboss_symbol(sign_label)
            possible=QLabel('Base 0–14');possible.setObjectName(f'streakPossible{sign}')
            possible.setStyleSheet('font-size:9px;color:#35d9f4;background:transparent;')

            limits=QVBoxLayout();limits.setContentsMargins(0,0,0,0);limits.setSpacing(1)
            low=QLineEdit();low.setObjectName(f'streakMinimum{sign}');low.setValidator(QIntValidator(0,14,low));low.setFixedSize(29,17);low.setMaxLength(2)
            high=QLineEdit();high.setObjectName(f'streakMaximum{sign}');high.setValidator(QIntValidator(0,14,high));high.setFixedSize(29,17);high.setMaxLength(2)
            low.setPlaceholderText('—');high.setPlaceholderText('—')
            limits.addWidget(possible)
            low_row=QHBoxLayout();low_row.setSpacing(2);low_row.addWidget(QLabel('Mín.'));low_row.addWidget(low)
            high_row=QHBoxLayout();high_row.setSpacing(2);high_row.addWidget(QLabel('Máx.'));high_row.addWidget(high)
            limits.addLayout(low_row);limits.addLayout(high_row)
            sign_header.addWidget(sign_label);sign_header.addLayout(limits);sign_header.addStretch(1)
            box.addLayout(sign_header)
            apply_row=QHBoxLayout();apply_row.setSpacing(3);apply_row.addWidget(QLabel('Aplicar'))
            apply_row.addWidget(self.run_apply[sign]);apply_row.addStretch(1);box.addLayout(apply_row)
            self.run_minmax_controls[sign]=(low,high)
            self.run_minmax_labels[sign]=(possible,possible)
            self.run_minmax_widgets[sign]['Manual']=(low,high)
            for editor in (low,high):
                editor.editingFinished.connect(lambda s=sign:self._streak_range_edited(s,'Manual'))

            matrix=QGridLayout();matrix.setContentsMargins(0,1,0,1);matrix.setHorizontalSpacing(1);matrix.setVerticalSpacing(0)
            matrix.addWidget(QLabel('Racha'),0,0)
            matrix_title=QLabel('Veces');matrix_title.setAlignment(Qt.AlignmentFlag.AlignCenter);matrix.addWidget(matrix_title,0,1,1,6)
            for count in range(6):
                label=QLabel(str(count));label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setStyleSheet('font-size:8px;color:#ffe85b;')
                matrix.addWidget(label,1,count+1)
            self.run_frequency_controls[sign]={}
            for length in range(2,15):
                row_label=QLabel(str(length));row_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                row_label.setStyleSheet('font-size:8px;color:#ffe85b;');matrix.addWidget(row_label,length,0)
                row_widgets=[row_label]
                self.run_count_values[sign][length]=set()
                self.run_frequency_controls[sign][length]={}
                for count in range(6):
                    cell=SelectionValueSquare(f'{sign}: {count} rachas máximas de longitud {length}')
                    cell.setFixedSize(19,13);cell.setText('—')
                    cell.setProperty('streakCount',(sign,length,count))
                    cell.toggled.connect(lambda checked,s=sign,k=length,n=count:self._streak_count_toggled(s,k,n,checked))
                    matrix.addWidget(cell,length,count+1)
                    row_widgets.append(cell)
                    self.run_count_squares[(sign,length,count)]=cell
                    self.run_frequency_controls[sign][length][count]=cell
                    self.run_frequency_labels[(sign,length,count)]=cell
                self.run_count_rows[(sign,length)]=tuple(row_widgets)
            box.addLayout(matrix)

            figure_heading=QLabel('Figuras · particiones de rachas máximas')
            figure_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
            figure_heading.setStyleSheet('font-size:9px;color:#56d8ff;')
            box.addWidget(figure_heading)
            figures_row=QHBoxLayout();figures_row.setContentsMargins(0,0,0,0);figures_row.setSpacing(2)
            total_box=QWidget();total_layout=QVBoxLayout(total_box);total_layout.setContentsMargins(0,0,0,0);total_layout.setSpacing(0)
            total_title=QLabel('Total');total_title.setStyleSheet('font-size:8px;color:#ffe85b;');total_layout.addWidget(total_title)
            total_scroll=QScrollArea();total_scroll.setObjectName(f'streakTotals{sign}');total_scroll.setWidgetResizable(True)
            total_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);total_scroll.setFixedSize(33,190)
            total_scroll.setObjectName('classicWhiteList')
            total_host=QWidget();total_host_layout=QVBoxLayout(total_host);total_host_layout.setContentsMargins(1,1,1,1);total_host_layout.setSpacing(0)
            total_host.setStyleSheet('background:#ffffff;')
            self.run_figure_total_squares[sign]={}
            for total in range(15):
                row=QWidget();row_layout=QHBoxLayout(row);row_layout.setContentsMargins(0,0,0,0);row_layout.setSpacing(2)
                square=SelectionSquare(f'Permitir total {total} de {sign}',size=10)
                label=QLabel(str(total));label.setStyleSheet('font-size:9px;color:#173b75;background:#ffffff;')
                row_layout.addWidget(square);row_layout.addWidget(label);row_layout.addStretch(1);total_host_layout.addWidget(row)
                square.toggled.connect(lambda checked,s=sign,n=total:self._streak_figure_total_toggled(s,n,checked))
                square.clicked.connect(lambda _checked=False,s=sign,n=total:self._focus_streak_figure_total(s,n))
                self.run_figure_total_squares[sign][total]=square
            total_host_layout.addStretch(1);total_scroll.setWidget(total_host);total_layout.addWidget(total_scroll)
            figures_row.addWidget(total_box)

            figure_box=QWidget();figure_layout=QVBoxLayout(figure_box);figure_layout.setContentsMargins(0,0,0,0);figure_layout.setSpacing(0)
            figures_title=QLabel('Figura');figures_title.setStyleSheet('font-size:8px;color:#ffe85b;');figure_layout.addWidget(figures_title)
            figure_scroll=QScrollArea();figure_scroll.setObjectName(f'streakFigures{sign}');figure_scroll.setWidgetResizable(True)
            figure_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);figure_scroll.setFixedSize(118,190)
            figure_scroll.setObjectName('classicWhiteList')
            figure_host=QWidget();figure_host.setObjectName(f'streakFigureList{sign}')
            figure_host_layout=QVBoxLayout(figure_host);figure_host_layout.setContentsMargins(1,1,1,1);figure_host_layout.setSpacing(0)
            figure_host.setStyleSheet('background:#ffffff;')
            figure_scroll.setWidget(figure_host);figure_layout.addWidget(figure_scroll);figures_row.addWidget(figure_box,1)
            self.run_figure_host[sign]=(figure_host,figure_host_layout)
            box.addLayout(figures_row)
            apply_figures=QHBoxLayout();apply_figures.setContentsMargins(0,0,0,0);apply_figures.setSpacing(3)
            apply_label=QLabel('Aplicar figuras');apply_label.setStyleSheet('font-size:8px;')
            apply_figures.addWidget(apply_label);apply_figures.addWidget(self.run_figure_apply[sign]);apply_figures.addStretch(1)
            box.addLayout(apply_figures);self.run_figure_apply_labels[sign]=apply_label
            self.run_figure_apply[sign].toggled.connect(lambda _checked,t='Racha':self._manual_mode_edited(t))
            board_layout.addWidget(panel)

        board_layout.addStretch(1);manual_layout.addWidget(board,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        manual_layout.addWidget(self.run_validation_label)
        footer=QHBoxLayout();footer.addStretch(1)
        initialize=QPushButton('Inicializar');initialize.setObjectName('streakInitialize')
        initialize.clicked.connect(self.initialize_streak_conditions);footer.addWidget(initialize);footer.addStretch(1)
        manual_layout.addLayout(footer);manual_layout.addStretch(1)
        self.run_figures_note=QLabel('Veces = número de rachas máximas exactas. Ej.: 1111 cuenta como una racha de longitud 4, no como tres pares.')
        self.run_figures_note.setWordWrap(True);self.run_figures_note.setVisible(False)
        heading.setToolTip(self.run_figures_note.text())
        manual_layout.insertWidget(1,self.run_figures_note)
        methods.addTab(manual,'Manual');self.run_mode_pages['Manual']=manual

        random_page=QWidget();random_layout=QVBoxLayout(random_page);random_layout.setContentsMargins(3,3,3,3);random_layout.setSpacing(4)
        random_layout.addWidget(QLabel('Azar · propuesta reproducible con la base actual; no usa temporadas.'))
        random_layout.addWidget(self._streak_summary_cards('Azar'))
        random_controls=QHBoxLayout();risk_group=self._make_streak_risk_group(random_page,'Riesgo aleatorio')
        self.streak_risk_groups['Azar']=risk_group
        risk_group.setExclusive(True);risk_group.button(0).setChecked(True)
        random_controls.addWidget(self._risk_group_box('Riesgo',risk_group),0,Qt.AlignmentFlag.AlignTop)
        seed=QSpinBox();seed.setRange(0,2_000_000_000);seed.setValue(1);seed.setFixedWidth(74)
        self.mode_azar_controls['Racha']=(risk_group,seed,None)
        random_summary=QLabel('Se muestrean columnas válidas de la base y se guardan semilla y riesgo.');random_summary.setWordWrap(True)
        self.streak_random_summary=random_summary;self.mode_azar_controls['Racha']=(risk_group,seed,random_summary)
        random_action=QVBoxLayout();seed_row=QHBoxLayout();seed_row.addWidget(QLabel('Semilla'));seed_row.addWidget(seed);seed_row.addStretch(1);random_action.addLayout(seed_row)
        random_button=QPushButton('Calcular');random_button.clicked.connect(lambda _checked=False:self.safe(lambda:self.calculate_random_mode('Racha',('1','X','2','V'),self.run_lengths,{},risk_group,seed,random_summary)))
        random_action.addWidget(random_button);random_action.addWidget(random_summary);random_action.addStretch(1)
        random_controls.addLayout(random_action,1);random_controls.addStretch(1);random_layout.addLayout(random_controls);random_layout.addStretch(1)
        methods.addTab(random_page,'Azar');self.run_mode_pages['Azar']=random_page

        automatic_page=QWidget();automatic_layout=QVBoxLayout(automatic_page);automatic_layout.setContentsMargins(3,3,3,3);automatic_layout.setSpacing(4)
        automatic_layout.addWidget(QLabel('Automática · recomendaciones descriptivas de resultados finales; no predicen el próximo resultado.'))
        automatic_layout.addWidget(self._streak_summary_cards('Automática'))
        automatic_layout.itemAt(0).widget().setVisible(False)
        seasons={str(row.get('season','')) for row in self.historical_reduction_results if row.get('season')}
        summary_label=QLabel();self.history_season_summaries['Racha']=summary_label
        scored=sum(bool(row.get('score_01')) for row in self.historical_reduction_results)
        summary_label.setText(f'{len(seasons)} temp. · {len(self.historical_reduction_results):,} jornadas · {scored} con marcador'.replace(',','.'))
        auto_row=QHBoxLayout();auto_row.setSpacing(5)
        auto_row.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        season_group=QGroupBox('Temporadas');season_group.setObjectName('streakSeasonGroup');season_group.setFixedWidth(210)
        season_group_layout=QVBoxLayout(season_group);season_group_layout.setContentsMargins(4,3,4,3);season_group_layout.setSpacing(2)
        season_actions=QHBoxLayout();select_all=QPushButton('Todas');select_none=QPushButton('Ninguna')
        select_all.setMaximumWidth(56);select_none.setMaximumWidth(64);season_actions.addWidget(select_all);season_actions.addWidget(select_none);season_actions.addStretch(1);season_group_layout.addLayout(season_actions)
        season_host=QWidget();season_grid=QGridLayout(season_host);season_grid.setContentsMargins(1,1,1,1);season_grid.setHorizontalSpacing(2);season_grid.setVerticalSpacing(1)
        season_scroll=QScrollArea();season_scroll.setWidgetResizable(True);season_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);season_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        season_scroll.setObjectName('classicWhiteList')
        season_scroll.setFixedSize(192,208);season_scroll.setWidget(season_host);season_group_layout.addWidget(season_scroll)
        season_host.setStyleSheet('background:#ffffff;QLabel{color:#163b74;background:#ffffff;font-size:10px;}')
        self.history_season_squares['Racha']={};self.history_season_hosts['Racha']=season_host;self.history_season_grids['Racha']=season_grid
        self.history_season_select_all['Racha']=select_all;self.history_season_select_none['Racha']=select_none
        current_round_key=self.round_picker.currentData()
        season_key=f'sseguidos_seasons:{current_round_key}' if current_round_key else 'sseguidos_seasons'
        saved_seasons=self.repository.setting(season_key,None)
        initial={season:(season in saved_seasons if saved_seasons is not None else True) for season in seasons}
        self._populate_history_seasons('Racha',seasons,initial)
        select_all.clicked.connect(lambda _checked=False:self._set_history_seasons('Racha',True))
        select_none.clicked.connect(lambda _checked=False:self._set_history_seasons('Racha',False))
        recommendation=QGroupBox('Riesgo');recommendation.setFixedWidth(112)
        recommendation_layout=QVBoxLayout(recommendation);recommendation_layout.setContentsMargins(4,3,4,3);recommendation_layout.setSpacing(1)
        auto_risk=self._make_streak_risk_group(recommendation,'Riesgo automático');self.streak_risk_groups['Automática']=auto_risk;auto_risk.setExclusive(True);auto_risk.button(0).setChecked(True)
        for radio in auto_risk.buttons():recommendation_layout.addWidget(radio)
        auto_row.addWidget(season_group,0,Qt.AlignmentFlag.AlignTop)
        auto_row.addWidget(recommendation,0,Qt.AlignmentFlag.AlignTop)

        calculate=QPushButton('Calcular');calculate.setObjectName('streakAutomaticCalculate');calculate.setEnabled(bool(seasons));calculate.clicked.connect(lambda _checked=False:self.safe(lambda:self.calculate_automatic_mode('Racha',('1','X','2','V'),self.run_lengths,{},auto_risk,auto_summary)))
        auto_summary=QLabel('El histórico integrado se carga con la aplicación. Selecciona una o varias temporadas.');auto_summary.setWordWrap(True)
        automatic_layout.addLayout(auto_row)
        automatic_layout.addWidget(summary_label)
        summary_label.setVisible(False)
        automatic_layout.addWidget(auto_summary)
        auto_summary.setStyleSheet('font-size:9px;color:#a8d9f2;background:transparent;')
        calculate_row=QHBoxLayout();calculate_row.addStretch(1);calculate_row.addWidget(calculate);calculate_row.addStretch(1)
        automatic_layout.addLayout(calculate_row);automatic_layout.addStretch(1)
        self.mode_automatic_controls['Racha']=(auto_risk,auto_summary,calculate)
        methods.addTab(automatic_page,'Automática');self.run_mode_pages['Automática']=automatic_page
        old_mode=self.repository.setting('sseguidos_mode','Manual')
        methods.setCurrentIndex(max(0,methods.indexOf(self.run_mode_pages.get(old_mode,manual))))
        methods.currentChanged.connect(lambda index:self.repository.set_setting('sseguidos_mode',methods.tabText(index)))
        methods.currentChanged.connect(self._resize_streak_classic_canvas)
        old_layout.addWidget(methods)
        self._resize_streak_classic_canvas(methods.currentIndex())
        self.update_streak_base_limits();self._refresh_history_statistics('Racha')

    def _resize_streak_classic_canvas(self,index):
        canvas=self.classic_reduction_canvases[1]
        canvas.setFixedSize(960,730) if index==0 else canvas.setFixedSize(950,620)

    def _build_fssiguedos_modes(self):
        """Build the separate exact run-partition reduction (FSSeguidos)."""
        from quiniela_ai_studio.domain.streak_statistics import possible_run_figures

        layout=self.reduction_tab_layouts[17]
        layout.setContentsMargins(3,3,3,3);layout.setSpacing(3)
        self.fss_mode_pages={}
        self.fss_figure_totals={sign:0 for sign in ('1','X','2','V')}
        self.fss_figure_values={sign:{} for sign in ('1','X','2','V')}
        self.fss_total_controls={};self.fss_figure_lists={};self.fss_figure_apply={}
        self.fss_possible_figures={sign:{} for sign in ('1','X','2','V')}
        self.fss_generation_metadata={}

        self.fss_context=QLabel();self.fss_context.setVisible(False);self.fss_context.setStyleSheet('font-weight:bold;color:#35d9f4;')
        layout.addWidget(self.fss_context);self._update_fss_context()
        methods=QTabWidget();methods.setObjectName('reductionModeTabs');methods.setDocumentMode(True)
        methods.setUsesScrollButtons(False);self.mode_tabs['FSSeguidos']=methods

        board=QWidget();board.setObjectName('fssFigureBoard')
        board_layout=QHBoxLayout(board);board_layout.setContentsMargins(3,3,3,3);board_layout.setSpacing(1)
        for sign in ('1','X','2','V'):
            panel=QGroupBox();panel.setObjectName('fssFigurePanel');panel.setFixedWidth(140)
            panel_layout=QVBoxLayout(panel);panel_layout.setContentsMargins(3,2,3,3);panel_layout.setSpacing(1)
            top=QHBoxLayout();top.setContentsMargins(0,0,0,0);top.setSpacing(3)
            mark=QLabel(sign);mark.setObjectName('classicSign');mark.setFixedHeight(85);emboss_symbol(mark)
            mark.setFixedWidth(75)
            total=ClassicTotalList(f'Total de signos {sign} para FSSeguidos')
            total.setObjectName(f'fssTotal{sign}')
            total.setFixedHeight(75)
            top.addWidget(mark);top.addStretch(1);top.addWidget(total)
            panel_layout.addLayout(top)
            panel_layout.addSpacing(31)
            figure_title=QLabel('Figuras');figure_title.setObjectName('classicHeading')
            panel_layout.addWidget(figure_title)
            choices=QListWidget();choices.setObjectName(f'fssFigures{sign}')
            choices.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
            choices.setFixedSize(128,220)
            panel_layout.addWidget(choices,1)
            apply_row=QHBoxLayout();apply_row.setContentsMargins(0,0,0,0);apply_row.setSpacing(4)
            apply_row.addWidget(QLabel('Aplicar'))
            square=SelectionSquare(f'Aplicar figuras exactas de {sign} en FSSeguidos',size=13)
            apply_row.addWidget(square);apply_row.addStretch(1);panel_layout.addLayout(apply_row)
            board_layout.addWidget(panel)
            self.fss_total_controls[sign]=total;self.fss_figure_lists[sign]=choices;self.fss_figure_apply[sign]=square
            total.valueChanged.connect(lambda value,s=sign:self._fss_total_changed(s,value))
            choices.itemSelectionChanged.connect(lambda s=sign:self._fss_selection_changed(s))
            square.toggled.connect(lambda _checked:self._fss_manual_edited())
        board_layout.addStretch(1)
        for sign in ('1','X','2','V'):
            self.fss_possible_figures[sign]=possible_run_figures(self._streak_base(),sign)

        def make_placeholder(name):
            host=QWidget();host.setObjectName(f'fssBoardHost{name}')
            host_layout=QVBoxLayout(host);host_layout.setContentsMargins(0,0,0,0);host_layout.setSpacing(0)
            return host,host_layout

        manual=QWidget();manual_layout=QVBoxLayout(manual);manual_layout.setContentsMargins(4,3,4,3);manual_layout.setSpacing(3)
        manual_layout.addLayout(self._fss_navigation_strip())
        manual_note=QLabel('Selecciona el total y una o varias particiones exactas de sus rachas máximas. X y 2 se agrupan como V; solo se analizan los 14 partidos.')
        manual_note.setWordWrap(True);manual_note.setVisible(False);manual_layout.addWidget(manual_note)
        manual_host,manual_host_layout=make_placeholder('Manual');manual_layout.addWidget(manual_host,0,Qt.AlignmentFlag.AlignLeft)
        initialize=QPushButton('Inicializar');initialize.setObjectName('fssInitialize');initialize.clicked.connect(self.initialize_fss_conditions)
        initialize_row=QHBoxLayout();initialize_row.addStretch(1);initialize_row.addWidget(initialize);initialize_row.addStretch(1);manual_layout.addLayout(initialize_row);manual_layout.addStretch(1)
        methods.addTab(manual,'Manual');self.fss_mode_pages['Manual']=manual

        random_page=QWidget();random_layout=QVBoxLayout(random_page);random_layout.setContentsMargins(4,3,4,3);random_layout.setSpacing(4)
        random_layout.addLayout(self._fss_navigation_strip())
        random_note=QLabel('Azar · elige figuras alcanzables con la base actual. La semilla permite repetir la propuesta.')
        random_note.setWordWrap(True);random_layout.addWidget(random_note)
        random_host,random_host_layout=make_placeholder('Azar');random_layout.addWidget(random_host,0,Qt.AlignmentFlag.AlignLeft)
        random_controls=QHBoxLayout();random_risk=self._make_streak_risk_group(random_page,'Riesgo FSSeguidos aleatorio');random_risk.setExclusive(True);random_risk.button(0).setChecked(True)
        random_controls.addWidget(self._risk_group_box('Riesgo',random_risk),0,Qt.AlignmentFlag.AlignTop)
        seed=QSpinBox();seed.setRange(0,2_000_000_000);seed.setValue(1);seed.setFixedWidth(78);seed.setAccessibleName('Semilla para FSSeguidos aleatorio')
        random_action=QVBoxLayout();seed_row=QHBoxLayout();seed_row.addWidget(QLabel('Semilla'));seed_row.addWidget(seed);seed_row.addStretch(1);random_action.addLayout(seed_row)
        random_summary=QLabel('La propuesta se genera con resultados posibles de la base actual.');random_summary.setWordWrap(True)
        random_calculate=QPushButton('Calcular');random_calculate.clicked.connect(lambda _checked=False:self.safe(lambda:self._calculate_random_fss_mode(random_risk,seed,random_summary)))
        random_action.addWidget(random_calculate);random_action.addWidget(random_summary);random_action.addStretch(1);random_controls.addLayout(random_action,1);random_controls.addStretch(1)
        random_layout.addLayout(random_controls);random_layout.addStretch(1)
        methods.addTab(random_page,'Azar');self.fss_mode_pages['Azar']=random_page
        self.mode_azar_controls['FSSeguidos']=(random_risk,seed,random_summary)

        automatic_page=QWidget();automatic_layout=QVBoxLayout(automatic_page);automatic_layout.setContentsMargins(4,3,4,3);automatic_layout.setSpacing(4)
        automatic_layout.addLayout(self._fss_navigation_strip())
        auto_note=QLabel('Automática · recomienda figuras por su frecuencia en resultados finales reales; no predice la próxima jornada.')
        auto_note.setWordWrap(True);automatic_layout.addWidget(auto_note)
        auto_host,auto_host_layout=make_placeholder('Automática');automatic_layout.addWidget(auto_host,0,Qt.AlignmentFlag.AlignLeft)
        seasons={str(row.get('season','')) for row in self.historical_reduction_results if row.get('season')}
        summary_label=QLabel();self.history_season_summaries['FSSeguidos']=summary_label
        scored=sum(bool(row.get('score_01')) for row in self.historical_reduction_results)
        summary_label.setText(f'{len(seasons)} temp. · {len(self.historical_reduction_results):,} jornadas · {scored} con marcador'.replace(',','.'))
        season_group=QGroupBox('Temporadas');season_group.setFixedWidth(400)
        season_layout=QVBoxLayout(season_group);season_layout.setContentsMargins(4,3,4,3);season_layout.setSpacing(2)
        season_actions=QHBoxLayout();select_all=QPushButton('Todas');select_none=QPushButton('Ninguna')
        select_all.setMaximumWidth(56);select_none.setMaximumWidth(64);season_actions.addWidget(select_all);season_actions.addWidget(select_none);season_actions.addStretch(1);season_layout.addLayout(season_actions)
        season_host=QWidget();season_grid=QGridLayout(season_host);season_grid.setContentsMargins(1,1,1,1);season_grid.setHorizontalSpacing(2);season_grid.setVerticalSpacing(1)
        season_scroll=QScrollArea();season_scroll.setWidgetResizable(True);season_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);season_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        season_scroll.setFixedSize(380,105);season_scroll.setWidget(season_host);season_layout.addWidget(season_scroll)
        self.history_season_squares['FSSeguidos']={};self.history_season_hosts['FSSeguidos']=season_host;self.history_season_grids['FSSeguidos']=season_grid
        current_round_key=self.round_picker.currentData();season_key=f'fsseguidos_seasons:{current_round_key}' if current_round_key else 'fsseguidos_seasons'
        saved_seasons=self.repository.setting(season_key,None)
        self._populate_history_seasons('FSSeguidos',seasons,{season:(season in saved_seasons if saved_seasons is not None else True) for season in seasons})
        select_all.clicked.connect(lambda _checked=False:self._set_history_seasons('FSSeguidos',True))
        select_none.clicked.connect(lambda _checked=False:self._set_history_seasons('FSSeguidos',False))
        season_group_layout=QHBoxLayout();season_group_layout.setContentsMargins(0,0,0,0);season_group_layout.setSpacing(5)
        auto_risk=self._make_streak_risk_group(automatic_page,'Riesgo FSSeguidos automático');auto_risk.setExclusive(True);auto_risk.button(0).setChecked(True)
        season_group_layout.addWidget(season_group,0,Qt.AlignmentFlag.AlignTop)
        season_group_layout.addWidget(self._risk_group_box('Riesgo',auto_risk),0,Qt.AlignmentFlag.AlignTop)
        automatic_page_layout=automatic_page.layout();automatic_page_layout.addLayout(season_group_layout)
        auto_summary=QLabel('El histórico integrado se carga con la aplicación. Elige temporadas y pulsa Calcular.');auto_summary.setWordWrap(True);automatic_layout.addWidget(auto_summary)
        auto_calculate=QPushButton('Calcular');auto_calculate.setEnabled(bool(seasons));auto_calculate.clicked.connect(lambda _checked=False:self.safe(lambda:self._calculate_automatic_fss_mode(auto_risk,auto_summary)))
        auto_row=QHBoxLayout();auto_row.addStretch(1);auto_row.addWidget(auto_calculate);auto_row.addStretch(1);automatic_layout.addLayout(auto_row);automatic_layout.addStretch(1)
        methods.addTab(automatic_page,'Automática');self.fss_mode_pages['Automática']=automatic_page
        self.mode_automatic_controls['FSSeguidos']=(auto_risk,auto_summary,auto_calculate)

        hosts={'Manual':(manual_host,manual_host_layout),'Azar':(random_host,random_host_layout),'Automática':(auto_host,auto_host_layout)}
        def show_shared_board(index):
            mode=methods.tabText(index);host,host_layout=hosts[mode]
            old_parent=board.parentWidget()
            old_layout=old_parent.layout() if old_parent else None
            if old_layout:old_layout.removeWidget(board)
            board.setParent(host);host_layout.addWidget(board)
        methods.currentChanged.connect(show_shared_board)
        old_mode=self.repository.setting('fsseguidos_mode','Manual')
        methods.setCurrentIndex(max(0,methods.indexOf(self.fss_mode_pages.get(old_mode,manual))))
        show_shared_board(methods.currentIndex())
        methods.currentChanged.connect(lambda index:self.repository.set_setting('fsseguidos_mode',methods.tabText(index)))
        layout.addWidget(methods,1)
        for sign in ('1','X','2','V'):
            self._refresh_fss_figure_list(sign)
        self._update_fss_context()

    def _fss_navigation_strip(self):
        """Keep the original Signos Seguidos / Figuras navigation functional."""
        row=QHBoxLayout();row.setContentsMargins(1,0,1,0);row.setSpacing(1)
        previous=QPushButton('Signos Seguidos');previous.setObjectName('classicSubTab')
        previous.clicked.connect(lambda _checked=False:self.reduction_tabs.setCurrentIndex(self.reduction_visible_indexes[1]))
        current=QPushButton('Figuras Signos Seg.');current.setObjectName('classicSubTab')
        current.setCheckable(True);current.setChecked(True)
        current.clicked.connect(lambda _checked=False:self.reduction_tabs.setCurrentIndex(self.reduction_visible_indexes[17]))
        row.addWidget(previous);row.addWidget(current);row.addStretch(1)
        return row

    def _update_fss_context(self):
        if not hasattr(self,'fss_context'):return
        try:round_=self.round
        except ValueError:
            self.fss_context.setText('Temporada: —    Jornada: —');return
        self.fss_context.setText(f'Temporada: {round_.season}    Jornada: {round_.number}')

    def _refresh_fss_figure_list(self,sign):
        from quiniela_ai_studio.domain.streak_statistics import possible_run_figures
        if sign not in self.fss_figure_lists:return
        self.fss_possible_figures[sign]=possible_run_figures(self._streak_base(),sign)
        total=self.fss_total_controls[sign].value();widget=self.fss_figure_lists[sign]
        self.fss_total_controls[sign].set_allowed_totals(set(self.fss_possible_figures[sign]),
            set(self.fss_figure_values[sign]))
        selected=self.fss_figure_values[sign].get(total,set());possible=self.fss_possible_figures[sign].get(total,())
        widget.blockSignals(True);widget.clear()
        figures=sorted(set(possible)|selected,key=lambda figure:tuple(-int(part) for part in figure.split('-')) if figure else ())
        if not figures:
            widget.setToolTip('No hay figuras alcanzables con este total y esta base.')
        for figure in figures:
            label=figure or '∅ · sin signos'
            if figure not in possible:label+=' · base cambió'
            widget.addItem(label)
            item=widget.item(widget.count()-1);item.setData(Qt.ItemDataRole.UserRole,figure)
            item.setSelected(figure in selected)
            if figure not in possible:
                item.setToolTip('La selección se conserva, aunque la base actual no pueda alcanzar esta figura.')
        widget.blockSignals(False)

    def _fss_total_changed(self,sign,total):
        self.fss_figure_totals[sign]=int(total)
        if self.fss_figure_apply[sign].isChecked() and not self.fss_figure_values[sign].get(int(total)):
            self.fss_figure_apply[sign].setChecked(False)
        self._refresh_fss_figure_list(sign)
        self._fss_manual_edited()

    def _fss_selection_changed(self,sign):
        widget=self.fss_figure_lists[sign];total=self.fss_total_controls[sign].value()
        selected={str(item.data(Qt.ItemDataRole.UserRole)) for item in widget.selectedItems()
                  if item.data(Qt.ItemDataRole.UserRole) is not None}
        self.fss_figure_values[sign][total]=selected
        if not selected and self.fss_figure_apply[sign].isChecked():
            self.fss_figure_apply[sign].setChecked(False)
        self._fss_manual_edited()

    def _fss_manual_edited(self):
        if self.configuring_filters:return
        self.fss_generation_metadata={}
        self.manual_filters_changed()

    def initialize_fss_conditions(self):
        """Clear only FSSeguidos choices, leaving SSeguidos and the ballot intact."""
        self.configuring_filters=True
        try:
            for sign in ('1','X','2','V'):
                self.fss_figure_values[sign].clear();self.fss_figure_totals[sign]=0
                self.fss_total_controls[sign].setValue(0);self.fss_figure_apply[sign].setChecked(False)
                self._refresh_fss_figure_list(sign)
        finally:self.configuring_filters=False
        self.fss_generation_metadata={};self.manual_filters_changed()

    def _install_fss_selections(self,selections,*,method,risk,seed=None,seasons=(),sample_size=0,coverage=1.0):
        """Render domain-recommended sign/total/figure sets in the shared board."""
        self.configuring_filters=True
        try:
            for sign in ('1','X','2','V'):
                self.fss_figure_values[sign].clear();self.fss_figure_totals[sign]=0
                self.fss_total_controls[sign].setValue(0)
                options=selections.get(sign,{})
                if not options:
                    self.fss_figure_apply[sign].setChecked(False)
                    self._refresh_fss_figure_list(sign)
                    continue
                chosen_total=max(options,key=lambda total:(len(options[total]),-total))
                self.fss_figure_totals[sign]=chosen_total
                self.fss_total_controls[sign].setValue(chosen_total)
                self.fss_figure_values[sign]={int(total):set(figures) for total,figures in options.items()}
                self.fss_figure_apply[sign].setChecked(bool(options[chosen_total]))
                self._refresh_fss_figure_list(sign)
        finally:self.configuring_filters=False
        self.fss_generation_metadata={'method':method,'risk':risk,'seed':seed,
            'seasons':tuple(sorted(seasons)),'sample_size':int(sample_size),
            'coverage':float(coverage),'source':'histórico integrado' if method=='automática' else 'muestra reproducible de la base'}
        self.manual_filters_changed()

    def _calculate_random_fss_mode(self,risk,seed,summary):
        """Choose reproducible exact figures observed in random valid base completions."""
        from quiniela_ai_studio.domain.streak_statistics import (
            random_figure_recommendations,
        )
        level,label=self._risk_value(risk);fraction={0:.80,1:.55,2:.30}[level]
        selections,columns=random_figure_recommendations(self._streak_base(),seed.value(),fraction)
        self._install_fss_selections(selections,method='azar',risk=label,seed=seed.value(),sample_size=len(columns),coverage=fraction)
        rules=[rule for rule in self.build_reduction_rules() if rule.tab_index==17 and rule.active]
        admitted=sum(all(rule.accepts(column) for rule in rules) for column in columns) if rules else len(columns)
        summary.setText(f'Semilla {seed.value()} · {admitted}/512 columnas de prueba admitidas · riesgo {label}. Muestra reproducible, no recuento exacto del universo.')

    def _calculate_automatic_fss_mode(self,risk,summary):
        """Recommend per-sign figures from actual selected final-result rows."""
        from quiniela_ai_studio.domain.streak_statistics import (
            historical_figure_recommendations,
        )
        seasons={season for season,square in self.history_season_squares.get('FSSeguidos',{}).items() if square.isChecked()}
        columns=[row['results14'] for row in self.historical_reduction_results if row.get('season') in seasons and row.get('results14')]
        if not columns:raise ValueError('Selecciona temporadas con resultados finales del histórico integrado.')
        level,label=self._risk_value(risk);coverage={0:1.0,1:.75,2:.50}[level]
        selections,matched=historical_figure_recommendations(columns,self._streak_base(),coverage)
        self._install_fss_selections(selections,method='automática',risk=label,seasons=seasons,
            sample_size=len(columns),coverage=coverage)
        summary.setText(f'{len(columns)} resultados finales · {matched} cumplen las figuras elegidas · {len(seasons)} temporadas · riesgo {label} ({coverage:.0%} por signo). Descriptivo, no predictivo.')

    def _build_fssiguedos_rules(self):
        """Persist selected partitions; only current total and checked signs are active."""
        from quiniela_ai_studio.domain.reduction_rules import ReductionRule
        metadata=self.fss_generation_metadata
        rules=[]
        for sign in ('1','X','2','V'):
            current=self.fss_total_controls[sign].value();selected_for_current=self.fss_figure_values[sign].get(current,set())
            impossible=selected_for_current-set(self.fss_possible_figures[sign].get(current,()))
            if self.fss_figure_apply[sign].isChecked() and impossible:
                raise ValueError(f'La base actual no alcanza las figuras de {sign}, total {current}: {", ".join(sorted(impossible))}.')
            common={'sign':sign,'generation_method':metadata.get('method','manual'),
                'generation_seed':metadata.get('seed'),'generation_risk':metadata.get('risk',''),
                'evidence_source':metadata.get('source',''),'evidence_seasons':tuple(metadata.get('seasons',())),
                'evidence_sample_size':int(metadata.get('sample_size',0)),
                'evidence_coverage':float(metadata.get('coverage',0)),'tab_index':17}
            for total,figures in sorted(self.fss_figure_values[sign].items(),key=lambda item:(item[0]==current,item[0])):
                if not figures:continue
                ordered=tuple(sorted(figures,key=lambda figure:tuple(-int(part) for part in figure.split('-')) if figure else ()))
                rules.append(ReductionRule(f'fss-figure-{sign}-{total}','allowed_run_figure',0,1,
                    allowed_figures=ordered,run_length=total,active=self.fss_figure_apply[sign].isChecked() and total==current,**common))
            if (not selected_for_current and
                    (current!=0 or self.fss_figure_values[sign] or self.fss_figure_apply[sign].isChecked() or metadata)):
                rules.append(ReductionRule(f'fss-current-{sign}','allowed_run_figure',0,1,
                    allowed_figures=(),run_length=current,active=False,**common))
        return rules

    def _build_interruption_modes(self):
        """Build separate Manual/Azar/Automática panels for transition filters."""
        from quiniela_ai_studio.domain.interruption_statistics import (
            possible_interruption_profiles,
        )

        layout=self.reduction_tab_layouts[18];layout.setContentsMargins(3,3,3,3);layout.setSpacing(3)
        self.interruption_selected_pairs=set()
        self.interruption_selected_totals=set()
        self.interruption_selected_figures=set()
        self.interruption_figure_buttons={}
        self.interruption_generation_metadata={}
        methods=QTabWidget();methods.setObjectName('reductionModeTabs');methods.setDocumentMode(True);methods.setUsesScrollButtons(False)
        self.mode_tabs['Interrupciones']=methods
        self.interruption_context=QLabel();self.interruption_context.setVisible(False);self.interruption_context.setStyleSheet('font-weight:bold;color:#35d9f4;')
        self._update_interruption_context()
        layout.addWidget(self.interruption_context)

        board=QWidget();board.setObjectName('interruptionAndDistanceBoard')
        board_layout=QHBoxLayout(board);board_layout.setContentsMargins(2,2,2,2);board_layout.setSpacing(4)
        left=QGroupBox('Interrupciones');left.setObjectName('interruptionPanel');left.setFixedWidth(300)
        left_layout=QVBoxLayout(left);left_layout.setContentsMargins(4,4,4,4);left_layout.setSpacing(2)
        left_apply_row=QHBoxLayout();left_apply_row.addStretch(1);left_apply_row.addWidget(QLabel('Aplicar'))
        self.interruption_apply=SelectionSquare('Aplicar la matriz de interrupciones',size=14)
        self.interruption_apply.toggled.connect(self._interruption_manual_edited);left_apply_row.addWidget(self.interruption_apply)
        left_apply_row.addStretch(1);left_layout.addLayout(left_apply_row)
        left_note=QLabel('Fila = total de cambios · columna = racha máxima de cambios seguidos')
        left_note.setVisible(False);left_layout.addWidget(left_note)
        self.interruption_matrix=InterruptionMatrix();self.interruption_matrix.changed.connect(self._interruption_matrix_changed)
        left_layout.addWidget(self.interruption_matrix,0,Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)
        left_actions=QHBoxLayout();left_actions.addStretch(1)
        mark_left=QPushButton('Marca todos');mark_left.setMaximumWidth(92)
        reset_left=QPushButton('Inicializar');reset_left.setMaximumWidth(82)
        mark_left.clicked.connect(self._mark_all_interruption_pairs);reset_left.clicked.connect(self._reset_interruption_matrix)
        left_actions.addWidget(mark_left);left_actions.addWidget(reset_left);left_actions.addStretch(1);left_layout.addLayout(left_actions)
        board_layout.addWidget(left,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        right=QGroupBox('Distancias');right.setObjectName('distanceFigurePanel');right.setFixedWidth(255)
        right_layout=QVBoxLayout(right);right_layout.setContentsMargins(4,4,4,4);right_layout.setSpacing(2)
        right_apply_row=QHBoxLayout();right_apply_row.addStretch(1);right_apply_row.addWidget(QLabel('Aplicar'))
        self.distance_apply=SelectionSquare('Aplicar figuras exactas de interrupciones',size=14)
        self.distance_apply.toggled.connect(self._interruption_manual_edited);right_apply_row.addWidget(self.distance_apply);right_apply_row.addStretch(1)
        right_layout.addLayout(right_apply_row)
        lists=QHBoxLayout();lists.setContentsMargins(0,0,0,0);lists.setSpacing(3)
        totals_box=QVBoxLayout();totals_box.addWidget(QLabel('Total'))
        totals_host=QWidget();totals_grid=QGridLayout(totals_host);totals_grid.setContentsMargins(0,0,0,0);totals_grid.setHorizontalSpacing(2);totals_grid.setVerticalSpacing(1)
        self.interruption_total_buttons={};self.interruption_total_labels={}
        self.interruption_focus_total=None
        for total in range(14):
            square=SelectionSquare(f'Permitir {total} interrupciones en Distancias',size=13)
            square.toggled.connect(lambda checked,value=total:self._interruption_total_toggled(value,checked))
            square.clicked.connect(lambda _checked=False,value=total:self._focus_interruption_total(value))
            label=QLabel(str(total));label.setFixedWidth(18)
            label.setStyleSheet('color:#173b75;background:#ffffff;font-size:10px;')
            totals_grid.addWidget(square,total,0);totals_grid.addWidget(label,total,1)
            self.interruption_total_buttons[total]=square;self.interruption_total_labels[total]=label
        totals_scroll=QScrollArea();totals_scroll.setWidgetResizable(True);totals_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        totals_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded);totals_scroll.setFixedSize(45,330);totals_scroll.setWidget(totals_host)
        totals_scroll.setObjectName('classicWhiteList');totals_host.setStyleSheet('background:#ffffff;')
        totals_box.addWidget(totals_scroll);lists.addLayout(totals_box)
        figures_box=QVBoxLayout();figures_box.addWidget(QLabel('Figuras'))
        self.interruption_figure_host=QWidget();self.interruption_figure_layout=QVBoxLayout(self.interruption_figure_host)
        self.interruption_figure_layout.setContentsMargins(1,1,1,1);self.interruption_figure_layout.setSpacing(1)
        self.interruption_figure_scroll=QScrollArea();self.interruption_figure_scroll.setWidgetResizable(True)
        self.interruption_figure_scroll.setFixedSize(180,330);self.interruption_figure_scroll.setWidget(self.interruption_figure_host)
        self.interruption_figure_scroll.setObjectName('classicWhiteList')
        self.interruption_figure_host.setStyleSheet('background:#ffffff;')
        figures_box.addWidget(self.interruption_figure_scroll);lists.addLayout(figures_box)
        right_layout.addLayout(lists)
        right_actions=QHBoxLayout();right_actions.addStretch(1)
        mark_right=QPushButton('Marca todos');mark_right.setMaximumWidth(92)
        reset_right=QPushButton('Inicializar');reset_right.setMaximumWidth(82)
        mark_right.clicked.connect(self._mark_all_interruption_figures);reset_right.clicked.connect(self._reset_interruption_figures)
        right_actions.addWidget(mark_right);right_actions.addWidget(reset_right);right_actions.addStretch(1);right_layout.addLayout(right_actions)
        board_layout.addWidget(right,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        board_layout.addStretch(1)
        surfaces=QStackedWidget()
        surfaces.addWidget(board)
        surfaces.addWidget(self._build_sign_distance_view())
        self.interruption_surfaces=surfaces
        self.interruption_subtab_index=0
        self.interruption_subtab_buttons=[]

        def subtab_row():
            row=QHBoxLayout();row.setContentsMargins(2,0,2,0);row.setSpacing(1)
            buttons=[]
            for index,label in enumerate(('Interrupciones','Distancias')):
                button=QPushButton(label);button.setCheckable(True);button.setObjectName('classicSubTab')
                button.setFixedWidth(112 if index==0 else 82)
                button.setAccessibleName(f'Mostrar {label} de la reducción Interrupciones')
                button.clicked.connect(lambda _checked=False,target=index:self._show_interruption_subtab(target))
                row.addWidget(button);buttons.append(button)
            row.addStretch(1)
            self.interruption_subtab_buttons.append(buttons)
            buttons[0].setChecked(True)
            return row

        def host_for(page_name):
            host=QWidget();host.setObjectName(f'interruptionBoardHost{page_name}')
            host_layout=QVBoxLayout(host);host_layout.setContentsMargins(0,0,0,0);host_layout.setSpacing(0)
            return host,host_layout

        pages={};hosts={}
        manual=QWidget();manual_layout=QVBoxLayout(manual);manual_layout.setContentsMargins(3,3,3,3);manual_layout.setSpacing(3)
        manual_note=QLabel('Marca en verde los totales y las figuras admitidas. Los cambios se miden entre los 14 partidos; el Pleno queda fuera.')
        manual_note.setWordWrap(True);manual_note.setVisible(False);manual_note.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Fixed)
        manual_layout.addWidget(manual_note)
        manual_layout.addLayout(subtab_row())
        host,host_layout=host_for('Manual');manual_layout.addWidget(host,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop);pages['Manual']=manual;hosts['Manual']=(host,host_layout)
        methods.addTab(manual,'Manual')

        random_page=QWidget();random_layout=QVBoxLayout(random_page);random_layout.setContentsMargins(3,3,3,3);random_layout.setSpacing(3)
        random_note=QLabel('Azar · propone perfiles alcanzables desde la base actual. La semilla permite repetir el cálculo.')
        random_note.setWordWrap(True);random_note.setVisible(False);random_note.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Fixed);random_layout.addWidget(random_note)
        random_layout.addLayout(subtab_row())
        host,host_layout=host_for('Azar');random_layout.addWidget(host,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop);pages['Azar']=random_page;hosts['Azar']=(host,host_layout)
        random_row=QHBoxLayout();random_risk=QComboBox()
        for label,value in (('Mínimo',0),('Medio',1),('Máximo',2)):random_risk.addItem(label,value)
        seed=QSpinBox();seed.setRange(0,2_000_000_000);seed.setValue(1);seed.setFixedWidth(78)
        seed.setAccessibleName('Semilla para Interrupciones aleatorias')
        random_calculate=QPushButton('Calcular');random_calculate.clicked.connect(lambda _checked=False:self.safe(lambda:self._calculate_random_interruption_mode(random_risk,seed,random_summary)))
        random_row.addWidget(QLabel('Riesgo'));random_row.addWidget(random_risk);random_row.addWidget(QLabel('Semilla'));random_row.addWidget(seed);random_row.addWidget(random_calculate);random_row.addStretch(1)
        random_layout.addLayout(random_row);random_summary=QLabel('Riesgo mínimo seleccionado.');random_summary.setWordWrap(True);random_layout.addWidget(random_summary);random_layout.addStretch(1)
        methods.addTab(random_page,'Azar');self.mode_azar_controls['Interrupciones']=(random_risk,seed,random_summary)

        automatic_page=QWidget();automatic_layout=QVBoxLayout(automatic_page);automatic_layout.setContentsMargins(3,3,3,3);automatic_layout.setSpacing(3)
        auto_note=QLabel('Automática · estadísticas descriptivas de resultados finales ya incluidos en la aplicación; no predice el siguiente resultado.')
        auto_note.setWordWrap(True);auto_note.setVisible(False);auto_note.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Fixed);automatic_layout.addWidget(auto_note)
        automatic_layout.addLayout(subtab_row())
        host,host_layout=host_for('Automática');automatic_layout.addWidget(host,0,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop);pages['Automática']=automatic_page;hosts['Automática']=(host,host_layout)
        seasons={str(row.get('season','')) for row in self.historical_reduction_results if row.get('season')}
        season_label=QLabel();self.history_season_summaries['Interrupciones']=season_label
        season_label.setText(f'{len(seasons)} temp. · {len(self.historical_reduction_results):,} jornadas'.replace(',','.'))
        season_group=QGroupBox('Temporadas');season_group.setFixedWidth(180)
        season_layout=QVBoxLayout(season_group);season_layout.setContentsMargins(4,3,4,3);season_layout.setSpacing(2)
        actions=QHBoxLayout();select_all=QPushButton('Todas');select_none=QPushButton('Ninguna')
        select_all.setMaximumWidth(58);select_none.setMaximumWidth(66);actions.addWidget(select_all);actions.addWidget(select_none);actions.addStretch(1);season_layout.addLayout(actions)
        season_host=QWidget();season_grid=QGridLayout(season_host);season_grid.setContentsMargins(1,1,1,1);season_grid.setHorizontalSpacing(2);season_grid.setVerticalSpacing(1)
        season_scroll=QScrollArea();season_scroll.setWidgetResizable(True);season_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        season_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded);season_scroll.setFixedSize(162,124);season_scroll.setWidget(season_host);season_layout.addWidget(season_scroll)
        self.history_season_squares['Interrupciones']={};self.history_season_hosts['Interrupciones']=season_host;self.history_season_grids['Interrupciones']=season_grid
        self.history_season_select_all['Interrupciones']=select_all;self.history_season_select_none['Interrupciones']=select_none
        key=self._interruption_season_setting_key();saved=self.repository.setting(key,None)
        self._populate_history_seasons('Interrupciones',seasons,{season:(season in saved if saved is not None else True) for season in seasons})
        select_all.clicked.connect(lambda _checked=False:self._set_history_seasons('Interrupciones',True))
        select_none.clicked.connect(lambda _checked=False:self._set_history_seasons('Interrupciones',False))
        controls=QHBoxLayout();auto_risk=QComboBox()
        for label,value in (('Mínimo',0),('Medio',1),('Máximo',2)):auto_risk.addItem(label,value)
        auto_calculate=QPushButton('Calcular');auto_summary=QLabel('Elige temporadas y calcula una recomendación basada en los resultados reales disponibles.')
        auto_summary.setWordWrap(True);auto_calculate.setEnabled(bool(seasons))
        auto_calculate.clicked.connect(lambda _checked=False:self.safe(lambda:self._calculate_automatic_interruption_mode(auto_risk,auto_summary)))
        controls.addWidget(QLabel('Riesgo'));controls.addWidget(auto_risk);controls.addWidget(auto_calculate);controls.addStretch(1)
        season_label.setVisible(False)
        automatic_layout.addWidget(season_label)
        compact_auto=QHBoxLayout();compact_auto.addLayout(controls);compact_auto.addStretch(1)
        compact_auto.addWidget(season_group,0,Qt.AlignmentFlag.AlignTop)
        automatic_layout.addLayout(compact_auto);automatic_layout.addWidget(auto_summary);automatic_layout.addStretch(1)
        methods.addTab(automatic_page,'Automática');self.mode_automatic_controls['Interrupciones']=(auto_risk,auto_summary,auto_calculate)

        def show_shared_board(index):
            name=methods.tabText(index);destination,host_layout=hosts[name]
            previous=surfaces.parentWidget();previous_layout=previous.layout() if previous else None
            if previous_layout:previous_layout.removeWidget(surfaces)
            surfaces.setParent(destination);host_layout.addWidget(surfaces)
        methods.currentChanged.connect(show_shared_board)
        old_mode=self.repository.setting('interrupciones_mode','Manual')
        methods.setCurrentIndex(max(0,methods.indexOf(pages.get(old_mode,manual))))
        show_shared_board(methods.currentIndex())
        methods.currentChanged.connect(lambda index:self.repository.set_setting('interrupciones_mode',methods.tabText(index)))
        layout.addWidget(methods,1)
        self.interruption_mode_pages=pages
        profiles=possible_interruption_profiles(self._streak_base())
        self.interruption_possible_profiles=set(profiles)
        self.interruption_possible_figures={total:{figure for candidate,_,figure in profiles if candidate==total}
                                             for total in range(14)}
        self._update_interruption_base()

    def _show_interruption_subtab(self,index):
        self.interruption_subtab_index=index
        self.interruption_surfaces.setCurrentIndex(index)
        for buttons in self.interruption_subtab_buttons:
            for candidate,button in enumerate(buttons):
                button.blockSignals(True);button.setChecked(candidate==index);button.blockSignals(False)

    def _build_sign_distance_view(self):
        """Build the independent 1/X/2/V maximum-distance panel."""
        view=QWidget();layout=QVBoxLayout(view)
        layout.setContentsMargins(3,4,3,3);layout.setSpacing(3)
        columns=QHBoxLayout();columns.setContentsMargins(0,0,0,0);columns.setSpacing(1)
        self.sign_distance_values={sign:set() for sign in ('1','X','2','V')}
        self.sign_distance_apply={};self.sign_distance_squares={}
        self.sign_distance_possible={sign:set() for sign in ('1','X','2','V')}
        for sign in ('1','X','2','V'):
            panel=QGroupBox();panel.setFixedWidth(103)
            panel_layout=QVBoxLayout(panel);panel_layout.setContentsMargins(3,2,3,3);panel_layout.setSpacing(0)
            mark=QLabel(sign);mark.setObjectName('classicSign');emboss_symbol(mark)
            mark.setAlignment(Qt.AlignmentFlag.AlignCenter);panel_layout.addWidget(mark)
            for distance in range(15):
                row=QHBoxLayout();row.setContentsMargins(5,0,5,0);row.setSpacing(3)
                label=QLabel(str(distance));label.setFixedWidth(18)
                label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                square=SelectionSquare(f'Distancia máxima {distance} entre {sign}',size=12)
                square.toggled.connect(lambda checked,s=sign,n=distance:self._sign_distance_toggled(s,n,checked))
                row.addWidget(label);row.addWidget(square);row.addStretch(1)
                panel_layout.addLayout(row)
                self.sign_distance_squares[(sign,distance)]=square
            apply_row=QHBoxLayout();apply_row.setSpacing(2)
            square=SelectionSquare(f'Aplicar distancias de {sign}',size=12)
            square.toggled.connect(self._interruption_manual_edited)
            apply_row.addWidget(square);apply_row.addWidget(QLabel('Aplicar'))
            panel_layout.addLayout(apply_row);self.sign_distance_apply[sign]=square
            columns.addWidget(panel)
        columns.addStretch(1);layout.addLayout(columns)
        actions=QHBoxLayout();actions.addSpacing(150)
        reset=QPushButton('Inicializar');reset.clicked.connect(self.initialize_sign_distances)
        actions.addWidget(reset);actions.addStretch(1);layout.addLayout(actions)
        layout.addStretch(1)
        return view

    def _sign_distance_toggled(self,sign,distance,checked):
        if checked:self.sign_distance_values[sign].add(distance)
        else:self.sign_distance_values[sign].discard(distance)
        self._interruption_manual_edited()

    def initialize_sign_distances(self):
        self.configuring_filters=True
        try:
            for sign in ('1','X','2','V'):
                self.sign_distance_values[sign].clear()
                self.sign_distance_apply[sign].setChecked(False)
                for distance in range(15):self.sign_distance_squares[(sign,distance)].setChecked(False)
        finally:self.configuring_filters=False
        self._interruption_manual_edited()

    def _update_sign_distance_base(self):
        from quiniela_ai_studio.domain.sign_distance import possible_sign_distances
        base=self._streak_base()
        for sign in ('1','X','2','V'):
            possible=set(possible_sign_distances(base,sign))
            self.sign_distance_possible[sign]=possible
            for distance in range(15):
                button=self.sign_distance_squares[(sign,distance)]
                button.setEnabled(distance in possible or distance in self.sign_distance_values[sign])
                button.setToolTip(f'Máxima separación entre apariciones consecutivas de {sign}: {distance}. '
                                  +('Alcanzable desde la base.' if distance in possible else 'No alcanzable desde la base.'))

    def _interruption_season_setting_key(self):
        current=self.round_picker.currentData()
        return f'interrupciones_seasons:{current}' if current else 'interrupciones_seasons'

    def _restore_interruption_seasons_for_round(self):
        selected=self.repository.setting(self._interruption_season_setting_key(),None)
        if selected is None:return
        selected=set(selected);self.configuring_filters=True
        try:
            for season,square in self.history_season_squares.get('Interrupciones',{}).items():
                square.setChecked(season in selected)
        finally:self.configuring_filters=False

    def _update_interruption_context(self):
        if not hasattr(self,'interruption_context'):return
        try:round_=self.round
        except ValueError:self.interruption_context.setText('Temporada: —    Jornada: —');return
        self.interruption_context.setText(f'Temporada: {round_.season}    Jornada: {round_.number}')

    def _update_interruption_base(self):
        if not hasattr(self,'interruption_matrix'):return
        from quiniela_ai_studio.domain.interruption_statistics import (
            possible_interruption_profiles,
        )
        profiles=set(possible_interruption_profiles(self._streak_base()))
        self.interruption_possible_profiles=profiles
        reachable={(total,maximum) for total,maximum,_figure in profiles}
        self.interruption_matrix.set_reachable(reachable)
        self.interruption_possible_figures={total:{figure for candidate,_,figure in profiles if candidate==total}
                                             for total in range(14)}
        for total,button in self.interruption_total_buttons.items():
            visible=bool(self.interruption_possible_figures.get(total)) or total in self.interruption_selected_totals
            button.setEnabled(visible);button.setVisible(visible)
            self.interruption_total_labels[total].setVisible(visible)
        if self.interruption_focus_total not in self.interruption_possible_figures or not self.interruption_possible_figures.get(self.interruption_focus_total):
            self.interruption_focus_total=next((total for total,figures in self.interruption_possible_figures.items() if figures),None)
        self._refresh_interruption_figure_list()
        self._update_sign_distance_base()

    def _refresh_interruption_figure_list(self):
        if not hasattr(self,'interruption_figure_layout'):return
        while self.interruption_figure_layout.count():
            item=self.interruption_figure_layout.takeAt(0)
            widget=item.widget()
            if widget is not None:widget.deleteLater()
        self.interruption_figure_buttons={}
        focus=self.interruption_focus_total
        figures=sorted({(total,figure) for total in (focus,) if total is not None
                        for figure in (self.interruption_possible_figures.get(total,set())|
                                       {saved for candidate,saved in self.interruption_selected_figures if candidate==total})},
                       key=lambda item:(item[0],tuple(-int(part) for part in item[1].split('-')) if item[1] else ()))
        if not figures:
            self.interruption_figure_host.setToolTip('No hay figuras alcanzables con el total y la base actuales.')
        for total,figure in figures:
            square=SelectionSquare(f'Figura {figure or "sin cambios"} para {total} interrupciones',size=12)
            square.setChecked((total,figure) in self.interruption_selected_figures)
            reachable=figure in self.interruption_possible_figures.get(total,set())
            square.setEnabled(reachable or (total,figure) in self.interruption_selected_figures)
            if not reachable:square.setToolTip('Figura conservada, pero no alcanzable con la base actual.')
            square.toggled.connect(lambda checked,key=(total,figure):self._interruption_figure_toggled(key,checked))
            label=QLabel(figure or '∅')
            label.setStyleSheet('background:#2c73c9;color:#ffffff;font-size:10px;' if (total,figure) in self.interruption_selected_figures else 'background:#ffffff;color:#173b75;font-size:10px;')
            row=QWidget();row_layout=QHBoxLayout(row);row_layout.setContentsMargins(1,0,1,0);row_layout.setSpacing(3)
            row_layout.addWidget(square);row_layout.addWidget(label);row_layout.addStretch(1)
            square.toggled.connect(lambda checked,item=label:item.setStyleSheet('background:#2c73c9;color:#ffffff;font-size:10px;' if checked else 'background:#ffffff;color:#173b75;font-size:10px;'))
            self.interruption_figure_layout.addWidget(row);self.interruption_figure_buttons[(total,figure)]=square
        self.interruption_figure_layout.addStretch(1)

    def _interruption_matrix_changed(self):
        self.interruption_selected_pairs=self.interruption_matrix.selected_pairs()
        self._interruption_manual_edited()

    def _interruption_total_toggled(self,total,checked):
        if checked:self.interruption_selected_totals.add(total)
        else:self.interruption_selected_totals.discard(total)
        if checked:self.interruption_focus_total=total
        if self.configuring_filters:return
        self._refresh_interruption_figure_list();self._interruption_manual_edited()

    def _focus_interruption_total(self,total):
        self.interruption_focus_total=total
        self._refresh_interruption_figure_list()

    def _interruption_figure_toggled(self,key,checked):
        if checked:
            self.interruption_selected_figures.add(key)
            if key[0] not in self.interruption_selected_totals:
                self.interruption_total_buttons[key[0]].setChecked(True)
        else:self.interruption_selected_figures.discard(key)
        self._interruption_manual_edited()

    def _interruption_manual_edited(self):
        if self.configuring_filters:return
        self.interruption_generation_metadata={};self.manual_filters_changed()

    def _mark_all_interruption_pairs(self):
        pairs={(total,maximum) for total,maximum,_figure in self.interruption_possible_profiles}
        self.interruption_matrix.set_selected_pairs(pairs);self.interruption_selected_pairs=pairs;self._interruption_manual_edited()

    def _reset_interruption_matrix(self):
        self.interruption_matrix.set_selected_pairs(set());self.interruption_selected_pairs.clear()
        self.interruption_apply.setChecked(False);self._interruption_manual_edited()

    def _mark_all_interruption_figures(self):
        self.configuring_filters=True
        try:
            usable_totals={total for total,figures in self.interruption_possible_figures.items() if figures}
            for total in usable_totals:
                self.interruption_selected_totals.add(total);self.interruption_total_buttons[total].setChecked(True)
            self.interruption_selected_figures={(total,figure) for total,figures in self.interruption_possible_figures.items() for figure in figures}
            self._refresh_interruption_figure_list()
            for button in self.interruption_figure_buttons.values():button.setChecked(True)
        finally:self.configuring_filters=False
        self._interruption_manual_edited()

    def _reset_interruption_figures(self):
        self.configuring_filters=True
        try:
            self.interruption_selected_totals.clear();self.interruption_selected_figures.clear()
            for button in self.interruption_total_buttons.values():button.setChecked(False)
            self._refresh_interruption_figure_list();self.distance_apply.setChecked(False)
        finally:self.configuring_filters=False
        self._interruption_manual_edited()

    def _install_interruption_recommendation(self,pairs,figures,*,method,risk,seed=None,seasons=(),sample_size=0,coverage=1.0):
        self.configuring_filters=True
        try:
            self.interruption_matrix.set_selected_pairs(pairs);self.interruption_selected_pairs=set(pairs)
            self.interruption_selected_totals={total for total,_figure in figures}
            self.interruption_selected_figures=set(figures)
            for total,button in self.interruption_total_buttons.items():button.setChecked(total in self.interruption_selected_totals)
            self.interruption_apply.setChecked(bool(pairs));self.distance_apply.setChecked(bool(figures))
            self._refresh_interruption_figure_list()
            for pair,button in self.interruption_figure_buttons.items():button.setChecked(pair in self.interruption_selected_figures)
        finally:self.configuring_filters=False
        self.interruption_generation_metadata={'method':method,'risk':risk,'seed':seed,'seasons':tuple(sorted(seasons)),
            'sample_size':int(sample_size),'coverage':float(coverage),'source':'histórico integrado' if method=='automática' else 'muestra de la base'}
        self.manual_filters_changed()

    def _calculate_random_interruption_mode(self,risk,seed,summary):
        from quiniela_ai_studio.domain.interruption_statistics import (
            random_interruption_recommendation,
        )
        level,label=self._risk_value(risk);coverage={0:1.0,1:.70,2:.40}[level]
        pairs,figures=random_interruption_recommendation(self._streak_base(),seed.value(),coverage)
        self._install_interruption_recommendation(pairs,figures,method='azar',risk=label,seed=seed.value(),
            sample_size=len(self.interruption_possible_profiles),coverage=coverage)
        summary.setText(f'{len(pairs)} pares total/racha · {len(figures)} figuras · semilla {seed.value()} · riesgo {label}. Método original provisional.')

    def _calculate_automatic_interruption_mode(self,risk,summary):
        from quiniela_ai_studio.domain.interruption_statistics import (
            historical_interruption_recommendation,
        )
        seasons={season for season,square in self.history_season_squares.get('Interrupciones',{}).items() if square.isChecked()}
        columns=[row['results14'] for row in self.historical_reduction_results
                 if row.get('season') in seasons and row.get('results14')]
        if not columns:raise ValueError('Selecciona temporadas con resultados finales disponibles.')
        level,label=self._risk_value(risk);coverage={0:.90,1:.70,2:.50}[level]
        pairs,figures,sample_size,matched=historical_interruption_recommendation(columns,self._streak_base(),coverage)
        self._install_interruption_recommendation(pairs,figures,method='automática',risk=label,
            seasons=seasons,sample_size=sample_size,coverage=coverage)
        summary.setText(f'{matched}/{sample_size} resultados finales compatibles con los perfiles elegidos · {len(seasons)} temporadas · riesgo {label} ({coverage:.0%} muestral). Descriptivo, no predictivo.')

    def _build_interruption_rules(self):
        """Persist the two independent subfilters in outer tab 18."""
        from quiniela_ai_studio.domain.reduction_rules import ReductionRule
        meta=self.interruption_generation_metadata;common={
            'generation_method':meta.get('method','manual'),'generation_seed':meta.get('seed'),
            'generation_risk':meta.get('risk',''),'evidence_source':meta.get('source',''),
            'evidence_seasons':tuple(meta.get('seasons',())),'evidence_sample_size':int(meta.get('sample_size',0)),
            'evidence_coverage':float(meta.get('coverage',0)),'tab_index':18,
        }
        rules=[]
        if self.interruption_apply.isChecked() and not self.interruption_selected_pairs:
            raise ValueError('Selecciona al menos una celda de la matriz de Interrupciones.')
        if self.interruption_apply.isChecked() and self.interruption_selected_pairs-self.interruption_matrix._reachable:
            raise ValueError('La base actual ya no alcanza alguna celda seleccionada de Interrupciones.')
        if self.interruption_selected_pairs:
            rules.append(ReductionRule('interruption-total-run-pairs','allowed_interruption_profile',0,1,
                profile_kind='interruptions',allowed_profiles=tuple(sorted(self.interruption_selected_pairs)),
                active=self.interruption_apply.isChecked(),**common))
        if self.interruption_selected_totals:
            # Disabled marker preserves the independent total-selection UI state.
            rules.append(ReductionRule('interruption-distance-totals','allowed_interruption_total',0,13,
                allowed_values=tuple(sorted(self.interruption_selected_totals)),active=False,**common))
        if self.distance_apply.isChecked() and not self.interruption_selected_figures:
            raise ValueError('Selecciona al menos una figura en Distancias o desactiva su aplicación.')
        if self.distance_apply.isChecked():
            impossible={pair for pair in self.interruption_selected_figures
                        if pair[1] not in self.interruption_possible_figures.get(pair[0],set())}
            if impossible:raise ValueError('La base actual ya no alcanza alguna figura seleccionada en Distancias.')
        for total in sorted(self.interruption_selected_totals):
            selected=tuple(sorted((figure for value,figure in self.interruption_selected_figures if value==total),
                key=lambda figure:tuple(-int(part) for part in figure.split('-')) if figure else ()))
            if selected or not self.distance_apply.isChecked():
                rules.append(ReductionRule(f'interruption-figure-{total}','allowed_interruption_figure',0,1,
                    run_length=total,allowed_figures=selected,active=self.distance_apply.isChecked() and bool(selected),**common))
        for sign in ('1','X','2','V'):
            values=self.sign_distance_values[sign]
            if self.sign_distance_apply[sign].isChecked() and not values:
                raise ValueError(f'Selecciona una distancia de {sign} o desactiva Aplicar.')
            if self.sign_distance_apply[sign].isChecked() and values-self.sign_distance_possible[sign]:
                raise ValueError(f'La base actual no alcanza alguna distancia seleccionada de {sign}.')
            if values:
                rules.append(ReductionRule(f'sign-distance-{sign}','allowed_sign_distance',0,13,
                    sign=sign,allowed_values=tuple(sorted(values)),
                    active=self.sign_distance_apply[sign].isChecked(),**common))
        return rules

    def _streak_summary_cards(self,mode):
        host=QWidget();layout=QHBoxLayout(host);layout.setContentsMargins(0,0,0,0);layout.setSpacing(3)
        host.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
        host.setFixedWidth(4*140+3*3)
        self.run_auto_minmax_controls[mode]={}
        for sign in ('1','X','2','V'):
            card=QGroupBox();card.setObjectName('streakSummaryCard');card.setFixedSize(140,120)
            card_layout=QHBoxLayout(card);card_layout.setContentsMargins(4,5,4,4);card_layout.setSpacing(2)
            title=QLabel(sign);title.setObjectName('classicSign');title.setFixedWidth(43);emboss_symbol(title)
            bounds=QLabel('Base 0–14');bounds.setAlignment(Qt.AlignmentFlag.AlignCenter);bounds.setStyleSheet('font-size:8px;color:#35d9f4;background:transparent;')
            fields=QVBoxLayout();fields.setContentsMargins(0,0,0,0);fields.setSpacing(2);fields.addWidget(bounds)
            editors=[]
            for label in ('Mín.','Máx.'):
                editor=QLineEdit();editor.setValidator(QIntValidator(0,14,editor));editor.setMaxLength(2);editor.setFixedSize(31,19);editor.setPlaceholderText('—')
                editor.setAccessibleName(f'{mode}, signo {sign}, {label}')
                editor.editingFinished.connect(lambda s=sign,m=mode:self._streak_range_edited(s,m))
                row=QHBoxLayout();row.setSpacing(2);row.addWidget(QLabel(label));row.addWidget(editor)
                fields.addLayout(row);editors.append(editor)
            card_layout.addWidget(title);card_layout.addLayout(fields)
            self.run_minmax_widgets[sign][mode]=tuple(editors)
            self.run_auto_minmax_controls[mode][sign]=(tuple(editors),bounds)
            layout.addWidget(card)
        return host

    @staticmethod
    def _make_streak_risk_group(parent,name):
        group=QButtonGroup(parent);group.setObjectName(name)
        for index,label in enumerate(('Mínimo','Medio','Máximo')):
            radio=QRadioButton(label);radio.setProperty('riskLevel',index);group.addButton(radio,index)
        return group

    @staticmethod
    def _risk_group_box(title,group):
        box=QGroupBox(title);layout=QVBoxLayout(box);layout.setContentsMargins(4,3,4,3);layout.setSpacing(0)
        for radio in group.buttons():layout.addWidget(radio)
        return box

    @staticmethod
    def _risk_value(control):
        if isinstance(control,QButtonGroup):
            button=control.checkedButton()
            if button is None:raise ValueError('Selecciona un nivel de riesgo.')
            return int(control.id(button)),button.text()
        return control.currentData(),control.currentText()

    @staticmethod
    def _set_risk_value(control,label):
        if isinstance(control,QButtonGroup):
            for button in control.buttons():button.setChecked(button.text()==label)
        else:control.setCurrentText(label)

    def _streak_base(self):
        if self.system:
            try:return self.service.origin_bets(self.system)[0].base
            except ValueError:return self.system.base
        return ('1X2',)*14

    def _sync_streak_minmax_fields(self,sign):
        values=self.run_minmax_values[sign]
        for editors in self.run_minmax_widgets.get(sign,{}).values():
            for key,editor in zip(('minimum','maximum'),editors,strict=True):
                editor.blockSignals(True);editor.setText('' if values[key] is None else str(values[key]));editor.blockSignals(False)

    def _streak_range_edited(self,sign,mode='Manual'):
        """Read one mode's optional bounds into the shared per-sign state."""
        if self.configuring_filters:return
        editors=self.run_minmax_widgets.get(sign,{}).get(mode)
        if not editors:return
        raw=[editor.text().strip() for editor in editors]
        if any(value and not value.isdigit() for value in raw):return
        parsed=[int(value) if value else None for value in raw]
        if parsed[0] is not None and parsed[1] is not None and parsed[0]>parsed[1]:
            self._show_streak_problem(f'Para {sign}, el mínimo no puede superar el máximo.')
            return
        base_low,base_high=self.run_possible_bounds.get(sign,(0,14))
        if parsed[0] is not None and parsed[0]>base_high or parsed[1] is not None and parsed[1]<base_low:
            self._show_streak_problem(f'El intervalo de {sign} no es posible en la base actual ({base_low}–{base_high}). Se conserva para que puedas revisarlo.')
            return
        self.run_minmax_values[sign]={'minimum':parsed[0],'maximum':parsed[1]}
        self.run_lengths[sign]=set(range(parsed[0] or 0,(parsed[1] if parsed[1] is not None else 14)+1))
        self.configuring_filters=True
        try:self._sync_streak_minmax_fields(sign)
        finally:self.configuring_filters=False
        self._show_streak_problem('')
        self._manual_mode_edited('Racha')

    def _streak_count_toggled(self,sign,length,count,checked):
        values=self.run_count_values[sign].setdefault(length,set())
        if checked:values.add(count)
        else:values.discard(count)
        if not values:self.run_count_values[sign].pop(length,None)
        self._manual_mode_edited('Racha')

    def _streak_figure_total_toggled(self,sign,total,checked):
        if checked:
            self.run_figure_totals[sign].add(total);self.run_figure_values[sign].setdefault(total,set())
            self.run_figure_focus[sign]=total
        else:
            self.run_figure_totals[sign].discard(total)
            if not self.run_figure_values[sign].get(total):self.run_figure_values[sign].pop(total,None)
        self._refresh_streak_figures(sign)
        self._manual_mode_edited('Racha')

    def _focus_streak_figure_total(self,sign,total):
        self.run_figure_focus[sign]=total
        self._refresh_streak_figures(sign)

    def _streak_figure_toggled(self,sign,total,figure,checked):
        figures=self.run_figure_values[sign].setdefault(total,set())
        if checked:figures.add(figure)
        else:figures.discard(figure)
        if figures:self.run_figure_totals[sign].add(total)
        self._manual_mode_edited('Racha')

    def _refresh_streak_figures(self,sign):
        _host,layout=self.run_figure_host[sign]
        while layout.count():
            item=layout.takeAt(0);widget=item.widget()
            if widget:widget.deleteLater()
        possible=self.run_possible_figures.get(sign,{})
        selected_totals=self.run_figure_totals[sign]
        available_totals=sorted(possible)
        focus=self.run_figure_focus.get(sign)
        if focus not in possible and focus not in selected_totals:
            focus=next(iter(sorted(selected_totals)),None)
            if focus is None and available_totals:
                focus=min(available_totals,key=lambda value:abs(value-7))
            self.run_figure_focus[sign]=focus
        for total in (focus,) if focus is not None else ():
            values=set(possible.get(total,()))|set(self.run_figure_values[sign].get(total,()))
            ordered=sorted(values,key=lambda figure:tuple(-int(part) for part in figure.split('-')) if figure else ())
            for figure in ordered:
                row=QWidget();row_layout=QHBoxLayout(row);row_layout.setContentsMargins(0,0,0,0);row_layout.setSpacing(2)
                display=figure or '— (sin rachas)'
                square=SelectionSquare(f'{sign}, total {total}, figura {display}',size=10)
                selected=figure in self.run_figure_values[sign].get(total,set())
                square.setChecked(selected)
                available=figure in possible.get(total,())
                square.setEnabled(available or selected)
                label=QLabel(display+(' · base cambió' if selected and not available else ''))
                label.setStyleSheet('font-size:9px;color:#a44a25;background:#ffffff;' if selected and not available else 'font-size:9px;color:#173b75;background:#ffffff;')
                square.setToolTip(f'Figura de {sign} con {total} apariciones: rachas máximas, ordenadas de mayor a menor.'+
                                  (' No alcanzable con la base actual; se conserva la selección.' if selected and not available else ''))
                square.toggled.connect(lambda checked,s=sign,n=total,f=figure:self._streak_figure_toggled(s,n,f,checked))
                row_layout.addWidget(square);row_layout.addWidget(label);row_layout.addStretch(1);layout.addWidget(row)
        layout.addStretch(1)

    def _show_streak_problem(self,message):
        if self.run_validation_label is None:return
        self.run_validation_label.setText(message)
        self.run_validation_label.setStyleSheet('font-size:9px;color:#ffcf70;' if message else 'font-size:9px;color:#91c7ee;')

    def _sync_streak_mode_views(self,sign):
        self._sync_streak_minmax_fields(sign)
        low,high=self.run_possible_bounds.get(sign,(0,14))
        for controls in self.run_auto_minmax_controls.values():
            if sign in controls:
                _editors,label=controls[sign];label.setText(f'Base {low}–{high}')
        for (candidate,length,count),button in self.run_count_squares.items():
            if candidate!=sign:continue
            reachable=count in self.run_possible_counts.get((sign,length),set())
            chosen=count in self.run_count_values[sign].get(length,set())
            button.setEnabled(reachable or chosen)
            button.setToolTip(f'{count} rachas máximas exactas de longitud {length}. '+
                              ('Alcanzable en la base actual.' if reachable else 'No alcanzable; la selección guardada se conserva.'))
            button.setChecked(chosen)
        for total,square in self.run_figure_total_squares.get(sign,{}).items():
            reachable=total in self.run_possible_figures.get(sign,{})
            chosen=total in self.run_figure_totals[sign]
            square.setEnabled(reachable or chosen);square.setChecked(chosen)
        self._refresh_streak_figures(sign)

    def initialize_streak_conditions(self):
        """Clear only SSeguidos; a neutral state never changes the base or Cuenta."""
        self.configuring_filters=True
        try:
            for sign in ('1','X','2','V'):
                self.run_minmax_values[sign]={'minimum':None,'maximum':None}
                self.run_lengths[sign].clear();self.run_count_values[sign].clear()
                self.run_figure_values[sign].clear();self.run_figure_totals[sign].clear()
                self.run_apply[sign].setChecked(False);self.run_figure_apply[sign].setChecked(False)
                for buttons in self.run_frequency_controls.get(sign,{}).values():
                    for button in buttons.values():button.setChecked(False)
                self._sync_streak_mode_views(sign)
        finally:self.configuring_filters=False
        self.legacy_streak_rules=[];self.automatic_profile_rules.pop('Racha',None);self.run_generation_metadata={}
        self._show_streak_problem('');self.manual_filters_changed()

    def _install_streak_recommendation(self,columns,profiles,*,method,risk,seed=None,seasons=(),coverage=1.0,total=None):
        """Project selected joint historical/sample profiles into shared controls."""
        from collections import defaultdict

        from quiniela_ai_studio.domain.reduction_rules import ReductionRule
        from quiniela_ai_studio.domain.streak_statistics import (
            run_figure,
            run_lengths,
            streak_profile,
        )

        selected_profiles=set(profiles)
        included=[column for column in columns if streak_profile(column) in selected_profiles]
        if not included:raise ValueError('La propuesta no contiene resultados compatibles para los cuatro signos.')
        indices={sign:index for index,sign in enumerate(('1','X','2','V'))}
        self.configuring_filters=True
        try:
            self.legacy_streak_rules=[];self.automatic_profile_rules.pop('Racha',None)
            self.run_generation_metadata={'method':method,'risk':risk,'seed':seed,
                'seasons':tuple(sorted(seasons)),'sample_size':len(columns),'coverage':coverage,
                'source':'histórico integrado/importado' if method=='automática' else 'muestra reproducible de la base'}
            for sign,index in indices.items():
                longest_values={profile[index] for profile in selected_profiles}
                self.run_minmax_values[sign]={
                    'minimum':min(longest_values) if longest_values else None,
                    'maximum':max(longest_values) if longest_values else None,
                }
                self.run_lengths[sign]=set(range(self.run_minmax_values[sign]['minimum'] or 0,
                    (self.run_minmax_values[sign]['maximum'] if self.run_minmax_values[sign]['maximum'] is not None else 14)+1))
                count_values={}
                offset=4+index*14
                for length in range(2,15):
                    count_values[length]={profile[offset+length-1] for profile in selected_profiles}
                self.run_count_values[sign]=count_values
                figure_values=defaultdict(set)
                for column in included:
                    _longest,counts=run_lengths(column,sign);total_signs=sum(length*count for length,count in enumerate(counts,1))
                    figure_values[total_signs].add(run_figure(column,sign))
                self.run_figure_values[sign]={total:set(values) for total,values in figure_values.items()}
                self.run_figure_totals[sign]=set(figure_values)
                self.run_apply[sign].setChecked(True)
                self.run_figure_apply[sign].setChecked(False)
                for length,buttons in self.run_frequency_controls[sign].items():
                    for count,button in buttons.items():button.setChecked(count in count_values.get(length,set()))
                self._sync_streak_mode_views(sign)
        finally:self.configuring_filters=False
        self.automatic_profile_rules['Racha']=ReductionRule(
            f'{method}-streak-profile','allowed_profile',0,14,profile_kind='streaks',
            allowed_profiles=tuple(sorted(selected_profiles)),generation_method=method,
            generation_seed=seed,generation_risk=risk,
            evidence_source='resultados finales integrados' if method=='automática' else 'muestra reproducible de la base',
            evidence_seasons=tuple(sorted(seasons)),evidence_sample_size=int(total or len(columns)),
            evidence_coverage=coverage,tab_index=1,
        )
        self.random_reduction_metadata.pop('Racha',None)
        self._show_streak_problem('')
        self.manual_filters_changed()
        return len(included)

    def _calculate_random_streak_mode(self,risk,seed,summary):
        """Propose a repeatable filter from random valid completions of the base."""
        import random

        from quiniela_ai_studio.domain.streak_statistics import (
            frequent_profiles,
            streak_profile,
        )

        base=self._streak_base();rng=random.Random(seed.value())
        samples=[''.join(rng.choice(pick) for pick in base) for _ in range(512)]
        level,label=self._risk_value(risk)
        coverage={0:.90,1:.70,2:.40}[level]
        profiles,total=frequent_profiles((streak_profile(column) for column in samples),coverage)
        included=self._install_streak_recommendation(samples,profiles,method='azar',risk=label,
            seed=seed.value(),coverage=coverage,total=total)
        rules=[rule for rule in self.build_reduction_rules() if rule.tab_index==1 and rule.active]
        admitted=sum(all(rule.accepts(column) for rule in rules) for column in samples)
        summary.setText(f'Semilla {seed.value()} · {admitted}/512 escenarios de la base admitidos; muestra aleatoria reproducible, no recuento exacto del universo. Riesgo {label} ({coverage:.0%} objetivo muestral).')
        self.statusBar().showMessage(f'Azar SSeguidos: {included} perfiles conjuntos muestreados; semilla {seed.value()}.',10000)

    def _calculate_automatic_streak_mode(self,risk,summary):
        """Recommend from selected real final-result seasons, preserving joint profiles."""
        from quiniela_ai_studio.domain.streak_statistics import (
            frequent_profiles,
            streak_profile,
        )

        seasons={season for season,square in self.history_season_squares.get('Racha',{}).items() if square.isChecked()}
        columns=[row['results14'] for row in self.historical_reduction_results if row.get('season') in seasons]
        if not columns:raise ValueError('Selecciona al menos una temporada con resultados finales del histórico integrado.')
        level,label=self._risk_value(risk);coverage={0:1.0,1:.75,2:.50}[level]
        profiles,total=frequent_profiles((streak_profile(column) for column in columns),coverage)
        included=self._install_streak_recommendation(columns,profiles,method='automática',risk=label,
            seasons=seasons,coverage=coverage,total=total)
        summary.setText(f'{total:,} resultados finales · {len(profiles)} perfiles conjuntos admitidos · {included:,} filas dentro del objetivo {coverage:.0%}. Las proyecciones por signo proceden de los mismos perfiles; no son una predicción.'.replace(',','.'))
        self.statusBar().showMessage(f'Automática SSeguidos: {len(profiles)} perfiles conjuntos de {len(seasons)} temporadas.',10000)

    def _manual_mode_edited(self,title):
        if self.configuring_filters:return
        self.automatic_profile_rules.pop(title,None)
        self.random_reduction_metadata.pop(title,None)
        if title=='Racha':
            self.legacy_streak_rules=[]
            self.run_generation_metadata={}
        self.manual_filters_changed()

    def import_reduction_history(self):
        """Import final match results; synthetic demo fixtures are rejected."""
        path,_=QFileDialog.getOpenFileName(self,'Importar resultados históricos','','CSV (*.csv);;JSON (*.json)')
        if not path:return
        file=Path(path)
        if file.suffix.lower()=='.json':
            payload=json.loads(file.read_text(encoding='utf-8'))
            if isinstance(payload,dict) and payload.get('demo') is True:
                raise ValueError('No se importan datos sintéticos de demostración como historial real.')
            records=payload if isinstance(payload,list) else payload.get('results',[]) if isinstance(payload,dict) else []
        else:
            import csv
            with file.open(encoding='utf-8-sig',newline='') as stream:records=list(csv.DictReader(stream))
        if not isinstance(records,list) or any(not isinstance(row,dict) for row in records):
            raise ValueError('El fichero debe contener una lista de filas con temporada, jornada y results14.')
        cleaned=[];updated=0
        from quiniela_ai_studio.domain.streak_statistics import validate_result_column
        existing={(str(item.get('season')),str(item.get('round'))):index for index,item in enumerate(self.historical_reduction_results)}
        for row in records:
            if row.get('demo') is True or row.get('results_status')=='synthetic_final':
                raise ValueError('No se importan resultados sintéticos de demostración como historial real.')
            season=str(row.get('season','')).strip();number=str(row.get('round',row.get('jornada',''))).strip()
            result=str(row.get('results14',row.get('result',row.get('results','')))).strip().upper()
            validate_result_column(result)
            if not season or not number:raise ValueError('Cada fila necesita temporada, jornada y results14.')
            key=(season,number)
            entry={'season':season,'round':number,'results14':result,'source':file.name}
            for index in range(1,16):
                score=str(row.get(f'score_{index:02}','')).strip()
                if score and not re.fullmatch(r'\d{1,2}-\d{1,2}',score):
                    raise ValueError(f'Marcador inválido en partido {index} de {season} / {number}.')
                entry[f'score_{index:02}']=score
            for index in range(1,15):
                score=entry[f'score_{index:02}']
                if score:
                    home,away=map(int,score.split('-'))
                    sign='1' if home>away else '2' if home<away else 'X'
                    if result[index-1]!=sign:
                        raise ValueError(f'El marcador {score} del partido {index} contradice el signo de {season} / {number}.')
            if key in existing:
                target_index=existing[key]
                target=(self.historical_reduction_results[target_index] if target_index<len(self.historical_reduction_results)
                        else cleaned[target_index-len(self.historical_reduction_results)])
                if target.get('results14')!=result:raise ValueError(f'Los signos de {season} / {number} no coinciden con el histórico ya incluido.')
                additions={field:value for field,value in entry.items() if value not in ('',None) and (field not in target or not target.get(field))}
                if additions:target.update(additions);updated+=1
            else:
                existing[key]=len(self.historical_reduction_results)+len(cleaned);cleaned.append(entry)
        if not cleaned and not updated:raise ValueError('El fichero no contiene resultados nuevos ni marcadores adicionales.')
        self.historical_reduction_results.extend(cleaned)
        self.repository.set_setting('reduction_historical_results',self.historical_reduction_results)
        self.refresh_history_seasons()
        self.statusBar().showMessage(f'Se añadieron {len(cleaned)} jornadas y se completaron {updated} registros existentes.',10000)

    def refresh_history_seasons(self):
        seasons=sorted({str(row.get('season','')) for row in self.historical_reduction_results if row.get('season')})
        for title,buttons in self.history_season_squares.items():
            selected={season:button.isChecked() for season,button in buttons.items()}
            self._populate_history_seasons(title,seasons,{season:selected.get(season,True) for season in seasons})
            scored=sum(bool(row.get('score_01')) for row in self.historical_reduction_results)
            self.history_season_summaries[title].setText(f'{len(seasons)} temp. · {len(self.historical_reduction_results):,} jornadas · {scored} con marcador'.replace(',','.'))
            _risk,_summary,calculate=self.mode_automatic_controls[title]
            calculate.setEnabled(bool(seasons))

    def _populate_history_seasons(self,title,seasons,selected):
        """Build a compact, row-major season grid with accessible green squares."""
        grid=self.history_season_grids[title]
        while grid.count():
            item=grid.takeAt(0)
            widget=item.widget()
            if widget is not None:widget.deleteLater()
        buttons={}
        ordered=sorted(seasons,reverse=True)
        columns=2 if title in ('Racha','FSSeguidos','Interrupciones') else 2
        if not ordered:
            empty=QLabel('No hay temporadas disponibles en el histórico integrado.')
            grid.addWidget(empty,0,0,1,columns)
        else:
            for index,season in enumerate(ordered):
                square=SelectionSquare(f'Incluir temporada {season}',size=13)
                square.setChecked(bool(selected.get(season,True)))
                square.toggled.connect(lambda _checked,t=title:self._history_season_toggled(t))
                label=QLabel(season);label.setFixedWidth(68)
                if title in ('Racha','FSSeguidos','Interrupciones'):
                    label.setStyleSheet('color:#173b75;background:#ffffff;font-size:10px;')
                cell=QWidget();cell_layout=QHBoxLayout(cell);cell_layout.setContentsMargins(1,0,1,0);cell_layout.setSpacing(3);cell_layout.addWidget(square);cell_layout.addWidget(label);cell_layout.addStretch(1)
                grid.addWidget(cell,index//columns,index%columns)
                buttons[season]=square
        self.history_season_squares[title]=buttons
        self._refresh_history_statistics(title)
        if title=='Cuenta':
            self._refresh_count_profiles()
            self._refresh_count_season_table()

    def _refresh_history_statistics(self,title=None):
        """Show exact historical frequencies in the miniature classic grid."""
        from collections import Counter

        from quiniela_ai_studio.domain.streak_statistics import (
            count_profile,
            run_lengths,
        )
        targets=(title,) if title else ('Cuenta','Racha')
        for target in targets:
            if target not in ('Cuenta','Racha'):
                continue
            selected={season for season,square in self.history_season_squares.get(target,{}).items() if square.isChecked()}
            rows=[row for row in self.historical_reduction_results if row.get('season') in selected]
            if target=='Cuenta':
                profiles=[count_profile(row['results14']) for row in rows]
                counters={sign:Counter(profile[index] for profile in profiles) for index,sign in enumerate(('V','X','2'))}
                for (sign,value),label in self.count_frequency_labels.items():
                    frequency=counters[sign][value]
                    label.setText(f'{frequency/1000:.1f}k' if frequency>=1000 else str(frequency) if profiles else '—')
                    label.setToolTip(f'{frequency} de {len(profiles)} jornadas ({100*frequency/len(profiles):.1f}%)' if profiles else 'No hay jornadas para las temporadas elegidas.')
                continue
            frequencies={key:Counter() for key in self.run_frequency_labels}
            for row in rows:
                for sign in ('1','X','2','V'):
                    _longest,counts=run_lengths(row['results14'],sign)
                    for length in range(2,15):frequencies[(sign,length,counts[length-1])][counts[length-1]]+=1
            for (sign,length,count),label in self.run_frequency_labels.items():
                frequency=frequencies[(sign,length,count)][count]
                label.setText(f'{frequency/1000:.1f}k' if frequency>=1000 else str(frequency) if rows else '—')
                label.setToolTip(f'{frequency} de {len(rows)} jornadas con exactamente {count} rachas máximas de longitud {length}.' if rows else 'No hay jornadas para las temporadas elegidas.')

    def _set_history_seasons(self,title,checked):
        for square in self.history_season_squares.get(title,{}).values():square.setChecked(checked)

    def _history_season_toggled(self,title):
        self._refresh_history_statistics(title)
        if title=='Cuenta':
            self._refresh_count_profiles()
            self._sync_count_season_table_checks()
        if title in ('Racha','FSSeguidos','Interrupciones'):
            current_round_key=self.round_picker.currentData()
            if title=='Interrupciones':key=self._interruption_season_setting_key()
            else:
                prefix='sseguidos' if title=='Racha' else 'fsseguidos'
                key=f'{prefix}_seasons:{current_round_key}' if current_round_key else f'{prefix}_seasons'
            self.repository.set_setting(key,[season for season,square in self.history_season_squares[title].items() if square.isChecked()])

    def calculate_automatic_mode(self,title,signs,values,buttons,risk,summary):
        if title=='Racha':
            self._calculate_automatic_streak_mode(risk,summary)
            return
        from quiniela_ai_studio.domain.reduction_rules import ReductionRule
        from quiniela_ai_studio.domain.streak_statistics import (
            count_profile,
            frequent_profiles,
            streak_profile,
        )
        selected_seasons={season for season,square in self.history_season_squares.get(title,{}).items() if square.isChecked()}
        columns=[row['results14'] for row in self.historical_reduction_results if row.get('season') in selected_seasons]
        if not columns:raise ValueError('Importa y selecciona al menos una temporada de resultados finales.')
        coverage={0:1.0,1:.9,2:.75,3:.5}[risk.currentData()]
        profiles,total=frequent_profiles((count_profile(column) if title=='Cuenta' else streak_profile(column) for column in columns),coverage)
        kind='counts' if title=='Cuenta' else 'streaks'
        self.automatic_profile_rules[title]=ReductionRule(f'automatic-{kind}-profile','allowed_profile',0,14,
            profile_kind=kind,allowed_profiles=profiles,generation_method='automática',
            generation_risk=risk.currentText(),evidence_source='resultados finales importados',
            evidence_seasons=tuple(sorted(selected_seasons)),evidence_sample_size=total,evidence_coverage=coverage)
        self.random_reduction_metadata.pop(title,None)
        if title=='Cuenta':
            self.count_profiles_selected=set(profiles)
            self.configuring_filters=True
            self.count_profile_active=True
            for button in self.count_profile_apply_buttons:
                button.blockSignals(True);button.setChecked(True);button.blockSignals(False)
            self.configuring_filters=False
            self._refresh_count_profiles()
        projections=({sign:set() for sign in signs})
        for profile in profiles:
            if title=='Cuenta':
                variants,x_count,two_count=profile
                projections['V'].add(variants);projections['X'].add(x_count);projections['2'].add(two_count)
            else:
                for index,sign in enumerate(signs):projections[sign].add(profile[index])
        self.configuring_filters=True
        for sign in signs:values[sign]=projections[sign]
        for (sign,value),button in buttons.items():button.setChecked(value in values[sign])
        applications=self.count_apply if title=='Cuenta' else self.run_apply
        for sign in signs:applications[sign].setChecked(True)
        self.configuring_filters=False
        summary.setText(f'{total} resultados finales · {len(profiles)} perfiles conjuntos admitidos · cobertura descriptiva objetivo {coverage:.0%} de la muestra. No es una predicción.')
        self.manual_filters_changed()

    def _mode_square_toggled(self,values,buttons,sign,value,checked):
        if checked:values[sign].add(value)
        else:values[sign].discard(value)
        was_configuring=self.configuring_filters
        self.configuring_filters=True
        for (other_sign,other_value),button in buttons.items():
            button.blockSignals(True);button.setChecked(other_value in values[other_sign]);button.blockSignals(False)
        self.configuring_filters=was_configuring
        if not was_configuring:self._manual_mode_edited('Cuenta' if values is self.count_values else 'Racha')

    def update_streak_base_limits(self):
        """Recompute feasible run lengths, exact frequencies and figures."""
        if not self.run_minmax_controls:return
        from quiniela_ai_studio.domain.streak_statistics import (
            possible_run_figures,
            possible_run_frequency_counts,
            possible_run_length_bounds,
        )
        base=self._streak_base();issues=[]
        was_configuring=self.configuring_filters;self.configuring_filters=True
        try:
            for sign in ('1','X','2','V'):
                self.run_possible_bounds[sign]=possible_run_length_bounds(base,sign)
                low,high=self.run_possible_bounds[sign]
                self.run_possible_figures[sign]=possible_run_figures(base,sign)
                for length in range(2,15):
                    possible=set(possible_run_frequency_counts(base,sign,length))
                    self.run_possible_counts[(sign,length)]=possible
                    for count,button in self.run_frequency_controls[sign][length].items():
                        selected=count in self.run_count_values[sign].get(length,set())
                        button.setEnabled(count in possible or selected)
                        button.setVisible(count in possible or selected)
                        button.setToolTip(f'{count} rachas máximas exactas de longitud {length} para {sign}.'+
                            (' Alcanzable con la base actual.' if count in possible else ' No alcanzable; se conserva si ya estaba marcado.'))
                self.run_minmax_labels[sign][0].setText(f'Base {low}–{high}')
                for total,square in self.run_figure_total_squares[sign].items():
                    possible=total in self.run_possible_figures[sign];selected=total in self.run_figure_totals[sign]
                    square.setEnabled(possible or selected)
                    square.setToolTip(f'Total {total} de {sign}.'+(' Alcanzable en esta base.' if possible else ' No alcanzable; se conserva si ya estaba marcado.'))
                minimum=self.run_minmax_values[sign]['minimum'];maximum=self.run_minmax_values[sign]['maximum']
                if minimum is not None and minimum>high or maximum is not None and maximum<low:
                    issues.append(f'rango {sign} {minimum if minimum is not None else "—"}–{maximum if maximum is not None else "—"}')
                for length,counts in self.run_count_values[sign].items():
                    if counts-self.run_possible_counts[(sign,length)]:issues.append(f'«Veces» {sign}, longitud {length}')
                for total,figures in self.run_figure_values[sign].items():
                    if figures-set(self.run_possible_figures[sign].get(total,())):issues.append(f'figuras {sign}, total {total}')
                self._sync_streak_mode_views(sign)
        finally:self.configuring_filters=was_configuring
        if issues:self._show_streak_problem('La base actual hace incompatibles selecciones guardadas: '+', '.join(issues)+'. Se conservan; revísalas antes de generar.')
        else:self._show_streak_problem('')
        if hasattr(self,'fss_figure_lists'):
            for sign in ('1','X','2','V'):self._refresh_fss_figure_list(sign)
        self._update_interruption_base()

    def _set_mode_values(self, values, buttons, selected, applications):
        was_configuring=self.configuring_filters
        self.configuring_filters=True
        for sign in values:
            values[sign]=set(selected.get(sign,()))
            if sign in applications:applications[sign].setChecked(bool(values[sign]))
        for (sign,value),button in buttons.items():button.setChecked(value in values[sign])
        self.configuring_filters=was_configuring

    def calculate_random_mode(self,title,signs,values,buttons,risk,seed,summary):
        """Choose reproducible observed counts/lengths without made-up rates."""
        if not self.system:
            raise ValueError('Abre una quiniela con apuestas generadas antes de calcular el modo Azar.')
        import random
        candidates=self.service.origin_bets(self.system)[1]
        if not candidates:raise ValueError('Genera o importa apuestas antes de calcular el modo Azar.')
        rng=random.Random(seed.value());observed={sign:set() for sign in signs}
        self.automatic_profile_rules.pop(title,None)
        if title=='Cuenta':
            self.count_profiles_selected.clear();self.count_profile_active=False
            for button in self.count_profile_apply_buttons:
                button.blockSignals(True);button.setChecked(False);button.blockSignals(False)
            self._refresh_count_profiles()
        self.random_reduction_metadata[title]={'method':'azar','seed':seed.value(),'risk':risk.currentText()}
        from quiniela_ai_studio.domain.reduction_rules import ReductionRule
        kinds=('count_sign' if title=='Cuenta' else 'longest_run')
        for sign in signs:
            observed[sign]={int(ReductionRule('sample',kinds,0,14,sign=sign).measure(bet.column)) for bet in candidates}
        fraction={0:.8,1:.6,2:.4,3:.25}[risk.currentData()]
        choices={sign:set(rng.sample(sorted(observed[sign]),max(1,min(len(observed[sign]),round(len(observed[sign])*fraction))))) for sign in signs}
        # Keep one joint condition set that admits at least one actual candidate.
        def admitted():
            return sum(all(int(ReductionRule('sample',kinds,0,14,sign=s).measure(b.column)) in choices[s] for s in signs) for b in candidates)
        while not admitted() and any(len(choices[s])<len(observed[s]) for s in signs):
            sign=max(signs,key=lambda item:len(observed[item])-len(choices[item]))
            remaining=sorted(observed[sign]-choices[sign])
            if not remaining:break
            choices[sign].add(rng.choice(remaining))
        self.configuring_filters=True
        for sign in signs:values[sign]=set(choices[sign])
        for (sign,value),button in buttons.items():button.setChecked(value in values[sign])
        applications=self.count_apply if title=='Cuenta' else self.run_apply
        for sign in signs:applications[sign].setChecked(True)
        self.configuring_filters=False
        kept=admitted()
        summary.setText(f'Semilla {seed.value()} · {kept:,} de {len(candidates):,} apuestas de origen admitidas. Riesgo «{risk.currentText()}».')
        self.manual_filters_changed()

    def reduction_tab_toggled(self,index,checked):
        self.reduction_active[index]=bool(checked)
        if self.system:
            self.repository.set_setting(f'reduction_tabs_configured:{self.system.system_id}',True)
        self.manual_filters_changed()

    def _build_pattern_tabs(self):
        """Pair/triple/quartet/quintet use the same window-count semantics."""
        self.pattern_controls={}
        for size,tab in enumerate(range(4,8),2):
            page=self.reduction_tab_layouts[tab]
            group=QGroupBox(f'Patrón de {size} partidos consecutivos')
            grid=QGridLayout(group)
            enabled=QCheckBox('Usar este patrón')
            pattern=SignMatrixWidget(size)
            minimum=QSpinBox();minimum.setRange(0,14);maximum=QSpinBox();maximum.setRange(0,14);maximum.setValue(14)
            grid.addWidget(enabled,0,0,1,4);grid.addWidget(pattern,1,0,1,4)
            grid.addWidget(QLabel('Apariciones desde'),2,0);grid.addWidget(minimum,2,1);grid.addWidget(QLabel('hasta'),2,2);grid.addWidget(maximum,2,3)
            page.addWidget(group)
            note=QLabel('Marca un signo por fila. Se cuentan las apariciones consecutivas solapadas. Regla original de Quiniela AI Studio.')
            note.setWordWrap(True);page.addWidget(note);page.addStretch()
            self.pattern_controls[size]=(enabled,pattern,minimum,maximum)

    def _build_reference_tabs(self):
        page=self.reduction_tab_layouts[3]
        box=QGroupBox('Repeticiones respecto a una columna de referencia');grid=QGridLayout(box)
        self.repeat_enabled=QCheckBox('Usar esta referencia')
        self.repeat_reference=SignMatrixWidget(14)
        self.repeat_minimum=QSpinBox();self.repeat_minimum.setRange(0,14);self.repeat_maximum=QSpinBox();self.repeat_maximum.setRange(0,14);self.repeat_maximum.setValue(14)
        grid.addWidget(self.repeat_enabled,0,0,1,5);grid.addWidget(self.repeat_reference,1,0,1,5);grid.addWidget(QLabel('Coincidencias desde'),2,0);grid.addWidget(self.repeat_minimum,2,1);grid.addWidget(QLabel('hasta'),2,2);grid.addWidget(self.repeat_maximum,2,3);page.addWidget(box)
        page.addWidget(QLabel('Marca una casilla 1/X/2 por partido. No se consultan resultados históricos sin que elijas una referencia.'))
        page.addStretch()
        page=self.reduction_tab_layouts[11]
        box=QGroupBox('Cuántas columnas de referencia deben quedar dentro del rango de aciertos')
        grid=QGridLayout(box);self.frequency_matrix=SignMatrixWidget(14)
        self.frequency_reference_list=QListWidget();self.frequency_reference_list.setMaximumHeight(100)
        add_reference=QPushButton('Añadir columna marcada');remove_reference=QPushButton('Quitar seleccionada')
        self.frequency_hits_min=QSpinBox();self.frequency_hits_min.setRange(0,14);self.frequency_hits_max=QSpinBox();self.frequency_hits_max.setRange(0,14);self.frequency_hits_max.setValue(14)
        self.frequency_count_min=QSpinBox();self.frequency_count_min.setRange(0,80);self.frequency_count_max=QSpinBox();self.frequency_count_max.setRange(0,80);self.frequency_count_max.setValue(80)
        grid.addWidget(self.frequency_matrix,0,0,1,6);grid.addWidget(add_reference,1,0,1,3);grid.addWidget(remove_reference,1,3,1,3);grid.addWidget(self.frequency_reference_list,2,0,1,6)
        grid.addWidget(QLabel('Aciertos por referencia: desde / hasta'),3,0);grid.addWidget(self.frequency_hits_min,3,1);grid.addWidget(self.frequency_hits_max,3,2)
        grid.addWidget(QLabel('N.º referencias en rango: desde / hasta'),4,0);grid.addWidget(self.frequency_count_min,4,1);grid.addWidget(self.frequency_count_max,4,2);page.addWidget(box)
        add_reference.clicked.connect(lambda:self.safe(self.add_frequency_reference));remove_reference.clicked.connect(self.remove_frequency_reference)
        page.addWidget(QLabel('Añade referencias con la matriz 1/X/2. Se cuentan las que caen en el intervalo de aciertos elegido.'))
        page.addStretch()

    def _build_weighted_tab(self):
        page=self.reduction_tab_layouts[12]
        box=QGroupBox('Valoración de la columna con los porcentajes de la fuente elegida')
        grid=QGridLayout(box);self.weight_sum_enabled=QCheckBox('Limitar suma de probabilidades de los signos elegidos')
        self.weight_sum_min=QDoubleSpinBox();self.weight_sum_min.setRange(0,14);self.weight_sum_min.setDecimals(4)
        self.weight_sum_max=QDoubleSpinBox();self.weight_sum_max.setRange(0,14);self.weight_sum_max.setDecimals(4);self.weight_sum_max.setValue(14)
        self.weight_product_enabled=QCheckBox('Limitar logaritmo de la probabilidad conjunta (no es premio esperado)')
        self.weight_product_min=QDoubleSpinBox();self.weight_product_min.setRange(-1000,0);self.weight_product_min.setDecimals(4);self.weight_product_min.setValue(-1000)
        self.weight_product_max=QDoubleSpinBox();self.weight_product_max.setRange(-1000,0);self.weight_product_max.setDecimals(4)
        grid.addWidget(self.weight_sum_enabled,0,0,1,2);grid.addWidget(QLabel('Suma desde'),1,0);grid.addWidget(self.weight_sum_min,1,1);grid.addWidget(QLabel('hasta'),1,2);grid.addWidget(self.weight_sum_max,1,3)
        grid.addWidget(self.weight_product_enabled,2,0,1,4);grid.addWidget(QLabel('Log-probabilidad desde'),3,0);grid.addWidget(self.weight_product_min,3,1);grid.addWidget(QLabel('hasta'),3,2);grid.addWidget(self.weight_product_max,3,3)
        page.addWidget(box);self.weight_status=QLabel('Selecciona una fuente deportiva con porcentajes descargados.')
        self.weight_status.setWordWrap(True);page.addWidget(self.weight_status);page.addStretch()

    def _build_columns_tabs(self):
        page=self.reduction_tab_layouts[13]
        box=QGroupBox('Suma de aciertos máximos de varios grupos');layout=QVBoxLayout(box)
        self.columns_sum_enabled=QCheckBox('Usar este límite de suma')
        layout.addWidget(self.columns_sum_enabled)
        self.columns_group_checks=QGridLayout();layout.addLayout(self.columns_group_checks)
        limits=QHBoxLayout();limits.addWidget(QLabel('Suma mínima'));self.columns_sum_min=QSpinBox();self.columns_sum_min.setRange(0,112);limits.addWidget(self.columns_sum_min)
        limits.addWidget(QLabel('Suma máxima'));self.columns_sum_max=QSpinBox();self.columns_sum_max.setRange(0,112);self.columns_sum_max.setValue(112);limits.addWidget(self.columns_sum_max);layout.addLayout(limits)
        self.columns_sum_enabled.toggled.connect(self.advanced_conditions_changed)
        self.columns_sum_min.valueChanged.connect(self.advanced_conditions_changed);self.columns_sum_max.valueChanged.connect(self.advanced_conditions_changed)
        self.columns_sum_min.valueChanged.connect(self.columns_sum_max.setMinimum);self.columns_sum_max.valueChanged.connect(self.columns_sum_min.setMaximum)
        page.addWidget(box)
        page.addWidget(QLabel('Marca los grupos que quieres sumar. La apuesta pasa si sus aciertos quedan dentro del rango. La diferencia entre dos grupos está en Relacionados.'))
        page.addWidget(QLabel('Para quitar columnas repetidas, añade las otras quinielas en Frecuencias; fija los aciertos en 14 y permite 0 referencias en ese rango. El presupuesto está en Optimizar.'))
        references_button=QPushButton('Elegir columnas para comparar')
        references_button.clicked.connect(lambda:self.reduction_tabs.setCurrentIndex(11));page.addWidget(references_button)
        page.addStretch()
        # Si… entonces has its own distinct rule and controls below.

    def _build_if_then_tab(self):
        page=self.reduction_tab_layouts[14]
        box=QGroupBox('Si se cumple este grupo… exige este resultado en otro')
        grid=QGridLayout(box)
        self.implication_enabled=QCheckBox('Activar condición si… entonces')
        self.implication_from=QComboBox();self.implication_to=QComboBox()
        self.implication_from_min=QSpinBox();self.implication_from_max=QSpinBox()
        self.implication_to_min=QSpinBox();self.implication_to_max=QSpinBox()
        for control in (self.implication_from_min,self.implication_from_max,self.implication_to_min,self.implication_to_max):control.setRange(0,14)
        self.implication_from_max.setValue(14);self.implication_to_max.setValue(14)
        grid.addWidget(self.implication_enabled,0,0,1,5)
        grid.addWidget(QLabel('Si los aciertos de'),1,0);grid.addWidget(self.implication_from,1,1)
        grid.addWidget(self.implication_from_min,1,2);grid.addWidget(QLabel('a'),1,3);grid.addWidget(self.implication_from_max,1,4)
        grid.addWidget(QLabel('entran en este rango, los de'),2,0);grid.addWidget(self.implication_to,2,1)
        grid.addWidget(self.implication_to_min,2,2);grid.addWidget(QLabel('a'),2,3);grid.addWidget(self.implication_to_max,2,4)
        page.addWidget(box)
        note=QLabel('Ejemplo: si el Grupo A acierta entre 2 y 3, exige que el Grupo B acierte entre 1 y 4. Si A queda fuera del rango, esta condición no interviene. Activa primero ambos grupos en la pestaña Grupos.')
        note.setWordWrap(True);page.addWidget(note);page.addStretch()
        for control in (self.implication_enabled,self.implication_from,self.implication_to,
                        self.implication_from_min,self.implication_from_max,self.implication_to_min,self.implication_to_max):
            signal=getattr(control,'toggled',None) or getattr(control,'currentIndexChanged',None) or getattr(control,'valueChanged',None)
            signal.connect(self.advanced_conditions_changed)
        self.implication_from_min.valueChanged.connect(self.implication_from_max.setMinimum)
        self.implication_from_max.valueChanged.connect(self.implication_from_min.setMaximum)
        self.implication_to_min.valueChanged.connect(self.implication_to_max.setMinimum)
        self.implication_to_max.valueChanged.connect(self.implication_to_min.setMaximum)

    def _build_athena_tab(self):
        page=self.reduction_tab_layouts[15]
        page.addWidget(QLabel('La tolerancia de fallos se configura aquí y se comparte con los grupos relacionados. Así una apuesta puede incumplir hasta el número indicado de reglas activas.'))
        self.reduction_tab_layouts[16].addWidget(QLabel('Reduce las candidatas del desarrollo de origen para cubrir el umbral elegido. La verificación independiente informará del universo cubierto; solo una comprobación exhaustiva puede llamarse garantía.'))
        objective=QGroupBox('Atenea · cobertura condicionada');grid=QGridLayout(objective)
        self.athena_hits=QComboBox()
        for hits in (13,12,11,10):self.athena_hits.addItem(f'Al menos {hits} aciertos',hits)
        self.athena_mode=QComboBox();self.athena_mode.addItem('Hermes · rápido','hermes');self.athena_mode.addItem('Atenea · mejora local','athena');self.athena_mode.addItem('Artemisa · exacto acotado','artemisa')
        self.athena_budget=QDoubleSpinBox();self.athena_budget.setRange(0,100000);self.athena_budget.setDecimals(2);self.athena_budget.setValue(10)
        self.athena_hits.setToolTip('Se comprueba cuántos signos de cada resultado posible coinciden con alguna apuesta elegida.')
        self.athena_mode.setToolTip('Hermes: selección rápida. Atenea: mejora cambios entre apuestas. Artemisa: busca el mejor resultado solo si el espacio es pequeño.')
        self.athena_budget.setToolTip('Límite de gasto para esta propuesta. Cada apuesta cuesta el precio de la jornada.')
        grid.addWidget(QLabel('Objetivo de cobertura'),0,0);grid.addWidget(self.athena_hits,0,1);grid.addWidget(QLabel('Búsqueda'),1,0);grid.addWidget(self.athena_mode,1,1);grid.addWidget(QLabel('Presupuesto máximo (€)'),2,0);grid.addWidget(self.athena_budget,2,1)
        page.addWidget(objective)
        self.athena_preview=QLabel('Primero genera o importa apuestas.');self.athena_preview.setWordWrap(True);page.addWidget(self.athena_preview)
        self.athena_run=QPushButton('Calcular y verificar reducción');page.addWidget(self.athena_run)
        self.athena_cancel=QPushButton('Cancelar cálculo');self.athena_cancel.setEnabled(False);page.addWidget(self.athena_cancel)
        self.athena_progress=QProgressBar();self.athena_progress.setRange(0,100);self.athena_progress.setValue(0);page.addWidget(self.athena_progress)
        self.athena_status=QLabel('El resultado se guardará como una quiniela nueva; la actual no se sobrescribe.')
        self.athena_status.setWordWrap(True);page.addWidget(self.athena_status)
        self.athena_run.clicked.connect(lambda:self.safe(self.start_athena_reduction))
        self.athena_cancel.clicked.connect(self.cancel_athena_reduction)
        page.addStretch()

    def start_athena_reduction(self):
        """Run the independent coverage search without blocking the Qt event loop."""
        from quiniela_ai_studio.domain.coverage_reducer import (
            CoverageReductionConfig,
            reduce_coverage,
        )
        if not self.system or not self.system.bets:
            raise ValueError('Genera o importa apuestas y espera a que se actualicen las condiciones.')
        if self.filter_timer.isActive() or self.filter_job is not None:
            raise ValueError('Espera a que termine la actualización de filtros.')
        if self.athena_job is not None:
            raise ValueError('Ya hay un cálculo de cobertura en marcha.')
        current=self.system
        frozen=self.frozen_round()
        cents=int(self.athena_budget.value()*100)
        config=CoverageReductionConfig(self.athena_hits.currentData(),cents,frozen.price_cents,
                                       method=self.athena_mode.currentData(),
                                       scenario_limit=20_000,candidate_limit=500,max_seconds=30)
        candidates=tuple(current.bets)
        snapshot=frozen.snapshot('sport')
        self.athena_run.setEnabled(False);self.athena_cancel.setEnabled(True)
        self.athena_progress.setValue(0);self.athena_status.setText('Preparando universo y candidatas…')
        def operation(cancel,status):
            def progress(done,total):
                if total:status(f'PROGRESS:{min(99,int(done*100/total))}:{done:,} de {total:,} comprobaciones…')
            return reduce_coverage(candidates,current.base,config,sport=snapshot,
                                   cancelled=cancel,progress=progress)
        job=DataTask(operation,self);self.athena_job=job
        job.status.connect(self.athena_update_progress)
        job.completed.connect(lambda result:self.athena_reduction_done(current,result))
        job.failed.connect(self.athena_reduction_failed)
        job.finished.connect(lambda:self.athena_reduction_finished(job))
        job.start()

    def athena_update_progress(self,message):
        if message.startswith('PROGRESS:'):
            _,value,text=message.split(':',2)
            self.athena_progress.setValue(int(value));self.athena_status.setText(text)
        else:self.athena_status.setText(message)

    def cancel_athena_reduction(self):
        if self.athena_job is not None:
            self.athena_job.cancel_event.set();self.athena_status.setText('Cancelando… se conservarán las apuestas actuales.')

    def athena_reduction_done(self,source,result):
        if self.close_pending or self.system!=source:return
        try:
            copy=self.service.coverage_copy(source,result.bets,result.report)
            self.set_system(copy)
            report=result.report;coverage=report['coverage']
            status='garantía exhaustiva' if report['guarantee'] else 'cobertura observada; sin garantía exhaustiva'
            covered=round(coverage['uniform'][str(report['target_hits'])]*coverage['scenarios'])
            minimum=coverage['minimum_hits'] if coverage['minimum_hits'] is not None else f'{coverage["observed_minimum"]} observado'
            self.athena_status.setText(f'{len(result.bets):,} apuestas · {money(report["cost_cents"])} · '
                f'{covered:,}/{coverage["scenarios"]:,} resultados con al menos {report["target_hits"]} aciertos · mínimo {minimum} · {status}. '
                f'El Pleno al 15 se conserva en las columnas, pero queda fuera de esta verificación.')
            self.athena_progress.setValue(100)
        except (ValueError,OSError) as exc:self.athena_reduction_failed(str(exc))

    def athena_reduction_failed(self,message):
        self.athena_status.setText(message)

    def athena_reduction_finished(self,job):
        if self.athena_job is job:self.athena_job=None
        self.athena_run.setEnabled(True);self.athena_cancel.setEnabled(False)
        job.deleteLater()
        if self.close_pending:self.close();return
        self.refresh()

    def _connect_reduction_controls(self):
        for control in (self.repeat_enabled,self.repeat_minimum,self.repeat_maximum,
                        self.frequency_hits_min,self.frequency_hits_max,
                        self.frequency_count_min,self.frequency_count_max,
                        self.weight_sum_enabled,self.weight_sum_min,self.weight_sum_max,
                        self.weight_product_enabled,self.weight_product_min,self.weight_product_max):
            signal=getattr(control,'textChanged',None) or getattr(control,'valueChanged',None) or getattr(control,'toggled',None)
            if signal:signal.connect(self.manual_filters_changed)
        self.repeat_reference.changed.connect(self.manual_filters_changed)
        self.frequency_matrix.changed.connect(self.manual_filters_changed)
        for enabled,pattern,minimum,maximum in self.pattern_controls.values():
            enabled.toggled.connect(self.manual_filters_changed)
            pattern.changed.connect(self.manual_filters_changed)
            minimum.valueChanged.connect(self.manual_filters_changed);maximum.valueChanged.connect(self.manual_filters_changed)
        for check,min_control,max_control in ((self.weight_sum_enabled,self.weight_sum_min,self.weight_sum_max),
                                               (self.weight_product_enabled,self.weight_product_min,self.weight_product_max)):
            check.toggled.connect(min_control.setEnabled);check.toggled.connect(max_control.setEnabled)
            min_control.setEnabled(False);max_control.setEnabled(False)

    def build_reduction_rules(self):
        from quiniela_ai_studio.domain.reduction_rules import ReductionRule
        rules=[]
        for title,tab,profile_kind in (('Cuenta',0,'counts'),):
            if title in self.automatic_profile_rules:
                rules.append(replace(self.automatic_profile_rules[title],active=self.count_profile_active,tab_index=tab))
            elif self.count_profiles_selected:
                rules.append(ReductionRule('count-joint-profiles','allowed_profile',0,14,
                    profile_kind=profile_kind,allowed_profiles=tuple(sorted(self.count_profiles_selected)),
                    generation_method='manual',active=self.count_profile_active,tab_index=tab))
        meta=self.random_reduction_metadata.get('Cuenta',{})
        for sign,values in self.count_values.items():
            if values and 'Cuenta' not in self.automatic_profile_rules:
                rules.append(ReductionRule(f'count-values-{sign}','allowed_count',0,14,sign=sign,allowed_values=tuple(sorted(values)),
                    generation_method=meta.get('method',''),generation_seed=meta.get('seed'),generation_risk=meta.get('risk',''),
                    active=self.count_apply[sign].isChecked(),tab_index=0))
        rules.extend(self._build_streak_reduction_rules())
        rules.extend(self._build_fssiguedos_rules())
        rules.extend(self._build_interruption_rules())
        reference=self.repeat_reference.column()
        if self.repeat_enabled.isChecked():
            if not reference:raise ValueError('Marca una casilla 1/X/2 por partido para completar la referencia.')
            rules.append(ReductionRule('manual-repeat','reference_hits',self.repeat_minimum.value(),self.repeat_maximum.value(),reference=reference,tab_index=3))
        for size,(enabled,matrix,minimum,maximum) in self.pattern_controls.items():
            if enabled.isChecked():
                pattern=matrix.column()
                if not pattern:raise ValueError(f'Marca un signo por fila para completar el patrón de {size} partidos.')
                rules.append(ReductionRule(f'manual-pattern-{size}','pattern_occurrences',minimum.value(),maximum.value(),patterns=(pattern,),tab_index=size+2))
        if self.frequency_reference_list.count():
            references=tuple(self.frequency_reference_list.item(i).text() for i in range(self.frequency_reference_list.count()))
            rules.append(ReductionRule('manual-hit-frequency','hit_frequency',self.frequency_count_min.value(),self.frequency_count_max.value(),
                                       reference_minimum=self.frequency_hits_min.value(),reference_maximum=self.frequency_hits_max.value(),references=references,tab_index=11))
        if self.weight_sum_enabled.isChecked() or self.weight_product_enabled.isChecked():
            snapshot=self.frozen_round().snapshot(self.ranking_source.currentData())
            if not snapshot:raise ValueError('Descarga porcentajes de la fuente seleccionada antes de usar valoraciones.')
            weights=tuple(tuple(float(v) for v in row) for row in snapshot.values)
            if self.weight_sum_enabled.isChecked():
                rules.append(ReductionRule('manual-weight-sum','weighted_sum',self.weight_sum_min.value(),self.weight_sum_max.value(),weights=weights,tab_index=12))
            if self.weight_product_enabled.isChecked():
                rules.append(ReductionRule('manual-weight-logp','weighted_log_probability',self.weight_product_min.value(),self.weight_product_max.value(),weights=weights,tab_index=12))
        self.weight_status.setText('Fuente: '+snapshot.source+' · valores guardados para esta quiniela.' if (self.weight_sum_enabled.isChecked() or self.weight_product_enabled.isChecked()) else 'Activa una valoración para usar los porcentajes de la fuente elegida.')
        return tuple(rules)

    def _build_streak_reduction_rules(self):
        """Serialize one canonical 1/X/2/V configuration; legacy rows stay exact."""
        from quiniela_ai_studio.domain.reduction_rules import ReductionRule
        if 'Racha' in self.automatic_profile_rules:
            return [replace(self.automatic_profile_rules['Racha'],active=True,tab_index=1)]
        if self.legacy_streak_rules:
            return [replace(rule,tab_index=1) for rule in self.legacy_streak_rules]

        page_active=self.reduction_active.get(1,False)
        rules=[]
        for sign in ('1','X','2','V'):
            run_active=self.run_apply[sign].isChecked()
            figure_active=self.run_figure_apply[sign].isChecked()
            minimum=self.run_minmax_values[sign]['minimum'];maximum=self.run_minmax_values[sign]['maximum']
            if page_active and run_active:
                low,high=self.run_possible_bounds[sign]
                if minimum is not None and maximum is not None and minimum>maximum:
                    raise ValueError(f'El mínimo de {sign} no puede superar el máximo.')
                if minimum is not None and minimum>high or maximum is not None and maximum<low:
                    raise ValueError(f'El límite elegido para {sign} queda fuera de lo posible en la base ({low}–{high}).')
                for length,counts in self.run_count_values[sign].items():
                    impossible=counts-self.run_possible_counts.get((sign,length),set())
                    if impossible:raise ValueError(f'La base actual no puede alcanzar «Veces» {sorted(impossible)} de longitud {length} para {sign}.')
            meta=self.run_generation_metadata
            common={'generation_method':meta.get('method','manual'),'generation_seed':meta.get('seed'),
                'generation_risk':meta.get('risk',''),'evidence_source':meta.get('source',''),
                'evidence_seasons':tuple(meta.get('seasons',())),
                'evidence_sample_size':int(meta.get('sample_size',0)),
                'evidence_coverage':float(meta.get('coverage',0)),'tab_index':1}
            if minimum is not None or maximum is not None:
                rules.append(ReductionRule(f'streak-max-{sign}','longest_run',
                    0 if minimum is None else minimum,14 if maximum is None else maximum,sign=sign,
                    run_minimum_enabled=minimum is not None,run_maximum_enabled=maximum is not None,
                    active=run_active,**common))
            for length,counts in self.run_count_values[sign].items():
                if counts:
                    rules.append(ReductionRule(f'streak-count-{sign}-{length}','allowed_run_count',0,14,
                        sign=sign,run_length=length,allowed_values=tuple(sorted(counts)),active=run_active,**common))
            totals=self.run_figure_totals[sign]|set(self.run_figure_values[sign])
            if page_active and figure_active:
                if not totals:raise ValueError(f'Selecciona al menos un total y una figura para {sign}.')
                for total in totals:
                    chosen=self.run_figure_values[sign].get(total,set())
                    if not chosen:raise ValueError(f'El total {total} de {sign} no tiene figuras seleccionadas.')
                    impossible=chosen-set(self.run_possible_figures[sign].get(total,()))
                    if impossible:raise ValueError(f'La base actual no alcanza las figuras elegidas para {sign}, total {total}.')
            for total in sorted(totals):
                chosen=tuple(sorted(self.run_figure_values[sign].get(total,set()),
                    key=lambda figure:tuple(-int(part) for part in figure.split('-')) if figure else ()))
                rules.append(ReductionRule(f'streak-figure-{sign}-{total}','allowed_run_figure',0,1,
                    sign=sign,allowed_figures=chosen,active=figure_active,**common))
        return rules

    def add_frequency_reference(self):
        reference=self.frequency_matrix.column()
        if not reference:raise ValueError('Marca una casilla 1/X/2 en cada partido antes de añadir la referencia.')
        existing=[self.frequency_reference_list.item(i).text() for i in range(self.frequency_reference_list.count())]
        if reference in existing:raise ValueError('Esa columna ya está en la lista.')
        self.frequency_reference_list.addItem(reference)
        self.frequency_matrix.set_column('');self.manual_filters_changed()

    def remove_frequency_reference(self):
        row=self.frequency_reference_list.currentRow()
        if row>=0:self.frequency_reference_list.takeItem(row);self.manual_filters_changed()

    def add_advanced_group(self):
        if len(self.advanced_groups)>=8:return
        index=len(self.advanced_groups);name=f'Grupo{chr(65+index)}';letter=chr(65+index)
        card=QGroupBox();card.setObjectName('reductionGroupCard');card.setFixedWidth(132)
        box=QVBoxLayout(card);box.setContentsMargins(5,5,5,5);box.setSpacing(3)
        title=QLabel(f'GRUPO {letter}');title.setObjectName('reductionGroupTitle');title.setAlignment(Qt.AlignmentFlag.AlignCenter);box.addWidget(title)
        enabled=QCheckBox('Usar');box.addWidget(enabled)
        grid=QGridLayout();grid.setContentsMargins(0,0,0,0);grid.setHorizontalSpacing(3);grid.setVerticalSpacing(1)
        for col,label in enumerate(('#','1','X','2')):
            header=QLabel(label);header.setAlignment(Qt.AlignmentFlag.AlignCenter);header.setObjectName('reductionGroupIndex');header.setStyleSheet('font-weight:bold;color:#57d4ff;')
            grid.addWidget(header,0,col)
        buttons=[];match_labels=[]
        for row in range(14):
            label=QLabel(f'{row+1:02}');label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setFixedWidth(20);label.setObjectName('reductionGroupIndex')
            label.setToolTip(f'Partido {row+1}');match_labels.append(label);grid.addWidget(label,row+1,0)
            row_buttons=[]
            for col,sign in enumerate('1X2',1):
                button=QPushButton(sign);button.setCheckable(True);button.setFixedSize(24,20)
                button.setStyleSheet('QPushButton{padding:0;border-radius:2px;background:#f3f6fb;color:#16406a;border:1px solid #9bb9d4;} QPushButton:checked{background:#d82848;color:white;border:1px solid #ff6678;font-weight:bold;} QPushButton:disabled{color:#9aabba;background:#e6edf3;}')
                button.toggled.connect(self.advanced_conditions_changed);grid.addWidget(button,row+1,col);row_buttons.append(button)
            buttons.append(row_buttons)
        box.addLayout(grid)
        range_row=QGridLayout();range_row.setContentsMargins(0,3,0,0);range_row.setHorizontalSpacing(3);range_row.setVerticalSpacing(2)
        minimum=QSpinBox();minimum.setRange(0,14);maximum=QSpinBox();maximum.setRange(0,14);maximum.setValue(14)
        minimum.setFixedWidth(48);maximum.setFixedWidth(48)
        range_row.addWidget(QLabel('Aciertos'),0,0,1,2);range_row.addWidget(QLabel('Mín.'),1,0);range_row.addWidget(minimum,1,1);range_row.addWidget(QLabel('Máx.'),2,0);range_row.addWidget(maximum,2,1);box.addLayout(range_row)
        group={'name':name,'widget':card,'enabled':enabled,'buttons':buttons,'labels':match_labels,'minimum':minimum,'maximum':maximum,'selected_count':0}
        self.advanced_groups.append(group)
        enabled.toggled.connect(self.advanced_conditions_changed);minimum.valueChanged.connect(self.advanced_conditions_changed);maximum.valueChanged.connect(self.advanced_conditions_changed)
        minimum.valueChanged.connect(maximum.setMinimum);maximum.valueChanged.connect(minimum.setMaximum)
        self.advanced_group_layout.addWidget(card)
        self.update_relation_choices();self.update_advanced_enabled();self.refresh_advanced_match_labels()

    def remove_advanced_group(self):
        if len(self.advanced_groups)<=2:return
        group=self.advanced_groups.pop();self.advanced_group_layout.removeWidget(group['widget']);group['widget'].deleteLater()
        self.update_relation_choices();self.update_advanced_enabled();self.advanced_conditions_changed()

    def update_relation_choices(self):
        current=self.advanced_relation_groups.currentData() if hasattr(self,'advanced_relation_groups') else None
        self.advanced_relation_groups.blockSignals(True);self.advanced_relation_groups.clear()
        for left in range(len(self.advanced_groups)):
            for right in range(left+1,len(self.advanced_groups)):
                pair=(self.advanced_groups[left]['name'],self.advanced_groups[right]['name'])
                self.advanced_relation_groups.addItem(f'Grupo {chr(65+left)} y {chr(65+right)}',pair)
        if current is not None:
            index=self.advanced_relation_groups.findData(current)
            if index>=0:self.advanced_relation_groups.setCurrentIndex(index)
        self.advanced_relation_groups.blockSignals(False)
        for combo in (self.implication_from,self.implication_to):
            selected=combo.currentData();combo.blockSignals(True);combo.clear()
            for index in range(len(self.advanced_groups)):
                combo.addItem(f'Grupo {chr(65+index)}',self.advanced_groups[index]['name'])
            pos=combo.findData(selected)
            if pos>=0:combo.setCurrentIndex(pos)
            combo.blockSignals(False)
        if hasattr(self,'columns_group_checks'):
            previous={name:check.isChecked() for name,check in getattr(self,'columns_group_check_map',{}).items()}
            while self.columns_group_checks.count():
                item=self.columns_group_checks.takeAt(0)
                if item.widget():item.widget().deleteLater()
            self.columns_group_check_map={}
            for index,group in enumerate(self.advanced_groups):
                check=QCheckBox(f'Grupo {chr(65+index)}');check.setChecked(previous.get(group['name'],False))
                check.toggled.connect(self.advanced_conditions_changed)
                self.columns_group_checks.addWidget(check,index//4,index%4);self.columns_group_check_map[group['name']]=check

    def refresh_advanced_match_labels(self):
        if not hasattr(self,'advanced_groups') or not self.round_picker.currentData():return
        for group in self.advanced_groups:
            for index,label in enumerate(group['labels']):
                match=self.round.matches[index]
                label.setToolTip(f'{index+1:02} · {match.home} – {match.away}')

    def update_advanced_enabled(self):
        active_conditions=0
        for group in self.advanced_groups:
            active=group['enabled'].isChecked()
            active_conditions+=int(active)
            selected=sum(any(button.isChecked() for button in row) for row in group['buttons'])
            for row in group['buttons']:
                for button in row:button.setEnabled(active)
            previous=group['selected_count']
            group['maximum'].setMaximum(selected)
            if group['maximum'].value()==previous:group['maximum'].setValue(selected)
            group['minimum'].setMaximum(selected)
            group['selected_count']=selected
            group['minimum'].setEnabled(active);group['maximum'].setEnabled(active)
            group['enabled'].setEnabled(True)
        active=self.advanced_relation_enabled.isChecked()
        active_conditions+=int(active)
        implication_active=self.implication_enabled.isChecked()
        active_conditions+=int(implication_active)
        column_sum_active=self.columns_sum_enabled.isChecked()
        active_conditions+=int(column_sum_active)
        relation_limit=14 if self.advanced_operation.currentData()=='difference' else 28
        self.advanced_relation_min.setMaximum(relation_limit)
        self.advanced_relation_max.setMaximum(relation_limit)
        for control in (self.advanced_relation_groups,self.advanced_operation,self.advanced_relation_min,self.advanced_relation_max):control.setEnabled(active)
        for control in (self.implication_from,self.implication_to,self.implication_from_min,self.implication_from_max,self.implication_to_min,self.implication_to_max):control.setEnabled(implication_active)
        maximum_sum=sum(self.advanced_groups[i]['selected_count'] for i,group in enumerate(self.advanced_groups)
                        if self.columns_group_check_map.get(group['name']) and self.columns_group_check_map[group['name']].isChecked())
        self.columns_sum_min.setMaximum(maximum_sum);self.columns_sum_max.setMaximum(maximum_sum)
        for control in self.columns_group_check_map.values():control.setEnabled(column_sum_active)
        self.columns_sum_min.setEnabled(column_sum_active);self.columns_sum_max.setEnabled(column_sum_active)
        if self.implication_from.count():
            self.implication_from_max.setMaximum(self.advanced_groups[self.implication_from.currentIndex()]['selected_count'])
            self.implication_from_min.setMaximum(self.implication_from_max.value())
        if self.implication_to.count():
            self.implication_to_max.setMaximum(self.advanced_groups[self.implication_to.currentIndex()]['selected_count'])
            self.implication_to_min.setMaximum(self.implication_to_max.value())
        self.advanced_add_group.setEnabled(len(self.advanced_groups)<8)
        self.advanced_remove_group.setEnabled(len(self.advanced_groups)>2)
        self.advanced_failures.setMaximum(active_conditions)

    def advanced_conditions_changed(self,*_args):
        self.update_advanced_enabled()
        if hasattr(self,'filter_timer'):
            self.schedule_live_filter()

    def advanced_spec(self):
        from quiniela_ai_studio.domain.advanced_conditions import (
            AdvancedConditions,
            HitGroup,
            HitImplication,
            HitRelation,
        )
        groups=[]
        for group in self.advanced_groups:
            if not group['enabled'].isChecked():continue
            places=[];accepted=[]
            for index,row in enumerate(group['buttons']):
                mask=''.join(sign for sign,button in zip('1X2',row,strict=True) if button.isChecked())
                if mask:places.append(index);accepted.append(mask)
            groups.append(HitGroup(group['name'],tuple(places),tuple(accepted),group['minimum'].value(),group['maximum'].value()))
        relations=[]
        if self.advanced_relation_enabled.isChecked():
            pair=self.advanced_relation_groups.currentData()
            if not pair or not set(pair)<=set(group.name for group in groups):raise ValueError('Para usar la relación, activa los dos grupos elegidos y marca sus partidos.')
            relations.append(HitRelation(self.advanced_operation.currentData(),tuple(pair),self.advanced_relation_min.value(),self.advanced_relation_max.value()))
        implications=[]
        if self.implication_enabled.isChecked():
            antecedent=self.implication_from.currentData();consequent=self.implication_to.currentData()
            if antecedent==consequent or not {antecedent,consequent}<=set(group.name for group in groups):
                raise ValueError('Activa dos grupos distintos antes de configurar la condición si… entonces.')
            implications.append(HitImplication(antecedent,self.implication_from_min.value(),self.implication_from_max.value(),
                consequent,self.implication_to_min.value(),self.implication_to_max.value()))
        if self.columns_sum_enabled.isChecked():
            selected=tuple(name for name,check in self.columns_group_check_map.items() if check.isChecked())
            if len(selected)<2:raise ValueError('Selecciona al menos dos grupos para sumar sus aciertos.')
            relations.append(HitRelation('sum',selected,self.columns_sum_min.value(),self.columns_sum_max.value()))
        return AdvancedConditions(tuple(groups),tuple(relations),self.advanced_failures.value(),tuple(implications),
                                  tuple(index for index,active in self.reduction_active.items() if active and index<17))

    @staticmethod
    def kickoff_caption(value):
        """Compact weekday/time from the stored WIN1X2 schedule, without inventing it."""
        if not value:
            return '—'
        for pattern in ('%d/%m/%Y%H:%M', '%d/%m/%Y %H:%M'):
            try:
                stamp=datetime.strptime(value,pattern)
            except ValueError:
                continue
            day=('LUN','MAR','MIÉ','JUE','VIE','SÁB','DOM')[stamp.weekday()]
            return f'{day} {stamp:%H:%M}'
        return value

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self,'prize_layout'):
            compact=self.width()<1700
            self.prize_layout.setDirection(QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight)
            self.prize_card.setMinimumHeight(82)
            if hasattr(self,'prize_grid_widget'):
                self.prize_grid_widget.setVisible(not compact)
            if hasattr(self,'prize_cards_layout'):
                self.prize_cards_layout.setDirection(
                    QBoxLayout.Direction.TopToBottom if self.width()<1100 else QBoxLayout.Direction.LeftToRight
                )
        if hasattr(self, 'scrutiny_splitter') and self.navigation.currentRow() == 4:
            QTimer.singleShot(0, self.fit_scrutiny_tables)

    def fit_scrutiny_tables(self):
        """Reserve room for all 15 score rows before expanding the bet list."""
        if self.close_pending or self.navigation.currentRow() != 4:
            return
        table = self.live_view
        complete = table.horizontalHeader().height() + 15 * table.verticalHeader().defaultSectionSize() + 2 * table.frameWidth()
        if table.horizontalScrollBar().isVisible():
            complete += table.horizontalScrollBar().height()
        if self.manual_mode.isChecked():
            complete = self.manual_container.maximumHeight()
        available = self.scrutiny_splitter.height() - self.scrutiny_splitter.handleWidth()
        if self.prize_card.isVisible() or self.prize_detail_card.isVisible():
            if self.prize_cards_layout.direction()==QBoxLayout.Direction.TopToBottom:reserve=385
            else:reserve=260 if self.width()<1700 else 220
        else:reserve=160
        upper = min(complete, max(80, available - reserve))
        self.scrutiny_splitter.setSizes([upper, max(100, available - upper)])

    def start_session(self):
        """Offer to resume once, or create a separate ballot for the current round."""
        if self._startup_prompt_done or self.close_pending:
            return
        self._startup_prompt_done = True
        previous = self.system or self.saved_builder('reduced')
        if self._startup_system_id:
            try:
                previous = self.repository.load(self._startup_system_id)
            except ValueError:
                pass
        if previous and self.ask_resume(previous):
            self.load_rounds(previous.round_key)
            self.set_system(previous)
            self.navigation.setCurrentRow(7 if self.system_mode(previous) == 'reduced' else 1)
        else:
            self.start_new_current()

    def ask_resume(self, previous):
        new_description = (
            'Si eliges No, empezaremos una nueva de ejemplo (datos ficticios).'
            if all(r.mode == 'simulation' for r in self.repository.rounds())
            else 'Si eliges No, empezaremos una nueva para la jornada actual.'
        )
        dialog = QMessageBox(
            QMessageBox.Icon.Question, 'Continuar con tu quiniela',
            f'¿Quieres continuar con tu última quiniela?\n\n{previous.name}\n'
            f'Jornada: {previous.round_key}\n\n'
            f'{new_description}\nLa anterior seguirá guardada en Mis Sistemas.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self,
        )
        dialog.setTextFormat(Qt.TextFormat.PlainText)
        dialog.button(QMessageBox.StandardButton.Yes).setText('Sí, continuar')
        dialog.button(QMessageBox.StandardButton.No).setText('No, empezar una nueva')
        dialog.setDefaultButton(QMessageBox.StandardButton.Yes)
        dialog.setEscapeButton(QMessageBox.StandardButton.Yes)
        return dialog.exec() == QMessageBox.StandardButton.Yes

    def start_new_current(self, *, download=True):
        """Use an editable current round; never present an old round as current."""
        self.navigation.setCurrentRow(self.SECTIONS.index('Normal'))
        self.set_system(None)
        rounds = self.repository.rounds()
        current = next((r for r in rounds if r.mode == 'current' and r.editable), None)
        if current is None and all(r.mode == 'simulation' for r in rounds):
            current = rounds[0] if rounds else None
        if current:
            self.load_rounds(current.key)
            self.new_system()
            self.background_status('Quiniela nueva preparada. Las anteriores siguen en Mis Sistemas.')
        elif download:
            self._startup_new_pending = True
            self.background_status('Descargando los partidos de la jornada actual para crear tu nueva quiniela…')
            self.download_data()
        else:
            self.background_status('No tenemos los partidos de la jornada actual. Pulsa Descargar datos o importa una carpeta actual; tus quinielas anteriores siguen guardadas.')

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
        for header in self.classic_headers.values():
            header.set_context(self.round.season,str(self.round.number))
        self.template_timer.stop()
        mode='reduced' if self.navigation.currentRow()==7 else 'normal'
        self.system=self.saved_builder(mode)
        self.update_streak_base_limits()
        self.restore_builder_controls()
        self.choose_reduction_positions()
        self.restore_filter_controls()
        self._restore_interruption_seasons_for_round()
        self.refresh_advanced_match_labels()
        self._update_fss_context()
        self._update_interruption_context()
        self.result_input.setText('-'*14)
        self.result_pleno.clear()
        self.final_check.setChecked(False)
        self.clear_scrutiny_awards()
        self.eval_model.update_rows([])
        self.prize_cache_error=''
        self.eval_summary.setText('Selecciona resultados para esta jornada.')
        self.live_matches = None
        self.live_pleno_summary.setText('Pleno actual: pendiente')
        self.live_model.update_rows([])
        cached = self.repository.setting('live:' + self.round.key)
        self.live_status.setText('Sin marcador guardado para esta jornada.')
        if cached:
            try:self.restore_live()
            except ValueError as exc:self.live_status.setText(str(exc))
        else:
            self.show_live_waiting(self.frozen_round())
        self.reset_manual_inputs()
        if self.navigation.currentRow()==4 and not self.manual_mode.isChecked():
            self.show_cached_scrutiny()
        self.ensure_live_updates()
        if not self._initializing:
            self.remember_builder()
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
        optimization=params.get('optimization_report')
        verification=params.get('reduction_verification') or (
            optimization.get('after') if isinstance(optimization,dict) else None
        )
        guarantee=coverage_footer(verification)
        self.footer.setText(f'{quantity:,} apuestas · {money(self.system.cost(round_) if self.system else 0)} · {pending} sin Pleno{guarantee} · Premio económico no garantizado')
        self.home_info.setText(f'{round_.key}\n15 partidos · {len(self.repository.systems(round_.key))} quinielas guardadas\nPrecio por apuesta: {money(round_.price_cents)} por apuesta. Guardar un archivo no envía ni paga la apuesta.')
        self.data_info.setText('Datos guardados: ' + (self.repository.setting('data_directory') or 'todavía no has añadido datos') + '\nWIN1X2 aporta partidos y premios. Quinielista aporta elecciones de otros jugadores y marcadores.')
        self.rule_price.setValue(round_.price_cents)
        busy = bool((self.filter_job and self.filter_job.isRunning()) or (self.worker and self.worker.isRunning()) or (self.data_worker and self.data_worker.isRunning()) or (self.athena_job and self.athena_job.isRunning()))
        for button in self.edit_buttons:
            button.setEnabled(round_.editable and not busy)
        generating=bool(self.worker and self.worker.isRunning())
        if not generating:
            self.progress.setValue(100 if self.system and self.system.bets else 0)
        self.progress.setFormat('%p%' if generating or (self.system and self.system.bets) else 'Sin desarrollo generado')
        # filter_group remains a hidden QObject parent for legacy lookups; disabling
        # it would also disable the controls reparented into the reduction tabs.
        self.update_filter_controls()
        self.quick_conditions_slider.setEnabled(round_.editable and not ((self.worker and self.worker.isRunning()) or (self.data_worker and self.data_worker.isRunning())))
        system = self.system
        number=json.loads(system.parameters).get('reduction_choice',json.loads(system.parameters).get('reduction',self.reduction_picker.currentData())) if system else None
        self.ballot_title.setText(f'BASE PARA REDUCIDA {number}' if self.construction_mode()=='reduced' else 'PARTIDOS DE LA JORNADA')
        if hasattr(self,'normal_generator'):
            self.normal_generator.load_round(view_round,system)
        self.pleno_auto_level.setEnabled(bool(system and round_.editable and not busy and self.pleno_mode.currentData()=='auto'))
        self.differentiation.setEnabled(bool(system and round_.editable and not busy))
        self.pleno_mode.setEnabled(bool(system and round_.editable and not busy))
        self.update_budget_capacity()
        for i, match in enumerate(view_round.matches[:14]):
            kickoff=match.kickoff[:10]+' '+match.kickoff[10:] if len(match.kickoff)==15 else match.kickoff
            self.match_labels[i].setText(f'{match.home} – {match.away}')
            self.match_labels[i].setToolTip(f'{match.home} – {match.away}\n{kickoff}')
            self.kickoff_labels[i].setText(self.kickoff_caption(match.kickoff))
            self.kickoff_labels[i].setToolTip(kickoff or 'Horario no disponible')
            snapshot = view_round.snapshot('sport'); public = view_round.snapshot('public')
            fmt = lambda snap,position=i: ' / '.join(f'{100*v:.0f}' for v in snap.values[position]) if snap else 'Sin datos'
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
        self.pleno_match_label.setText('Pleno al 15')
        self.pleno_match_label.setToolTip(f'{pleno_match.home} – {pleno_match.away}')
        for label,team,role in zip(self.pleno_team_labels,(pleno_match.home,pleno_match.away),('Local','Visitante')):
            label.setText(team);label.setToolTip(f'{role}: {team}')
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
        self.button('Consultar escrutinio', lambda: self.navigation.setCurrentRow(4), row)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.data_button('Descargar / actualizar datos', self.download_data, row, primary=True)
        self.data_button('Importar datos locales', self.import_win1x2, row)
        self.button('En curso', self.go_current, row)
        layout.addLayout(row)
        note = QLabel('Crea una quiniela normal o una reducida. Elige 1 si gana el local, X si empatan y 2 si gana el visitante.')
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
        scroll = QScrollArea(); scroll.setWidgetResizable(True);scroll.setMaximumHeight(322)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ballot_scroll = scroll
        grid_widget = QWidget();grid_widget.setFixedHeight(322)
        grid = QGridLayout(grid_widget); grid.setSpacing(1);grid.setContentsMargins(6,4,6,4);grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        grid_widget.setObjectName('ballot')
        for col,title in enumerate(('', 'Partido', 'Hora', 'Modelo %', '1', 'X', '2', 'Bloq.')):
            heading=QLabel(title);heading.setFixedHeight(20);heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
            heading.setProperty('ballotHeader','sign' if col in (4,5,6) else 'data')
            grid.addWidget(heading,0,col)
            if col==3:self.prob_heading=heading
        self.match_labels=[];self.kickoff_labels=[];self.prob_labels=[];self.sign_buttons=[];self.lock_buttons=[]
        for i in range(14):
            shade='even' if i%2==0 else 'odd'
            number=QLabel(str(i+1));number.setFixedSize(20,20);number.setAlignment(Qt.AlignmentFlag.AlignCenter);number.setProperty('ballotShade',shade)
            number.setStyleSheet('font-weight:bold;');grid.addWidget(number,i+1,0)
            label=QLabel();label.setMinimumWidth(140);label.setFixedHeight(20);label.setStyleSheet('font-size:11px; font-weight:bold;')
            label.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
            label.setProperty('ballotShade',shade);self.match_labels.append(label);grid.addWidget(label,i+1,1)
            hour=QLabel();hour.setFixedSize(58,20);hour.setAlignment(Qt.AlignmentFlag.AlignCenter);hour.setStyleSheet('font-size:9px;');hour.setProperty('ballotShade',shade)
            self.kickoff_labels.append(hour);grid.addWidget(hour,i+1,2)
            prob=QLabel();prob.setFixedSize(72,20);prob.setAlignment(Qt.AlignmentFlag.AlignCenter);prob.setStyleSheet('font-size:9px;');prob.setProperty('ballotShade',shade)
            self.prob_labels.append(prob);grid.addWidget(prob,i+1,3)
            signs={}
            for j, sign in enumerate('1X2'):
                button=QPushButton(sign); button.setCheckable(True); button.setFixedSize(27,20); button.setStyleSheet("padding: 1px;")
                button.setAccessibleName(f'Partido {i+1}, signo {sign}')
                button.clicked.connect(partial(self.toggle_sign,i,sign));grid.addWidget(button,i+1,j+4);signs[sign]=button
            self.sign_buttons.append(signs)
            lock=QPushButton('Bloquear');lock.setCheckable(True);lock.setFixedSize(44,20);lock.setStyleSheet('padding:1px 5px;')
            lock.clicked.connect(partial(self.toggle_lock,i));grid.addWidget(lock,i+1,7);self.lock_buttons.append(lock)
        grid.setColumnStretch(1,1)
        scroll.setWidget(grid_widget);layout.addWidget(scroll)
        row=QHBoxLayout();self.pleno_match_label=QLabel();self.pleno_match_label.setWordWrap(True);self.pleno_match_label.setStyleSheet('color:#ffc83d; font-weight:bold;');row.addWidget(self.pleno_match_label)
        self.pleno_combos=[]
        for _ in range(2):
            combo=QComboBox();combo.addItems(['—','0','1','2','M']);combo.currentIndexChanged.connect(self.change_pleno)
            combo.hide();self.pleno_combos.append(combo)
        layout.addLayout(row)
        row=QHBoxLayout();row.addWidget(QLabel('Modo del Pleno'));self.pleno_mode=QComboBox();self.pleno_mode.addItem('Manual','manual');self.pleno_mode.addItem('Automático según fuente','auto');self.pleno_mode.addItem('Diversificado: varias parejas manuales','diversified');self.pleno_mode.currentIndexChanged.connect(self.schedule_template);row.addWidget(self.pleno_mode,1)
        row.addWidget(QLabel('Nivel automático'));self.pleno_auto_level=QSpinBox();self.pleno_auto_level.setRange(0,10);self.pleno_auto_level.setValue(0);self.pleno_auto_level.setFixedWidth(58);self.pleno_auto_level.setToolTip('Solo amplía los goles del Pleno en modo Automático.');self.pleno_auto_level.valueChanged.connect(self.schedule_template);row.addWidget(self.pleno_auto_level);layout.addLayout(row)
        self.goal_buttons=[]
        self.goal_percentages=[]
        self.pleno_team_labels=[]
        self.pleno_panel=QWidget();self.pleno_panel.setObjectName('plenoPanel')
        self.pleno_panel.setMaximumWidth(350)
        pleno_grid=QGridLayout(self.pleno_panel);pleno_grid.setContentsMargins(6,4,6,4);pleno_grid.setHorizontalSpacing(4);pleno_grid.setVerticalSpacing(1)
        badge=QLabel('P15');badge.setObjectName('plenoBadge');badge.setFixedWidth(32);badge.setAlignment(Qt.AlignmentFlag.AlignCenter);pleno_grid.addWidget(badge,0,1,5,1)
        for side,label_text in enumerate(('Local','Visitante')):
            team_label=QLabel(label_text);team_label.setObjectName('plenoTeam');team_label.setFixedWidth(140);self.pleno_team_labels.append(team_label)
            pleno_grid.addWidget(team_label,side*3,0,2,1);buttons={};percentages={}
            for column,goal in enumerate('012M',2):
                button=QPushButton(goal);button.setCheckable(True);button.setFixedSize(32,22);button.setToolTip('3 goles o más' if goal=='M' else f'{goal} goles')
                button.clicked.connect(lambda checked=False,i=side,g=goal:self.toggle_goal(i,g))
                pleno_grid.addWidget(button,side*3,column);buttons[goal]=button
                percentage=QLabel('—');percentage.setObjectName('plenoPercentage');percentage.setFixedWidth(32);percentage.setAlignment(Qt.AlignmentFlag.AlignCenter);pleno_grid.addWidget(percentage,side*3+1,column);percentages[goal]=percentage
            self.goal_buttons.append(buttons)
            self.goal_percentages.append(percentages)
        pleno_grid.setRowMinimumHeight(2,4);pleno_grid.setColumnStretch(6,1);layout.addWidget(self.pleno_panel)
        self.pleno_selection_info=QLabel();self.pleno_selection_info.setWordWrap(True);layout.addWidget(self.pleno_selection_info)
        left_layout=layout;layout=self.page_layout(1)
        self.normal_generator=NormalGenerator(self)
        self.normal_generator.base_group.setParent(None);layout.addWidget(self.normal_generator.base_group)
        row=QHBoxLayout();row.addWidget(QLabel('Elegir signos según'))
        self.ranking_source=QComboBox();self.ranking_source.addItem('Mercado: casas de apuestas','sport');self.ranking_source.addItem('Popularidad: Quinielista','public');row.addWidget(self.ranking_source,1)
        self.button('Descargar porcentajes',self.refresh_system_sources,row,editable=True).setToolTip('Descarga los porcentajes de los 14 partidos y del Pleno para la jornada abierta, sin cambiar tus apuestas.');layout.addLayout(row)
        self.source_status=QLabel();self.source_status.setWordWrap(True);layout.addWidget(self.source_status)
        self.ranking_source.currentIndexChanged.connect(self.ranking_source_changed)
        self.differentiation=QSlider(Qt.Orientation.Horizontal);self.differentiation.setRange(0,10)
        row=QHBoxLayout();row.addWidget(QLabel('Diferenciación del público'));row.addWidget(self.differentiation,1);self.differentiation_label=QLabel('0');row.addWidget(self.differentiation_label);layout.addLayout(row)
        self.differentiation.valueChanged.connect(lambda value:self.differentiation_label.setText(str(value)));self.differentiation.valueChanged.connect(self.schedule_template)
        note=QLabel('La diferenciación actualiza el boleto automáticamente. Si no hay datos de mercado y público, no altera la selección. Es un criterio de selección, no una predicción ni una garantía. Los triples y dobles se fijan con valores numéricos arriba y se aplican al pulsar «Rellenar quiniela base».')
        note.setWordWrap(True);note.setObjectName('muted');layout.addWidget(note)
        layout=left_layout
        row=QHBoxLayout();self.generate_button=self.button('Generar',self.start_generation,row,primary=True,editable=True)
        self.cancel_button=self.button('Cancelar',self.cancel_generation,row);self.cancel_button.setEnabled(False)
        self.progress=QProgressBar();self.progress.setValue(0);row.addWidget(self.progress,1);layout.addLayout(row)
        layout.addStretch(1)
        preview=self.page_layout(1)
        self.preview_info=QLabel();self.preview_info.setWordWrap(True);preview.addWidget(self.preview_info)
        self.preview_view,self.preview_model=self.table(('Columna','Pleno','Cantidad'),preview)
        note=QLabel('El boleto permanece visible a la izquierda. La vista muestra hasta 100 filas; el archivo exportado conserva todas las apuestas.');note.setWordWrap(True);preview.addWidget(note)
        row=QHBoxLayout();self.button('Guardar apuestas (TXT)',self.export_txt,row);self.button('Guardar quiniela (JSON)',self.export_json,row);preview.addLayout(row)
        self.full_export_button=self.data_button('Guardar todas las combinaciones…',self.export_development,preview)
        self.normal_generator.actions_group.setParent(None);preview.addWidget(self.normal_generator.actions_group)
        self.preview_view.setMaximumHeight(220)

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
        previous=(self.system.system_id,self.system.revision,self.system.hash) if self.system else None
        incoming=(system.system_id,system.revision,system.hash) if system else None
        if previous!=incoming:self.clear_scrutiny_awards()
        self.system=system
        self.update_streak_base_limits()
        self.remember_builder()
        if changed:self.template_timer.stop();self.restore_builder_controls();self.restore_filter_controls();self.choose_reduction_positions()
        self.refresh()
        if self.navigation.currentRow()==4 and not self.manual_mode.isChecked() and not self.show_cached_scrutiny():
            if self.live_matches:self.evaluate_live()
            else:
                self.prize_card.hide();self.prize_notice.show()
                self.prize_notice.setText('Premios pendientes de escrutinio publicado.')
                self.eval_model.update_rows([])
                self.eval_summary.setText('Abre una quiniela con apuestas y carga resultados para ver tus aciertos.')

    def clear_scrutiny_awards(self):
        """Discard awards from the previously selected system immediately."""
        self.published_scrutiny=None
        if hasattr(self,'prize_card'):
            self.prize_card.hide()
            self.prize_detail_card.hide()
            self.prize_total.clear()
            self.prize_notice.show()
            self.prize_notice.setText('Premios pendientes de escrutinio publicado.')
            self.eval_model.update_rows([])
            self.eval_summary.setText('Selecciona una quiniela para consultar su escrutinio.')

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
        self.repository.set_setting('last_open_system', self.system.system_id)

    def saved_builder(self,mode):
        key=self.repository.setting('builder_modes:'+self.round.key,{}).get(mode)
        if key:
            candidate=self.repository.load(key)
            if candidate.round_key==self.round.key and self.system_mode(candidate)==mode:return candidate
        systems=[s for s in self.repository.systems(self.round.key) if self.system_mode(s)==mode and (mode!='reduced' or json.loads(s.parameters).get('construction_mode')=='reduced')]
        return systems[-1] if systems else None

    def restore_builder_controls(self):
        params=json.loads(self.system.parameters) if self.system else {}
        for slider,value in ((self.pleno_auto_level,params.get('level',0)),(self.differentiation,params.get('differentiation_level',0)),(self.reduction_pleno_level,params.get('level',0)),(self.reduction_differentiation,params.get('differentiation_level',0))):
            slider.blockSignals(True);slider.setValue(value);slider.blockSignals(False)
        self.differentiation_label.setText(str(self.differentiation.value()))
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
        if hasattr(self,'normal_generator'):
            self.normal_generator.use_selected_snapshot(self.ranking_source.currentData())
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
        from quiniela_ai_studio.domain.normal_generation import best_base
        frozen=self.frozen_round();snapshot=frozen.snapshot(kind)
        has_pleno=bool(snapshot and snapshot.pleno_values)
        if self.differentiation.value():
            if not snapshot:raise ValueError('La diferenciación necesita porcentajes descargados de la fuente elegida.')
            from quiniela_ai_studio.domain.strategies import selection_weights
            weights=selection_weights(frozen,kind,self.differentiation.value())
            probabilities=weights.values;snapshot=weights
        else:
            matrix_has_values=any(self.normal_generator.probability_table.item(row,column) and self.normal_generator.probability_table.item(row,column).text().strip() for row in range(14) for column in (2,3,4))
            if self.normal_generator.matrix_origin in {'manual','weighted'} and matrix_has_values:
                probabilities=self.normal_generator._matrix_values()
            elif snapshot:probabilities=snapshot.values
            else:raise ValueError('La jornada no tiene porcentajes disponibles; importa una fuente o rellena la matriz 1/X/2 antes de aplicar la selección automática.')
        base,report=best_base(probabilities,self.normal_generator.triples.value(),self.normal_generator.doubles.value(),self.system.locks,self.system.base)
        parameters=json.loads(self.system.parameters)
        matrix_origin=self.normal_generator.matrix_origin
        if self.differentiation.value() or matrix_origin.startswith('snapshot:'):
            probability_source=snapshot.source if snapshot else None
        elif matrix_origin=='weighted':
            probability_source='Media ponderada de fuentes importadas'
        else:
            probability_source='Matriz editada manualmente'
        report.update(round_key=self.system.round_key,source=probability_source,
                      matrix_origin=self.normal_generator.matrix_origin,
                      factor_weights=({key:spin.value() for key,spin in self.normal_generator.weight_spin.items()}
                                      if matrix_origin=='weighted' else {}),
                      probabilities=[list(row) for row in probabilities])
        parameters.update(level=self.pleno_auto_level.value(),kind=kind,differentiation_level=self.differentiation.value(),pleno_mode=self.pleno_mode.currentData(),normal_base_generation=report)
        changes={"base":base,"bets":(),"origin":"Base automática por pérdida de cobertura","parameters":json.dumps(parameters,ensure_ascii=False)}
        if self.pleno_mode.currentData()=='auto' and snapshot and snapshot.pleno_values:
            masks=engine.pleno_template(snapshot,self.pleno_auto_level.value())
            plenos=tuple(local+visitor for local in masks[0] for visitor in masks[1])
            changes.update(pleno=plenos[0] if len(plenos)==1 else "",parameters=json.dumps({**parameters,"pleno_masks":list(masks),"plenos":list(plenos)},ensure_ascii=False))
        updated=self.service.version(self.system,**changes)
        self.repository.record_event('normal_base_generated',dict(base=list(base),**report))
        self.set_system(updated)
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
        self.prob_heading.setText('Modelo %' if self.ranking_source.currentData()=='sport' else 'Jugado %')
        self.prob_heading.setToolTip('Porcentajes 1 / X / 2 de la fuente seleccionada. Mercado y popularidad son datos diferentes; no son una IA propia.')
        for i,label in enumerate(self.prob_labels):
            values=' / '.join(f'{100*v:.0f}' for v in snapshot.values[i]) if snapshot else '—'
            label.setText(values)
            label.setToolTip(f'{snapshot.source}\n1 / X / 2: {values}' if snapshot else 'Sin porcentajes disponibles de esta fuente.')
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
        self.filter_job=None;self.filter_epoch=0;self.filter_pending=False;self.athena_job=None
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
            check=QCheckBox(label_text);check.setProperty('filterLabel',label_text);check.setToolTip(self.filter_tips[key]);check.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Fixed);self.filter_checks[key]=check
            check.toggled.connect(self.filters_changed);grid.addWidget(check,i,0)
            minimum=QSpinBox();minimum.setRange(lower,upper);minimum.setValue(lower);minimum.setMaximumWidth(70)
            maximum=QSpinBox();maximum.setRange(lower,upper);maximum.setValue(upper);maximum.setMaximumWidth(70)
            self.filter_ranges[key]=(minimum,maximum)
            grid.addWidget(QLabel('Desde'),i,1);grid.addWidget(minimum,i,2);grid.addWidget(QLabel('Hasta'),i,3);grid.addWidget(maximum,i,4)
        self.filter_max_one=QSpinBox();self.filter_max_one.setRange(1,14);self.filter_max_one.setValue(14)
        self.filter_max_x=QSpinBox();self.filter_max_x.setRange(1,14);self.filter_max_x.setValue(14)
        self.filter_max_two=QSpinBox();self.filter_max_two.setRange(1,14);self.filter_max_two.setValue(14)
        for row,key,label_text,control in ((6,'max_one_run','Locales seguidos (1)',self.filter_max_one),(7,'max_x_run','Empates seguidos (X)',self.filter_max_x),(8,'max_two_run','Visitantes seguidos (2)',self.filter_max_two)):
            check=QCheckBox(label_text);check.setProperty('filterLabel',label_text);check.setToolTip(self.filter_tips[key]);check.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Fixed);self.filter_checks[key]=check
            check.toggled.connect(self.filters_changed);grid.addWidget(check,row,0);grid.addWidget(QLabel('Máximo'),row,1);grid.addWidget(control,row,2)
        self.filter_reference=SignMatrixWidget(14)
        self.filter_reference.setToolTip('Marca una casilla 1/X/2 por partido. Solo se usa con «Parecido a otra quiniela».')
        grid.addWidget(QLabel('La otra quiniela'),9,0);grid.addWidget(self.filter_reference,9,1,1,4)
        self.filter_reset=QPushButton('Quitar todas las condiciones');self.filter_reset.clicked.connect(self.reset_filters)
        self.filter_feedback=QLabel();self.filter_feedback.setWordWrap(True)
        layout.addStretch()
        self.budget_group=QGroupBox('2. Ajusta el resultado a tu presupuesto')
        budget_outer=QVBoxLayout(self.budget_group);budget_layout=QHBoxLayout();budget_outer.addLayout(budget_layout);budget_layout.addWidget(QLabel('1. Máximo (€)'))
        self.budget=QDoubleSpinBox();self.budget.setRange(0,100000);self.budget.setDecimals(2);self.budget.setValue(10);budget_layout.addWidget(self.budget)
        self.budget_capacity=QLabel();budget_layout.addWidget(self.budget_capacity)
        row=QHBoxLayout();row.addWidget(QLabel('2. Objetivo'));self.portfolio_objective=QComboBox()
        for label,key in (('Automático recomendado','auto'),('Máxima probabilidad','probability'),('Máxima cobertura 13+/12+','coverage'),('Valor esperado: no disponible','expected')):self.portfolio_objective.addItem(label,key)
        self.portfolio_objective.model().item(3).setEnabled(False);row.addWidget(self.portfolio_objective,1);budget_outer.addLayout(row)
        self.budget_apply=self.button('3. Optimizar mis apuestas',self.optimize,row,primary=True,editable=True)
        self.portfolio_cancel=self.button('Cancelar optimización',self.cancel_data,budget_outer)
        self.portfolio_cancel.setEnabled(False)
        advanced_toggle=QCheckBox('Parámetros avanzados');budget_outer.addWidget(advanced_toggle)
        advanced=QGroupBox('Parámetros avanzados de optimización');advanced_layout=QGridLayout(advanced);advanced.hide()
        # Comparte el área desplazable de condiciones: nunca desplaza los
        # botones de presupuesto/cancelación fuera de pantallas pequeñas.
        layout.insertWidget(1,advanced)
        advanced_toggle.toggled.connect(advanced.setVisible)
        advanced_toggle.toggled.connect(lambda checked:QTimer.singleShot(0,lambda:scroll.ensureWidgetVisible(advanced)) if checked else None)
        self.portfolio_advanced_toggle=advanced_toggle;self.portfolio_advanced=advanced
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
        self.filter_reference.changed.connect(self.manual_filters_changed)
        self.quick_conditions_slider.valueChanged.connect(self.configure_quick_conditions)
        self.update_filter_controls()

    def restore_filter_controls(self):
        """Restore saved optimization settings without recalculating on load."""
        self.filter_timer.stop();self.filter_epoch+=1
        if self.filter_job:self.filter_job.cancel_event.set()
        self.configuring_filters=True
        params=json.loads(self.system.parameters) if self.system else {}
        saved=params.get('filter_spec',{})
        saved_tabs=saved.get('reduction_tabs_enabled')
        for index,square in self.reduction_activation_buttons.items():
            square.blockSignals(True);square.setChecked(False);square.blockSignals(False)
            self.reduction_active[index]=False
        configured=bool(self.system and self.repository.setting(f'reduction_tabs_configured:{self.system.system_id}',False))
        if configured and isinstance(saved_tabs,list):
            active=set(saved_tabs)&{0,1,9,17,18}
            for index,square in self.reduction_activation_buttons.items():
                square.blockSignals(True);square.setChecked(index in active);square.blockSignals(False)
                self.reduction_active[index]=index in active
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
        self.filter_reference.set_column(saved.get('reference',''))
        self.filter_checks['coincidences'].setChecked(bool(saved.get('reference')))
        from quiniela_ai_studio.domain.advanced_conditions import (
            advanced_from_parameters,
        )
        advanced=advanced_from_parameters(saved.get('advanced'))
        self.configuring_filters=True
        required=max(6,max((ord(group.name[-1])-ord('A')+1 for group in advanced.groups),default=0))
        while len(self.advanced_groups)<required:self.add_advanced_group()
        while len(self.advanced_groups)>required:self.remove_advanced_group()
        for group_ui in self.advanced_groups:
            group_ui['enabled'].setChecked(False)
            for row in group_ui['buttons']:
                for button in row:button.setChecked(False)
        for group in advanced.groups:
            index=ord(group.name[-1])-ord('A');group_ui=self.advanced_groups[index]
            group_ui['enabled'].setChecked(True)
            for position,mask in zip(group.positions,group.accepted,strict=True):
                for sign,button in zip('1X2',group_ui['buttons'][position],strict=True):button.setChecked(sign in mask)
            group_ui['minimum'].setValue(group.minimum);group_ui['maximum'].setValue(group.maximum)
        difference=next((item for item in advanced.relations if item.operation=='difference'),None)
        if difference:
            relation=difference;self.advanced_relation_enabled.setChecked(True)
            self.update_relation_choices()
            self.advanced_relation_groups.setCurrentIndex(self.advanced_relation_groups.findData(relation.groups))
            self.advanced_operation.setCurrentIndex(self.advanced_operation.findData(relation.operation))
            self.advanced_relation_min.setValue(relation.minimum);self.advanced_relation_max.setValue(relation.maximum)
        summed=next((item for item in advanced.relations if item.operation=='sum'),None)
        if summed:
            self.columns_sum_enabled.setChecked(True)
            for name,check in self.columns_group_check_map.items():check.setChecked(name in summed.groups)
            self.columns_sum_min.setValue(summed.minimum);self.columns_sum_max.setValue(summed.maximum)
        self.implication_enabled.setChecked(bool(advanced.implications))
        if advanced.implications:
            rule=advanced.implications[0]
            self.implication_from.setCurrentIndex(self.implication_from.findData(rule.antecedent))
            self.implication_to.setCurrentIndex(self.implication_to.findData(rule.consequent))
            self.implication_from_min.setValue(rule.antecedent_minimum);self.implication_from_max.setValue(rule.antecedent_maximum)
            self.implication_to_min.setValue(rule.consequent_minimum);self.implication_to_max.setValue(rule.consequent_maximum)
        self.advanced_failures.setValue(advanced.allowed_failures)
        self._restore_reduction_rules(saved.get('reduction_rules',()))
        current_rules=json.loads(self.system.parameters).get('filter_spec',{}).get('reduction_rules',()) if self.system else ()
        rule_ids={row.get('rule_id') for row in current_rules}
        for key,sign in (('variants','V'),('x_count','X'),('two_count','2')):
            if self.filter_checks[key].isChecked() and f'count-values-{sign}' not in rule_ids:
                low,high=(tuple(saved.get(key,self.filter_defaults[key])))
                self.count_values[sign]=set(range(low,high+1));self.count_apply[sign].setChecked(True)
        for (sign,value),button in self.count_squares.items():button.setChecked(value in self.count_values[sign])
        self._refresh_count_profiles()
        self.quick_description.setText(f'Nivel {self.quick_level} / 10' if self.quick_level is not None else 'Condiciones personalizadas' if saved else 'Nivel 10 / 10')
        self.filter_feedback.setText('Primero pulsa Generar debajo del boleto.' if not self.system or (not self.system.bets and not saved) else '')
        self.configuring_filters=False;self.update_filter_controls()

    def configure_quick_conditions(self, level):
        """Populate filter controls; moving the slider never edits a saved system."""
        from quiniela_ai_studio.domain.filters import quick_conditions
        spec=quick_conditions(level)
        self.configuring_filters=True
        self.quick_level=level
        # Quick presets take the place of custom Cuenta/Racha conditions while
        # preserving their grid selections for when the user returns to Manual.
        self.automatic_profile_rules.clear()
        for button in (*self.count_apply.values(),*self.run_apply.values()):button.setChecked(False)
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
        self.count_values.clear();self.count_values.update({sign:set() for sign in ('V','X','2')})
        self.count_profiles_selected.clear();self.count_profile_active=False
        self.automatic_profile_rules.pop('Cuenta',None);self.random_reduction_metadata.pop('Cuenta',None)
        for button in self.count_apply.values():button.setChecked(False)
        for button in self.count_squares.values():button.setChecked(False)
        for button in self.count_profile_apply_buttons:button.setChecked(False)
        self.count_distance_apply.setChecked(False);self._refresh_count_profiles()
        while len(self.advanced_groups)>6:self.remove_advanced_group()
        for group in self.advanced_groups:
            group['enabled'].setChecked(False)
            for row in group['buttons']:
                for button in row:button.setChecked(False)
            group['minimum'].setValue(0);group['maximum'].setValue(14)
        self.advanced_relation_enabled.setChecked(False);self.advanced_relation_min.setValue(0);self.advanced_relation_max.setValue(28);self.advanced_failures.setValue(0)
        self.columns_sum_enabled.setChecked(False);self.columns_sum_min.setValue(0);self.columns_sum_max.setValue(112)
        for check in self.columns_group_check_map.values():check.setChecked(False)
        self.implication_enabled.setChecked(False);self.implication_from_min.setValue(0);self.implication_from_max.setValue(14);self.implication_to_min.setValue(0);self.implication_to_max.setValue(14)
        self.repeat_enabled.setChecked(False);self.repeat_reference.set_column('');self.repeat_minimum.setValue(0);self.repeat_maximum.setValue(14)
        for enabled,pattern,minimum,maximum in self.pattern_controls.values():enabled.setChecked(False);pattern.set_column('');minimum.setValue(0);maximum.setValue(14)
        self.frequency_matrix.set_column('');self.frequency_reference_list.clear();self.frequency_hits_min.setValue(0);self.frequency_hits_max.setValue(14);self.frequency_count_min.setValue(0);self.frequency_count_max.setValue(80)
        self.weight_sum_enabled.setChecked(False);self.weight_sum_min.setValue(0);self.weight_sum_max.setValue(14)
        self.weight_product_enabled.setChecked(False);self.weight_product_min.setValue(-1000);self.weight_product_max.setValue(0)
        self.filter_reference.set_column('')
        self.configuring_filters=False
        self.update_filter_controls();self.schedule_live_filter()

    def apply_filters_ui(self):
        try:
            self.apply_filters()
        except ValueError as exc:
            self.filter_feedback.setText(f'{exc} Puedes corregir los datos o desmarcar el filtro; no se han cambiado tus apuestas.')

    def filter_spec(self):
        if self.reduction_active.get(8,False) and self.filter_checks['coincidences'].isChecked() and not self.filter_reference.column():
            raise ValueError('Marca un signo 1/X/2 por partido en la matriz de Coincidencias, o desmarca ese filtro.')
        from quiniela_ai_studio.domain.filters import BasicFilters
        limits={key:(a.value(),b.value()) if self.filter_checks[key].isChecked() else self.filter_defaults[key] for key,(a,b) in self.filter_ranges.items()}
        for key,sign in (('variants','V'),('x_count','X'),('two_count','2')):
            if self.count_apply[sign].isChecked() and self.count_values[sign]:limits[key]=self.filter_defaults[key]
        run_controls=(('max_one_run',self.filter_max_one,'1'),('max_x_run',self.filter_max_x,'X'),('max_two_run',self.filter_max_two,'2'))
        run_limits={key:(control.value() if self.filter_checks[key].isChecked() and not (self.run_apply[sign].isChecked() and self.run_lengths[sign]) else 14)
                    for key,control,sign in run_controls}
        return BasicFilters(**limits,**run_limits,
                          reference=(self.filter_reference.column()
                                     if self.reduction_active.get(8,False)
                                     and self.filter_checks['coincidences'].isChecked() else ''),
                          advanced=self.advanced_spec(),reduction_rules=self.build_reduction_rules(),
                          reduction_tabs_enabled=tuple(index for index,active in self.reduction_active.items() if active),
                          quick_conditions_active=self.quick_level is not None)

    def _restore_reduction_rules(self, rows):
        from quiniela_ai_studio.domain.reduction_rules import rules_from_parameters
        self.repeat_enabled.setChecked(False);self.repeat_reference.set_column('');self.repeat_minimum.setValue(0);self.repeat_maximum.setValue(14)
        for enabled,pattern,minimum,maximum in self.pattern_controls.values():enabled.setChecked(False);pattern.set_column('');minimum.setValue(0);maximum.setValue(14)
        self.frequency_matrix.set_column('');self.frequency_reference_list.clear();self.frequency_hits_min.setValue(0);self.frequency_hits_max.setValue(14);self.frequency_count_min.setValue(0);self.frequency_count_max.setValue(80)
        self.weight_sum_enabled.setChecked(False);self.weight_sum_min.setValue(0);self.weight_sum_max.setValue(14)
        self.weight_product_enabled.setChecked(False);self.weight_product_min.setValue(-1000);self.weight_product_max.setValue(0)
        rules=rules_from_parameters(rows)
        self.automatic_profile_rules={};self.random_reduction_metadata={};self.run_generation_metadata={};self.legacy_streak_rules=[]
        self.fss_generation_metadata={}
        self.interruption_generation_metadata={}
        self.interruption_selected_pairs.clear();self.interruption_selected_totals.clear();self.interruption_selected_figures.clear()
        self.interruption_matrix.set_selected_pairs(set());self.interruption_apply.setChecked(False);self.distance_apply.setChecked(False)
        for button in self.interruption_total_buttons.values():button.setChecked(False)
        self._refresh_interruption_figure_list()
        for sign in ('1','X','2','V'):
            self.sign_distance_values[sign].clear()
            self.sign_distance_apply[sign].setChecked(False)
        for button in self.sign_distance_squares.values():button.setChecked(False)
        for sign in ('1','X','2','V'):
            self.fss_figure_values[sign].clear();self.fss_figure_totals[sign]=0
            self.fss_total_controls[sign].setValue(0);self.fss_figure_apply[sign].setChecked(False)
            self._refresh_fss_figure_list(sign)
        self.count_values.clear();self.count_values.update({sign:set() for sign in ('V','X','2')})
        self.count_profiles_selected.clear();self.count_profile_active=False
        for button in self.count_profile_apply_buttons:
            button.blockSignals(True);button.setChecked(False);button.blockSignals(False)
        self.automatic_profile_rules.pop('Cuenta',None)
        self.run_lengths.clear();self.run_lengths.update({sign:set() for sign in ('1','X','2','V')})
        for sign in ('1','X','2','V'):
            self.run_minmax_values[sign]={'minimum':None,'maximum':None}
            self.run_count_values[sign]={};self.run_figure_values[sign]={};self.run_figure_totals[sign].clear()
            for editor in self.run_minmax_widgets.get(sign,{}).values():
                for item in editor:item.clear()
            self.run_apply[sign].setChecked(False);self.run_figure_apply[sign].setChecked(False)
            for buttons in self.run_frequency_controls.get(sign,{}).values():
                for button in buttons.values():button.setChecked(False)
            for square in self.run_figure_total_squares.get(sign,{}).values():square.setChecked(False)
            self._refresh_streak_figures(sign)
        for button in (*self.count_apply.values(),):button.setChecked(False)
        for button in self.count_squares.values():button.setChecked(False)

        for rule in rules:
            if rule.tab_index==17:
                method=rule.generation_method
                if method in ('azar','automática'):
                    self.fss_generation_metadata.update(method=method,risk=rule.generation_risk,
                        seed=rule.generation_seed,seasons=rule.evidence_seasons,
                        sample_size=rule.evidence_sample_size,coverage=rule.evidence_coverage,
                        source=rule.evidence_source)
                    if method=='azar':
                        risk,seed,_summary=self.mode_azar_controls['FSSeguidos'];self._set_risk_value(risk,rule.generation_risk)
                        if rule.generation_seed is not None:seed.setValue(rule.generation_seed)
                    else:
                        risk,_summary,_calculate=self.mode_automatic_controls['FSSeguidos'];self._set_risk_value(risk,rule.generation_risk)
                        chosen=set(rule.evidence_seasons)
                        for season,square in self.history_season_squares.get('FSSeguidos',{}).items():square.setChecked(season in chosen)
            if rule.tab_index==18:
                method=rule.generation_method
                self.interruption_generation_metadata.update(method=method,risk=rule.generation_risk,
                    seed=rule.generation_seed,seasons=rule.evidence_seasons,sample_size=rule.evidence_sample_size,
                    coverage=rule.evidence_coverage,source=rule.evidence_source)
                if method=='azar':
                    risk,seed,_summary=self.mode_azar_controls['Interrupciones'];self._set_risk_value(risk,rule.generation_risk)
                    if rule.generation_seed is not None:seed.setValue(rule.generation_seed)
                elif method=='automática':
                    risk,_summary,_calculate=self.mode_automatic_controls['Interrupciones'];self._set_risk_value(risk,rule.generation_risk)
                    for season,square in self.history_season_squares.get('Interrupciones',{}).items():square.setChecked(season in set(rule.evidence_seasons))
            if rule.generation_method=='azar':
                title='Cuenta' if rule.rule_id.startswith('count-values-') else 'Racha' if rule.tab_index==1 else ''
                if title=='Cuenta':
                    self.random_reduction_metadata[title]={'method':'azar','seed':rule.generation_seed,'risk':rule.generation_risk}
                    risk,seed,_summary=self.mode_azar_controls[title]
                    risk.setCurrentText(rule.generation_risk)
                    if rule.generation_seed is not None:seed.setValue(rule.generation_seed)
                elif title=='Racha':
                    self.run_generation_metadata.update(method='azar',seed=rule.generation_seed,risk=rule.generation_risk)
                    risk,seed,_summary=self.mode_azar_controls['Racha'];self._set_risk_value(risk,rule.generation_risk)
                    if rule.generation_seed is not None:seed.setValue(rule.generation_seed)
            elif rule.generation_method=='automática' and rule.tab_index==1:
                self.run_generation_metadata.update(method='automática',risk=rule.generation_risk,
                    seasons=rule.evidence_seasons,sample_size=rule.evidence_sample_size,coverage=rule.evidence_coverage,
                    source=rule.evidence_source)
                self._set_risk_value(self.mode_automatic_controls['Racha'][0],rule.generation_risk)
                chosen_seasons=set(rule.evidence_seasons)
                for season,square in self.history_season_squares.get('Racha',{}).items():square.setChecked(season in chosen_seasons)

            if rule.kind=='allowed_count' and rule.sign in self.count_values:
                self.count_values[rule.sign]=set(rule.allowed_values);self.count_apply[rule.sign].setChecked(rule.active)
            elif rule.kind=='allowed_profile' and rule.profile_kind=='counts':
                self.count_profiles_selected=set(rule.allowed_profiles)
                self.count_profile_active=rule.active
                for button in self.count_profile_apply_buttons:
                    button.blockSignals(True);button.setChecked(rule.active);button.blockSignals(False)
                if rule.rule_id!='count-joint-profiles':self.automatic_profile_rules['Cuenta']=rule
                for variants,x_count,two_count in rule.allowed_profiles:
                    self.count_values['V'].add(variants);self.count_values['X'].add(x_count);self.count_values['2'].add(two_count)
                for sign in ('V','X','2'):self.count_apply[sign].setChecked(True)
                risk,summary,_calculate=self.mode_automatic_controls['Cuenta'];risk.setCurrentText(rule.generation_risk)
                for season,square in self.history_season_squares.get('Cuenta',{}).items():square.setChecked(season in set(rule.evidence_seasons))
                summary.setText(f'{rule.evidence_sample_size} resultados finales · {len(rule.allowed_profiles)} perfiles conjuntos · objetivo muestral {rule.evidence_coverage:.0%}. No es una predicción.')
            elif rule.kind=='allowed_run_length' and rule.tab_index==1:
                self.legacy_streak_rules.append(rule);self.run_lengths[rule.sign]=set(rule.allowed_values)
                self.run_apply[rule.sign].setChecked(rule.active)
                self.run_minmax_values[rule.sign]={'minimum':min(rule.allowed_values),'maximum':max(rule.allowed_values)}
            elif rule.kind=='run_frequency' and rule.tab_index==1:
                self.legacy_streak_rules.append(rule);self.run_apply[rule.sign].setChecked(rule.active)
                for length,minimum,maximum in rule.run_limits:
                    self.run_count_values[rule.sign][length]=set(range(minimum,maximum+1))
            elif rule.kind=='allowed_profile' and rule.profile_kind=='streaks':
                self.automatic_profile_rules['Racha']=rule
                self.run_generation_metadata.update(method='automática',risk=rule.generation_risk,
                    seasons=rule.evidence_seasons,sample_size=rule.evidence_sample_size,
                    coverage=rule.evidence_coverage,source=rule.evidence_source)
                for index,sign in enumerate(('1','X','2','V')):
                    longest={profile[index] for profile in rule.allowed_profiles}
                    self.run_minmax_values[sign]={'minimum':min(longest),'maximum':max(longest)}
                    figures_by_total={}
                    for length in range(2,15):
                        offset=4+index*14+length-1
                        self.run_count_values[sign][length]={profile[offset] for profile in rule.allowed_profiles}
                    for profile in rule.allowed_profiles:
                        offset=4+index*14
                        parts=tuple(length for length in range(14,0,-1)
                                    for _ in range(profile[offset+length-1]))
                        total=sum(parts)
                        figures_by_total.setdefault(total,set()).add('-'.join(map(str,parts)))
                    self.run_figure_values[sign]=figures_by_total
                    self.run_figure_totals[sign]=set(figures_by_total)
                    self.run_apply[sign].setChecked(True)
                self._set_risk_value(self.mode_automatic_controls['Racha'][0],rule.generation_risk)
                chosen_seasons=set(rule.evidence_seasons)
                for season,square in self.history_season_squares.get('Racha',{}).items():square.setChecked(season in chosen_seasons)
                self.mode_automatic_controls['Racha'][1].setText(f'{rule.evidence_sample_size} resultados finales · {len(rule.allowed_profiles)} perfiles conjuntos · objetivo muestral {rule.evidence_coverage:.0%}. No es una predicción.')
            elif rule.kind=='longest_run' and rule.tab_index==1:
                minimum_enabled=True if rule.run_minimum_enabled is None else rule.run_minimum_enabled
                maximum_enabled=True if rule.run_maximum_enabled is None else rule.run_maximum_enabled
                self.run_minmax_values[rule.sign]={
                    'minimum':int(rule.minimum) if minimum_enabled else None,
                    'maximum':int(rule.maximum) if maximum_enabled else None,
                }
                self.run_apply[rule.sign].setChecked(rule.active)
            elif rule.kind=='allowed_run_count' and rule.tab_index==1:
                self.run_count_values[rule.sign][rule.run_length]=set(rule.allowed_values)
                self.run_apply[rule.sign].setChecked(rule.active)
            elif rule.kind=='allowed_run_figure' and rule.tab_index==1:
                self.run_figure_totals[rule.sign].add(int(rule.rule_id.rsplit('-',1)[-1]))
                total=int(rule.rule_id.rsplit('-',1)[-1])
                self.run_figure_values[rule.sign][total]=set(rule.allowed_figures)
                self.run_figure_apply[rule.sign].setChecked(rule.active)
            elif rule.kind=='allowed_run_figure' and rule.tab_index==17:
                sign=rule.sign;total=int(rule.run_length)
                self.fss_figure_totals[sign]=total;self.fss_total_controls[sign].setValue(total)
                if rule.rule_id.startswith('fss-figure-'):
                    self.fss_figure_values[sign][total]=set(rule.allowed_figures)
                    if rule.active:self.fss_figure_apply[sign].setChecked(True)
                elif rule.rule_id.startswith('fss-current-'):
                    self.fss_figure_apply[sign].setChecked(False)
            elif rule.kind=='allowed_interruption_profile' and rule.tab_index==18:
                self.interruption_selected_pairs=set(tuple(pair) for pair in rule.allowed_profiles)
                self.interruption_matrix.set_selected_pairs(self.interruption_selected_pairs)
                self.interruption_apply.setChecked(rule.active)
            elif rule.kind=='allowed_interruption_total' and rule.tab_index==18:
                self.interruption_selected_totals.update(rule.allowed_values)
            elif rule.kind=='allowed_interruption_figure' and rule.tab_index==18:
                self.interruption_selected_totals.add(rule.run_length)
                self.interruption_selected_figures.update((rule.run_length,figure) for figure in rule.allowed_figures)
                self.distance_apply.setChecked(self.distance_apply.isChecked() or rule.active)
            elif rule.kind=='allowed_sign_distance' and rule.tab_index==18:
                self.sign_distance_values[rule.sign]=set(rule.allowed_values)
                self.sign_distance_apply[rule.sign].setChecked(rule.active)
                for value in rule.allowed_values:
                    self.sign_distance_squares[(rule.sign,value)].setChecked(True)
            elif rule.kind=='reference_hits' and rule.rule_id=='manual-repeat':
                self.repeat_enabled.setChecked(True);self.repeat_reference.set_column(rule.reference);self.repeat_minimum.setValue(int(rule.minimum));self.repeat_maximum.setValue(int(rule.maximum))
            elif rule.kind=='pattern_occurrences':
                size=next((size for size in self.pattern_controls if rule.rule_id==f'manual-pattern-{size}'),None)
                if size is not None:
                    enabled,pattern,minimum,maximum=self.pattern_controls[size]
                    enabled.setChecked(True);pattern.set_column(rule.patterns[0]);minimum.setValue(int(rule.minimum));maximum.setValue(int(rule.maximum))
            elif rule.kind=='hit_frequency' and rule.rule_id=='manual-hit-frequency':
                self.frequency_reference_list.addItems(rule.references);self.frequency_hits_min.setValue(rule.reference_minimum);self.frequency_hits_max.setValue(rule.reference_maximum);self.frequency_count_min.setValue(int(rule.minimum));self.frequency_count_max.setValue(int(rule.maximum))
            elif rule.rule_id in ('manual-weight-sum','manual-weight-logp'):
                enabled,minimum,maximum=(self.weight_sum_enabled,self.weight_sum_min,self.weight_sum_max) if rule.rule_id=='manual-weight-sum' else (self.weight_product_enabled,self.weight_product_min,self.weight_product_max)
                enabled.setChecked(True);minimum.setValue(rule.minimum);maximum.setValue(rule.maximum)

        for (sign,value),button in self.count_squares.items():button.setChecked(value in self.count_values[sign])
        for sign in ('1','X','2','V'):
            self._sync_streak_mode_views(sign)
            self._refresh_fss_figure_list(sign)
        if self.run_generation_metadata.get('method')=='automática':
            self.mode_tabs['SSeguidos'].setCurrentWidget(self.run_mode_pages['Automática'])
        elif self.run_generation_metadata.get('method')=='azar':
            self.mode_tabs['SSeguidos'].setCurrentWidget(self.run_mode_pages['Azar'])
        if self.fss_generation_metadata.get('method')=='automática':
            self.mode_tabs['FSSeguidos'].setCurrentWidget(self.fss_mode_pages['Automática'])
        elif self.fss_generation_metadata.get('method')=='azar':
            self.mode_tabs['FSSeguidos'].setCurrentWidget(self.fss_mode_pages['Azar'])
        if self.interruption_generation_metadata.get('method')=='automática':
            self.mode_tabs['Interrupciones'].setCurrentWidget(self.interruption_mode_pages['Automática'])
        elif self.interruption_generation_metadata.get('method')=='azar':
            self.mode_tabs['Interrupciones'].setCurrentWidget(self.interruption_mode_pages['Azar'])
        self._refresh_interruption_figure_list()
        for total,button in self.interruption_total_buttons.items():button.setChecked(total in self.interruption_selected_totals)
        self.update_streak_base_limits()

        by_id={rule.rule_id:rule for rule in rules}
        repetition=by_id.get('manual-repeat')
        if repetition:
            self.repeat_enabled.setChecked(True);self.repeat_reference.set_column(repetition.reference);self.repeat_minimum.setValue(int(repetition.minimum));self.repeat_maximum.setValue(int(repetition.maximum))
        for size,(enabled,pattern,minimum,maximum) in self.pattern_controls.items():
            rule=by_id.get(f'manual-pattern-{size}')
            if rule:enabled.setChecked(True);pattern.set_column(rule.patterns[0]);minimum.setValue(int(rule.minimum));maximum.setValue(int(rule.maximum))
        frequency=by_id.get('manual-hit-frequency')
        if frequency:
            self.frequency_reference_list.addItems(frequency.references);self.frequency_hits_min.setValue(frequency.reference_minimum);self.frequency_hits_max.setValue(frequency.reference_maximum);self.frequency_count_min.setValue(int(frequency.minimum));self.frequency_count_max.setValue(int(frequency.maximum))
        for rule_id,enabled,minimum,maximum in (('manual-weight-sum',self.weight_sum_enabled,self.weight_sum_min,self.weight_sum_max),('manual-weight-logp',self.weight_product_enabled,self.weight_product_min,self.weight_product_max)):
            rule=by_id.get(rule_id)
            if rule:enabled.setChecked(True);minimum.setValue(rule.minimum);maximum.setValue(rule.maximum)

    def apply_filters(self):
        if not self.system:raise ValueError('Abre primero una quiniela.')
        self.filter_timer.stop();self.filter_epoch+=1
        if self.filter_job:self.filter_job.cancel_event.set()
        spec=self.filter_spec()
        candidates=self.service.origin_bets(self.system)[1]
        before=sum(b.quantity for b in candidates)
        bets=spec.apply(candidates)
        parameters=json.loads(self.system.parameters)
        serialized_spec=json.loads(json.dumps(spec.parameters()))
        from quiniela_ai_studio.domain.advanced_conditions import AdvancedConditions
        from quiniela_ai_studio.domain.filters import BasicFilters
        neutral_spec=json.loads(json.dumps(BasicFilters(reduction_tabs_enabled=(),
            advanced=AdvancedConditions(enabled_tabs=())).parameters()))
        is_initial_noop=(parameters.get('filter_spec') is None and self.quick_level is None
                         and serialized_spec==neutral_spec)
        if (not is_initial_noop and (bets!=self.system.bets or parameters.get('filter_spec')!=serialized_spec
                or parameters.get('quick_level')!=self.quick_level)):
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
            if hasattr(self,'advanced_feedback'):
                before=sum(b.quantity for b in candidates);after=sum(b.quantity for b in bets)
                detail=''
                if spec.advanced.enabled:
                    failed=spec.advanced.failure_counts(candidates)
                    detail=' Condiciones incumplidas en el desarrollo de origen (los recuentos pueden solaparse): '+'; '.join(f'{name}: {count:,}' for name,count in failed)+'.'
                self.advanced_feedback.setText(f'El desarrollo conserva {after:,} de {before:,} apuestas.{detail} El coste se actualiza en la franja inferior.')
        except ValueError as exc:
            self.filter_feedback.setText(str(exc))

    def live_filter_failed(self,context,message):
        if not self.close_pending and context[0]==self.filter_epoch:
            self.filter_feedback.setText(message)
            if hasattr(self,'advanced_feedback'):self.advanced_feedback.setText(message)

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
        if (self.data_worker and self.data_worker.isRunning()) or (self.worker and self.worker.isRunning()):
            raise ValueError('Espera o cancela la operación actual.')
        cents=int(Decimal(self.budget.cleanText().replace(',','.'))*100)
        source=self.system
        bets,base,config,frozen,spec=self.service.optimization_input(source,cents,
            objective=self.portfolio_objective.currentData(),seed=self.portfolio_seed.value(),max_seconds=self.portfolio_time.value(),
            universe_scope=self.portfolio_scope.currentData(),min_per_pleno=self.portfolio_channel.currentData(),
            include_pleno_probability=self.portfolio_pleno_model.isChecked())
        from quiniela_ai_studio.domain.portfolio import optimize_portfolio
        audit=dict(run_id=uuid.uuid4().hex,created_at=utcnow(),round_key=source.round_key,input_hash=source.hash,
            input_revision=source.revision,base=list(base),filter_spec=spec.parameters(),sources=[asdict(s) for s in frozen.snapshots],
            config=asdict(config),initial_quantity=sum(b.quantity for b in bets))
        def operation(cancel,status):
            admitted=set(spec.apply(bets,cancel))
            def progress(done,total):
                if done==total or done%max(1,total//100)==0:status(f'Optimización: {done:,}/{total:,} · cálculo real; permite cancelar')
            result=optimize_portfolio(bets,base,config,frozen.snapshot('sport'),public=frozen.snapshot('public'),eligible=lambda b:b in admitted,cancelled=cancel,progress=progress)
            result.report.update(audit,status='completed')
            return result
        self.portfolio_audit=audit
        self.portfolio_started=time.monotonic()
        self.portfolio_audit_finished=False
        self.repository.record_event('optimization_started',dict(audit,status='started'))
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
        self.published_scrutiny=None
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
        self.scrutiny_splitter=QSplitter(Qt.Orientation.Vertical);self.scrutiny_splitter.setChildrenCollapsible(False)
        upper=QWidget();upper_layout=QVBoxLayout(upper);upper_layout.setContentsMargins(0,0,0,0)
        lower=QWidget();lower_layout=QVBoxLayout(lower);lower_layout.setContentsMargins(0,0,0,0)
        upper.setMinimumHeight(80);lower.setMinimumHeight(100)
        self.scrutiny_splitter.addWidget(upper);self.scrutiny_splitter.addWidget(lower)
        self.scrutiny_splitter.setStretchFactor(0,0);self.scrutiny_splitter.setStretchFactor(1,1)
        layout.addWidget(self.scrutiny_splitter,1)
        self.live_view,self.live_model=self.table(('Partido','Marcador','Resultado','Tu signo','Acierto / fallo','Estado'),upper_layout)
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
        upper_layout.addWidget(self.manual_container);self.manual_container.hide()
        self.prize_card=QFrame();self.prize_card.setObjectName('prizeCard')
        prize_layout=QHBoxLayout(self.prize_card);prize_layout.setContentsMargins(12,7,12,7);prize_layout.setSpacing(18)
        self.prize_layout=prize_layout
        prize_highlight=QVBoxLayout();prize_highlight.setSpacing(1)
        self.prize_headline=QLabel('✦ ¡Hay premio en tu quiniela!');self.prize_headline.setObjectName('prizeHeadline')
        self.prize_total=QLabel();self.prize_total.setObjectName('prizeTotal')
        self.prize_fine_print=QLabel('Importe calculado para las apuestas guardadas. Comprueba el boleto validado antes de cobrar.')
        self.prize_fine_print.setObjectName('prizeFinePrint');self.prize_fine_print.setWordWrap(True)
        prize_highlight.addWidget(self.prize_headline);prize_highlight.addWidget(self.prize_total)
        prize_highlight.addWidget(self.prize_fine_print)
        prize_layout.addLayout(prize_highlight,1)
        prize_grid=QGridLayout();prize_grid.setContentsMargins(0,0,0,0);prize_grid.setHorizontalSpacing(12);prize_grid.setVerticalSpacing(1)
        for column,caption in enumerate(('Categoría','Apuestas','Por apuesta','Subtotal')):
            label=QLabel(caption);label.setObjectName('prizeCategoryHeading')
            prize_grid.addWidget(label,0,column)
        self.prize_category_rows={}
        captions={15:'Pleno al 15',14:'14 aciertos',13:'13 aciertos',12:'12 aciertos',11:'11 aciertos',10:'10 aciertos'}
        for row,category in enumerate((15,14,13,12,11,10),1):
            labels=[QLabel(captions[category]),QLabel(),QLabel(),QLabel()]
            for column,label in enumerate(labels):
                label.setObjectName('prizeCategoryValue');prize_grid.addWidget(label,row,column)
            self.prize_category_rows[category]=labels
        self.prize_grid_widget=QWidget();self.prize_grid_widget.setLayout(prize_grid)
        prize_layout.addWidget(self.prize_grid_widget,0)
        self.prize_detail_card=QFrame();self.prize_detail_card.setObjectName('prizeBreakdownCard')
        self.prize_detail_card.setMinimumHeight(125)
        detail_layout=QGridLayout(self.prize_detail_card)
        detail_layout.setContentsMargins(8,4,8,4)
        detail_layout.setHorizontalSpacing(8);detail_layout.setVerticalSpacing(0)
        for caption,column,span in (('OFICIALES',0,3),('TUS PREMIOS',3,2)):
            label=QLabel(caption);label.setObjectName('prizeTableGroup')
            detail_layout.addWidget(label,0,column,1,span)
        for column,caption in enumerate(('Aciertos','Acertantes','Premio/u.','Apuestas','Importe')):
            label=QLabel(caption);label.setObjectName('prizeTableHeader')
            detail_layout.addWidget(label,1,column)
        self.prize_detail_rows={}
        for row,category in enumerate((15,14,13,12,11,10),2):
            labels=[QLabel('Pleno 15' if category==15 else str(category))]+[QLabel() for _ in range(4)]
            for column,label in enumerate(labels):
                label.setObjectName('prizeTableOwn' if column==4 else 'prizeTableValue')
                detail_layout.addWidget(label,row,column)
            self.prize_detail_rows[category]=labels
        total_label=QLabel('TOTAL');total_label.setObjectName('prizeTableGroup')
        detail_layout.addWidget(total_label,8,3)
        self.prize_detail_total=QLabel();self.prize_detail_total.setObjectName('prizeTableTotal')
        detail_layout.addWidget(self.prize_detail_total,8,4)
        self.prize_cards_layout=QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.prize_cards_layout.setContentsMargins(0,0,0,0);self.prize_cards_layout.setSpacing(8)
        self.prize_cards_layout.addWidget(self.prize_card,1)
        self.prize_cards_layout.addWidget(self.prize_detail_card,1)
        self.prize_card.hide();self.prize_detail_card.hide()
        lower_layout.addLayout(self.prize_cards_layout)
        self.prize_notice=QLabel('Premios pendientes de escrutinio publicado.');self.prize_notice.setObjectName('muted')
        self.prize_cache_error=''
        self.prize_notice.setWordWrap(True);lower_layout.addWidget(self.prize_notice)
        self.eval_summary=QLabel('Abre una quiniela con apuestas para ver tus aciertos.');self.eval_summary.setWordWrap(True);self.eval_summary.setMinimumHeight(48);lower_layout.addWidget(self.eval_summary)
        self.eval_view,self.eval_model=self.table(('Apuesta','Pleno','Copias','Aciertos','Fallos','Pendientes','Máximo','Pleno ahora'),lower_layout)
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
        if manual:self.clear_scrutiny_awards()
        self.ensure_live_updates()
        if manual:self.schedule_manual_evaluation()
        elif not self.show_cached_scrutiny():
            if self.live_matches:self.evaluate_live()
            else:
                self.prize_card.hide();self.prize_notice.show()
                self.prize_notice.setText('Premios pendientes de escrutinio publicado.')
        QTimer.singleShot(0,self.fit_scrutiny_tables)

    def _render_prize_card(self,outcome,source='',scrutiny=None):
        """Show a prize only when definitive published amounts are available."""
        total=outcome['prize_cents']
        self.prize_card.setVisible(total is not None and total>0)
        self.prize_detail_card.setVisible(total is not None and scrutiny is not None)
        self.prize_notice.setVisible(total is None or total==0)
        if self.navigation.currentRow()==4:QTimer.singleShot(0,self.fit_scrutiny_tables)
        if total is None:
            message='Premios pendientes de escrutinio publicado.'
            if self.prize_cache_error:message+=f' El PRE guardado no se ha usado: {self.prize_cache_error}'
            self.prize_notice.setText(message)
            return
        if total==0:
            self.prize_notice.setText('Escrutinio publicado · sin premios en estas apuestas guardadas.')
            return
        self.prize_total.setText(prize_money(total))
        self.prize_total.setAccessibleName(f'Premio total calculado: {prize_money(total)}')
        self.prize_fine_print.setText(
            f'{source} · Importe calculado para las apuestas guardadas. '
            'Comprueba el boleto validado antes de cobrar.'
        )
        for payout in outcome['payouts']:
            labels=self.prize_category_rows[payout['category']]
            visible=payout['bets']>0
            for label in labels:label.setVisible(visible)
            labels[1].setText(str(payout['bets']))
            labels[2].setText(prize_money(payout['unit_cents']))
            labels[3].setText(prize_money(payout['subtotal_cents']))

    def _render_prize_detail(self,outcome,scrutiny):
        """Show every published category beside this system's matching bets."""
        if outcome['prize_cents'] is None or scrutiny is None:
            self.prize_detail_card.hide()
            return
        winners={int(key):value for key,value in scrutiny.get('winners',{}).items()}
        for payout in outcome['payouts']:
            category=payout['category'];labels=self.prize_detail_rows[category]
            count=winners.get(category)
            labels[1].setText(f'{count:,}'.replace(',','.') if type(count) is int else '—')
            labels[2].setText(prize_money(payout['unit_cents']))
            labels[3].setText(str(payout['bets']))
            labels[4].setText(prize_money(payout['subtotal_cents']))
        self.prize_detail_total.setText(prize_money(outcome['prize_cents']))
        self.prize_detail_card.show()

    def render_scrutiny(self,outcome,actual_pleno,pleno_final,source='',scrutiny=None):
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
        self._render_prize_card(outcome,source,scrutiny)
        self._render_prize_detail(outcome,scrutiny)
        self.eval_summary.setText(
            f'{outcome["known"]} de 14 resultados disponibles · mejor apuesta: {best} aciertos · '
            f'{outcome["counts"][15]} Plenos confirmados. Marcadores en juego pueden cambiar; sin premios calculados.'
            if outcome['prize_cents'] is None else
            f'Escrutinio definitivo · mejor apuesta: {best} aciertos · '
            f'{sum(outcome["counts"][category] for category in (10,11,12,13,14))} '
            'apuestas con al menos 10 aciertos. El Pleno es una categoría adicional.'
        )

    def evaluate(self,prizes=None,source='PRE seleccionado',scrutiny=None):
        if not self.system or not self.system.bets:raise ValueError('Abre una quiniela con apuestas preparadas.')
        result=self.result_input.text().upper();pleno=self.result_pleno.text().upper()
        outcome=engine.evaluate(self.system.bets,result,pleno,finalized=(self.final_check.isChecked(),)*14,
                                prizes=prizes,official=prizes is not None)
        self.render_scrutiny(outcome,pleno,self.final_check.isChecked(),source,scrutiny)

    def read_scrutiny(self):
        path,_=QFileDialog.getOpenFileName(self,'Seleccionar PRE de esta temporada',filter='WIN1X2 (PRE*.txt Pre*.txt)')
        if not path:return
        if Path(path).name.casefold()!=f'pre{self.frozen_round().season}.txt'.casefold():
            raise ValueError('La temporada del fichero no coincide con la seleccionada.')
        scrutiny=scrutiny_from_cache(Path(path).parent,self.frozen_round())
        if not scrutiny:raise ValueError('No hay escrutinio definitivo para esta jornada.')
        self.manual_mode.setChecked(True)
        self.set_manual_results(scrutiny['result'],scrutiny['pleno']);self.final_check.setChecked(True)
        self.manual_eval_timer.stop();self.evaluate(scrutiny['prizes'],scrutiny=scrutiny)

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
                    any(job and job.isRunning() for job in (self.worker,self.data_worker,self.filter_job,self.athena_job)))

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
        path,_=QFileDialog.getSaveFileName(self,f'Guardar apuestas de {system.name}',self.export_filename(system,'txt'),'TXT clásico · 14 signos + Pleno (*.txt)')
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
        history_button=self.button('Añadir resultados históricos CSV/JSON…',lambda:self.safe(self.import_reduction_history),layout)
        history_button.setObjectName('historyImportButton')
        history_note=QLabel('El histórico incluido se carga automáticamente. Esta opción solo sirve para añadir resultados finales propios.')
        history_note.setWordWrap(True);layout.addWidget(history_note)
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
        self.portfolio_cancel.setEnabled(bool(self.data_worker and self.data_worker.isRunning() and self.data_kind=='portfolio'))

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
        if self.data_kind=='portfolio':self.portfolio_summary.setText(message)

    def background_error(self,message):
        if self.data_kind == 'import':
            self._startup_new_pending = False
        if self.data_kind=='portfolio' and not getattr(self,'portfolio_audit_finished',True):
            cancelled=bool(self.data_worker and self.data_worker.cancel_event.is_set())
            self.repository.record_event('optimization_run',dict(self.portfolio_audit,
                status='cancelled' if cancelled else 'failed',finished_at=utcnow(),
                elapsed_seconds=time.monotonic()-self.portfolio_started,error=message))
            self.portfolio_audit_finished=True
        self.background_status(message)
        if not self.close_pending and not (self.data_worker and self.data_worker.cancel_event.is_set()):
            QMessageBox.warning(self,'Datos anteriores conservados',message)

    def cancel_data(self):
        if self.data_worker:
            self.data_worker.cancel_event.set()
            self.background_status('Cancelando cálculo… La quiniela anterior se conserva.' if self.data_kind=='portfolio' else 'Cancelando… Se espera a que termine la petición en curso (máximo 30 s).')

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
        if self.data_kind=='portfolio':
            self.repository.record_event('optimization_run',result.report)
            self.portfolio_audit_finished=True
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
                fresh_session = self._startup_new_pending and self.system is None
                self._startup_new_pending = False
                if not fresh_session and not self.confirm_data(prepared):
                    self.background_status('Importación descartada; se conservan los datos anteriores.');return
                self.repository.import_rounds(prepared.rounds,prepared.directory)
                preferred=prepared.preferred if fresh_session or self.round.season=='DEMO' else self.round.key
                previous=self.system
                self.load_rounds(preferred)
                if previous and previous.round_key==self.round.key:self.set_system(self.repository.load(previous.system_id))
                self.background_status(f'{len(prepared.rounds)} jornadas importadas. '+ ('\n'.join(prepared.warnings) if prepared.warnings else 'Datos disponibles sin conexión.'))
                if fresh_session:
                    self.start_new_current(download=False)
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

    def show_cached_scrutiny(self):
        """Use a matching definitive PRE or a previously verified published page."""
        if self.manual_mode.isChecked() or not self.system or not self.system.bets:
            self.clear_scrutiny_awards()
            return False
        context=self.frozen_round()
        directory_name=self.repository.setting('data_directory')
        scrutiny=None;source='PRE guardado';self.prize_cache_error=''
        if directory_name:
            directory=Path(directory_name)
            try:
                expected=f'pre{context.season}.txt'.casefold()
                if directory.is_dir() and any(path.name.casefold()==expected for path in directory.iterdir()):
                    scrutiny=scrutiny_from_cache(directory,context)
                    if not scrutiny:self.prize_cache_error='El escrutinio de esta jornada aún no es definitivo.'
            except (OSError,ValueError) as exc:
                self.prize_cache_error=str(exc)
        if not scrutiny:
            cached=self.repository.setting('published_scrutiny:'+context.key) or {}
            fixture=[[m.home_id,m.away_id] for m in context.matches]
            if cached.get('fixture')==fixture and cached.get('nominal_date')==context.nominal_date:
                candidate=cached.get('scrutiny') or {}
                if (candidate.get('round_no')==context.number and
                    isinstance(candidate.get('result'),str) and len(candidate['result'])==14 and
                    isinstance(candidate.get('pleno'),str) and len(candidate['pleno'])==2 and
                    {int(key) for key in candidate.get('prizes',{})}=={10,11,12,13,14,15}):
                    scrutiny=candidate
                    scrutiny['prizes']={int(key):value for key,value in scrutiny['prizes'].items()}
                    source=candidate.get('source','Escrutinio publicado guardado')
            if not scrutiny:
                self.clear_scrutiny_awards()
                self.prize_notice.setText(self.prize_cache_error or 'Premios pendientes de escrutinio publicado.')
                return False
        self.prize_cache_error=''
        self.published_scrutiny=scrutiny
        outcome=engine.evaluate(self.system.bets,scrutiny['result'],scrutiny['pleno'],
                                finalized=(True,)*14,prizes=scrutiny['prizes'],official=True)
        self.render_scrutiny(outcome,scrutiny['pleno'],True,source,scrutiny)
        self.live_pleno_summary.setText(f'Pleno publicado: {scrutiny["pleno"][0]}–{scrutiny["pleno"][1]}')
        return True

    def refresh_scrutiny_page(self):
        """Restore cached awards or the current live comparison on page entry."""
        if self.live_matches:
            self.evaluate_live()
        else:
            self.show_cached_scrutiny()

    def maybe_fetch_published_scrutiny(self):
        """Look up published payouts in a worker after all scores are final."""
        if (self.close_pending or self.manual_mode.isChecked() or self.published_scrutiny or
            self.published_worker is not None or not self.system or not self.system.bets or
            self.navigation.currentRow()!=4 or len(self.live_matches or ())!=15 or
            not all(match.final and (match.sign if match.number<15 else match.pleno) for match in self.live_matches)):
            return
        context=self.frozen_round()
        now=time.monotonic()
        if now-self.published_attempts.get(context.key,-10000)<600:return
        self.published_attempts[context.key]=now
        job=DataTask(lambda cancel,status:fetch_published_scrutiny(context),self)
        self.published_worker=job
        self.prize_notice.setText('Consultando el escrutinio publicado…')
        job.completed.connect(lambda result:self.published_received(context,result))
        job.failed.connect(lambda message:self.published_failed(context,message))
        job.finished.connect(lambda:self.published_finished(job))
        job.start()

    def published_received(self,context,scrutiny):
        if self.close_pending or self.published_worker.cancel_event.is_set():return
        self.repository.set_setting('published_scrutiny:'+context.key,{
            'fixture':[[m.home_id,m.away_id] for m in context.matches],
            'nominal_date':context.nominal_date,'scrutiny':scrutiny})
        if (self.round.key==context.key and not self.manual_mode.isChecked() and
            self.system and self.system.bets):
            self.show_cached_scrutiny()

    def published_failed(self,context,message):
        if not self.close_pending and self.round.key==context.key and not self.published_scrutiny:
            self.prize_notice.setText('Premios aún sin confirmar en la fuente pública. '+message)

    def published_finished(self,job):
        if self.published_worker is job:self.published_worker=None
        job.deleteLater()
        if self.close_pending:self.close()

    def read_cached_scrutiny(self):
        directory=self.repository.setting('data_directory')
        if not directory:raise ValueError('Importa o descarga primero los datos de WIN1X2.')
        scrutiny=scrutiny_from_cache(Path(directory),self.frozen_round())
        if not scrutiny:raise ValueError('Todavía no hay escrutinio definitivo guardado para esta jornada.')
        self.manual_mode.setChecked(True)
        self.set_manual_results(scrutiny['result'],scrutiny['pleno']);self.final_check.setChecked(True)
        self.manual_eval_timer.stop();self.evaluate(scrutiny['prizes'],'PRE guardado',scrutiny)

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
        if not self.live_matches:
            self.show_live_waiting(context)
        cached=self.repository.setting('live:'+context.key) or {}
        previous_matches=cached.get('matches',())
        preferred_source=(
            'ESPN (alternativa)' if any(match.get('source')=='ESPN (alternativa)' for match in previous_matches)
            else previous_matches[0].get('source','') if previous_matches else ''
        )
        job=DataTask(lambda cancel,status:live_for_round(context,preferred_source=preferred_source),self);self.live_worker=job
        self.live_status.setText('Buscando el marcador de esta jornada…')
        job.completed.connect(lambda matches:self.live_received(context,matches))
        job.failed.connect(lambda message:self.live_error(context,message))
        job.finished.connect(lambda:self.live_finished(job))
        job.start()

    def show_live_waiting(self,context):
        """Show the fixture list while no downloaded or cached scores exist."""
        rows=[]
        for match in context.matches:
            state=self.waiting_marker_status(match.kickoff)
            rows.append((f'{match.number:02} · {match.home} – {match.away}', '—', '—', '—', 'Sin comprobar', state))
        self.live_model.update_rows(rows)
        self.live_pleno_summary.setText('Pleno actual: sin resultado recibido')
        self.eval_summary.setText('Faltan los datos del marcador. Los partidos con horario pasado aparecen como “sin resultado”, no como pendientes.')

    @staticmethod
    def waiting_marker_status(kickoff,now=None):
        """Describe schedule time without claiming a match has started or ended."""
        if not kickoff:
            return 'Sin datos del marcador'
        scheduled=None
        for pattern in ('%d/%m/%Y%H:%M','%d/%m/%Y %H:%M','%Y-%m-%dT%H:%M:%S%z','%Y-%m-%dT%H:%M:%S','%Y-%m-%d %H:%M:%S'):
            try:
                scheduled=datetime.strptime(kickoff,pattern)
                break
            except ValueError:
                continue
        if scheduled is None:
            try:scheduled=datetime.fromisoformat(kickoff)
            except ValueError:return 'Sin datos del marcador'
        if scheduled.tzinfo is None:scheduled=scheduled.astimezone()
        current=now or datetime.now().astimezone()
        if current.tzinfo is None:current=current.astimezone()
        caption=scheduled.astimezone().strftime('%d/%m %H:%M')
        if scheduled>current:
            return f'Por comenzar · {caption}'
        return f'Sin resultado · horario {caption}'

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
            friendly=('No hay conexión con Dataradar ni con la fuente alternativa ESPN.'
                      if 'No se pudo conectar con el marcador público' in message else message)
            if self.live_matches:
                self.live_status.setText(f'{friendly} Se conserva el marcador guardado y se volverá a intentar.')
            else:
                self.live_status.setText(
                    f'{friendly} No se ha recibido ningún resultado. Los horarios pasados aparecen como '
                    '«Sin resultado»; la consulta volverá a intentarse mientras el marcador automático esté activado.'
                )

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
        sources=', '.join(dict.fromkeys(m.source for m in self.live_matches if m.source))
        self.live_status.setText(f'{"Marcador guardado" if cached else "Última consulta"}: {queried} · {sources or "fuente desconocida"}')
        self.evaluate_live()

    def display_match_comparison(self,*_):
        published=self.published_scrutiny if not self.manual_mode.isChecked() else None
        if not published and not self.manual_mode.isChecked() and not self.live_matches:return
        index=self.eval_view.currentIndex().row()
        chosen=self.eval_model.rows[index if 0<=index<len(self.eval_model.rows) else 0] if self.eval_model.rows else None
        rows=[]
        matches=self.frozen_round().matches if published or self.manual_mode.isChecked() else self.live_matches
        for m in matches:
            number=m.number
            if published:
                actual=published['pleno'] if number==15 else published['result'][number-1]
                live=self.live_matches[number-1] if self.live_matches else None
                live_sign=(live.pleno if number==15 else live.sign) if live else None
                score=live.score if live_sign==actual else '—'
                status='Escrutinio publicado'
            elif self.manual_mode.isChecked():
                actual=(self.result_pleno.text() or '—') if number==15 else self.result_input.text()[number-1]
                score='—';status='Resultado introducido' if actual not in ('—','-') else 'Pendiente'
            else:
                actual=(m.pleno or '—') if number==15 else m.sign or '—'
                score=m.score;status=m.status
            predicted=(chosen[1] if number==15 else chosen[0][number-1]) if chosen else '—'
            state='Pendiente'
            if chosen and actual not in ('—','-'):
                state=('Goles coinciden' if predicted==actual else 'Goles fallados') if number==15 else ('Acierto' if predicted==actual else 'Fallo')
            rows.append((f'{number:02} · {m.home} – {m.away}',score,actual,predicted,state,status))
        self.live_model.update_rows(rows)

    def restore_live(self):
        cached=self.repository.setting('live:'+self.round.key)
        if not cached:raise ValueError('No hay directo guardado para esta jornada.')
        from quiniela_ai_studio.infrastructure.integration import validate_teams
        matches=tuple(LiveMatch(**m) for m in cached['matches'])
        validate_teams(self.frozen_round(),[(m.home,m.away) for m in matches])
        self.display_live(matches,cached['captured_at'],cached=True)

    def evaluate_live(self):
        if not self.system or not self.system.bets:
            self.eval_model.update_rows([]);self.eval_summary.setText('Abre una quiniela con apuestas para compararla con los resultados.');return
        if self.show_cached_scrutiny():return
        if not self.live_matches:raise ValueError('Actualiza o recupera primero el marcador de esta jornada.')
        from quiniela_ai_studio.infrastructure.integration import validate_teams
        validate_teams(self.frozen_round(),[(m.home,m.away) for m in self.live_matches])
        result=''.join(m.sign or '-' for m in self.live_matches[:14])
        finalized=tuple(bool(m.final and m.sign) for m in self.live_matches[:14])
        last=self.live_matches[14]
        outcome=engine.evaluate(self.system.bets,result,last.pleno,finalized=finalized,pleno_final=last.final)
        self.render_scrutiny(outcome,last.pleno,last.final)
        self.maybe_fetch_published_scrutiny()

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
        path,selected=QFileDialog.getSaveFileName(self,'Guardar todas las combinaciones',self.export_filename(self.system,'txt'),'TXT clásico · 14 signos + Pleno (*.txt);;JSON (*.json)')
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
        if self.published_worker and self.published_worker.isRunning():
            self.close_pending=True;self.published_worker.cancel_event.set();event.ignore();return
        if self.live_worker and self.live_worker.isRunning():
            self.close_pending=True;self.live_worker.cancel_event.set();event.ignore();return
        self.filter_timer.stop();self.filter_epoch+=1
        if self.athena_job and self.athena_job.isRunning():
            self.close_pending=True;self.athena_job.cancel_event.set();event.ignore();return
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
