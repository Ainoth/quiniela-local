"""Measured, reusable Qt surfaces for the compact WIN1X2 reduction views.

Only the decorative surface is painted. Lists, cells, tabs and buttons remain
native, focusable Qt widgets above it.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QButtonGroup,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QWidget,
)

CLASSIC_STYLE = """
QWidget#classicReductionCanvas QWidget {background:transparent;}
QWidget#classicReductionCanvas QLabel {background:transparent;color:#f4f7ff;font-family:Arial,"DejaVu Sans";font-size:11px;}
QWidget#classicReductionCanvas QLabel#classicHeading {color:#78e9e8;font-weight:bold;font-size:13px;}
QWidget#classicReductionCanvas QLabel#classicSign {color:#ffe67a;font-weight:900;font-size:46px;}
QWidget#classicReductionCanvas QGroupBox {background:rgba(15,55,112,70);border:1px solid #568bb4;border-radius:4px;margin-top:14px;padding-top:5px;color:#83ebec;font-weight:bold;font-size:11px;}
QWidget#classicReductionCanvas QGroupBox::title {subcontrol-origin:margin;subcontrol-position:top left;left:8px;padding:1px 5px;color:#8cebea;background:#0a203b;}
QWidget#classicReductionCanvas QTabWidget#reductionModeTabs::pane {background:transparent;border:2px solid #a3cbed;border-bottom-color:#16417b;border-right-color:#16417b;top:-1px;}
QWidget#classicReductionCanvas QTabWidget#reductionModeTabs QTabBar::tab {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #245c9a,stop:1 #11346c);border:1px solid #87c9ed;border-bottom-color:#193e7c;color:#8be9ef;padding:6px 12px;margin-right:1px;font-size:11px;min-width:72px;}
QWidget#classicReductionCanvas QTabWidget#reductionModeTabs QTabBar::tab:selected {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #4b92c7,stop:1 #1a4b91);color:#ffe571;font-weight:bold;}
QWidget#classicReductionCanvas QLineEdit,QWidget#classicReductionCanvas QSpinBox,QWidget#classicReductionCanvas QComboBox {background:#ffffff;color:#183b75;border:1px solid #95b8da;border-radius:0;padding:1px;font-size:11px;}
QWidget#classicReductionCanvas QPushButton {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #4b86bd,stop:0.5 #225c9c,stop:1 #123875);color:#f3f8ff;border:1px solid #86bce6;border-bottom-color:#12346b;border-right-color:#12346b;border-radius:0;padding:2px 6px;font-size:10px;min-height:17px;}
QWidget#classicReductionCanvas QPushButton:hover {background:#3478ba;}
QWidget#classicReductionCanvas QPushButton:checked {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #3b8fc4,stop:1 #17508c);color:#ffe877;font-weight:bold;border-color:#b5e1fb;}
QWidget#classicReductionCanvas QPushButton#classicSubTab {min-height:23px;padding:2px 7px;}
QWidget#classicReductionCanvas QListWidget,QWidget#classicReductionCanvas QScrollArea#classicWhiteList {background:#ffffff;color:#143b79;border:1px solid #a9c9e3;border-bottom-color:#133d7a;border-right-color:#133d7a;border-radius:0;font-size:10px;}
QWidget#classicReductionCanvas QListWidget::item {background:#ffffff;color:#143b79;min-height:12px;padding:0 1px;}
QWidget#classicReductionCanvas QListWidget::item:selected {background:#2666b4;color:white;}
QWidget#classicReductionCanvas QScrollBar:vertical {background:#d3e0ec;width:9px;}
QWidget#classicReductionCanvas QScrollBar::handle:vertical {background:#91aeca;min-height:17px;border:1px solid #5981a7;}
QWidget#classicReductionCanvas QRadioButton {background:transparent;color:white;font-size:11px;}
QWidget#classicReductionCanvas QRadioButton::indicator {width:10px;height:10px;}
"""


class ClassicReductionsCanvas(QWidget):
    """Decorative blue canvas, independent of the functional filter widgets."""

    def __init__(self, width: int = 700, height: int = 640, parent: QWidget | None = None,
                 *, decorative: bool = True):
        super().__init__(parent)
        self.decorative = decorative
        self.setObjectName("classicReductionCanvas")
        self.setFixedWidth(width)
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)
        self.setStyleSheet(CLASSIC_STYLE)

    def sizeHint(self) -> QSize:
        return QSize(self.width(), max(self.minimumHeight(), 640))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        if not self.decorative:
            painter.fillRect(self.rect(), QColor("#071a33"))
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rectangle = self.rect()
        base = QLinearGradient(0, 0, rectangle.width(), rectangle.height())
        base.setColorAt(0, QColor("#55b3d8"))
        base.setColorAt(0.17, QColor("#20568d"))
        base.setColorAt(0.58, QColor("#214b88"))
        base.setColorAt(1, QColor("#0b306d"))
        painter.fillRect(rectangle, base)
        glow = QRadialGradient(rectangle.width() * .54, rectangle.height() * .55,
                               rectangle.width() * .67)
        glow.setColorAt(0, QColor(86, 168, 223, 83))
        glow.setColorAt(1, QColor(13, 48, 103, 0))
        painter.fillRect(rectangle, glow)
        painter.setPen(QPen(QColor(116, 186, 230, 35), 3))
        centre_x = rectangle.width() * .53
        centre_y = rectangle.height() * .63
        for radius in (105, 175, 250, 330):
            painter.drawEllipse(int(centre_x-radius), int(centre_y-radius), radius*2, radius*2)
        painter.setPen(QPen(QColor("#a1d8f1"), 2))
        painter.drawLine(2, 2, rectangle.width()-3, 2)
        painter.drawLine(2, 2, 2, rectangle.height()-3)
        painter.setPen(QPen(QColor("#16396e"), 2))
        painter.drawLine(3, rectangle.height()-3, rectangle.width()-3, rectangle.height()-3)
        painter.drawLine(rectangle.width()-3, 3, rectangle.width()-3, rectangle.height()-3)


class ClassicPillBadge(QLabel):
    """Small raised season/jornada value in the historical header."""

    def __init__(self, value: str, parent: QWidget | None = None):
        super().__init__(value, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(78, 22)
        self.setStyleSheet(
            "QLabel{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #071f4f,stop:0.52 #1d639d,stop:1 #092858);"
            "border:1px solid #39749c;border-radius:5px;"
            "color:#9ee9ff;font-weight:bold;font-size:10px;}"
        )


class ClassicContextHeader(QWidget):
    """Compact classic header with live season and round badges."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 1, 4, 1)
        row.setSpacing(5)
        row.addStretch(1)
        row.addWidget(QLabel("Temporada"))
        self.season = ClassicPillBadge("—")
        row.addWidget(self.season)
        row.addSpacing(4)
        row.addWidget(QLabel("Jornada"))
        self.round = ClassicPillBadge("—")
        self.round.setFixedWidth(58)
        row.addWidget(self.round)
        row.addStretch(1)
        self.setFixedHeight(28)

    def set_context(self, season: str, round_number: str) -> None:
        self.season.setText(season)
        self.round.setText(round_number)


class ClassicTotalList(QListWidget):
    """Vertical total selector with a QSpinBox-compatible value API."""

    valueChanged = Signal(int)

    def __init__(self, accessible_name: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAccessibleName(accessible_name)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedSize(37, 58)
        for value in range(15):
            item = QListWidgetItem(str(value))
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.addItem(item)
        self.currentRowChanged.connect(self.valueChanged.emit)
        self.setCurrentRow(0)

    def value(self) -> int:
        return max(0, self.currentRow())

    def setValue(self, value: int) -> None:
        self.setCurrentRow(int(value))

    def set_allowed_totals(self, allowed: set[int], selected: set[int] | None = None) -> None:
        """Gray impossible totals while retaining a previously selected value."""
        retained = selected or set()
        for value in range(self.count()):
            item = self.item(value)
            enabled = value in allowed or value in retained
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled if enabled else Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor("#163c75") if enabled else QColor("#97a4b4"))


class ClassicTotalGrid(QWidget):
    """Compact, fully visible 0–14 selector for exact run figures."""

    valueChanged = Signal(int)

    def __init__(self, accessible_name: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAccessibleName(accessible_name)
        self._allowed: set[int] = set(range(15))
        self._retained: set[int] = set()
        self._value = 0
        self.buttons: list[QPushButton] = []
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(2)
        grid.setVerticalSpacing(2)
        for value in range(15):
            button = QPushButton(str(value), self)
            button.setCheckable(True)
            button.setFixedSize(20, 18)
            button.setAccessibleName(f'{accessible_name}: total {value}')
            button.setStyleSheet(
                'QPushButton{padding:0;background:#f3f6fb;color:#173b75;border:1px solid #9bb9d4;}'
                'QPushButton:checked{background:#2782b8;color:#fff;font-weight:bold;border-color:#b5e1fb;}'
                'QPushButton:disabled{background:#d7e0e9;color:#97a4b4;border-color:#b7c6d3;}'
            )
            button.toggled.connect(lambda checked, total=value: self._selected(total, checked))
            self.group.addButton(button, value)
            self.buttons.append(button)
            grid.addWidget(button, value // 5, value % 5)
        self.buttons[0].setChecked(True)

    def _selected(self, value: int, checked: bool) -> None:
        if checked and value != self._value:
            self._value = value
            self.valueChanged.emit(value)

    def value(self) -> int:
        return self._value

    def setValue(self, value: int) -> None:
        value = max(0, min(14, int(value)))
        self.buttons[value].setChecked(True)

    def set_allowed_totals(self, allowed: set[int], selected: set[int] | None = None) -> None:
        self._allowed = set(allowed)
        self._retained = set(selected or ())
        for value, button in enumerate(self.buttons):
            enabled = value in self._allowed or value in self._retained
            button.setEnabled(enabled)
            button.setToolTip(
                f'Total {value} alcanzable en la base actual.' if value in self._allowed
                else f'Total {value} conservado; no aparece en la base actual.'
            )


def emboss_symbol(label: QLabel) -> None:
    """Give the live sign label the small ochre shadow in the references."""
    effect = QGraphicsDropShadowEffect(label)
    effect.setBlurRadius(2)
    effect.setOffset(2, 2)
    effect.setColor(QColor("#815307"))
    label.setGraphicsEffect(effect)
