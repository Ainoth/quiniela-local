"""Visible risk choices with stable labels/data for existing calculations."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

RISK_BUTTON_STYLE = """
QPushButton#riskLevel {
    background:#123451; color:#adcce2; border:1px solid #376889;
    border-radius:4px; padding:5px 7px; font-size:11px; min-height:19px;
}
QPushButton#riskLevel:hover {background:#1b4b6d; border-color:#5fbed7;}
QPushButton#riskLevel:checked {
    background:#116d60; color:#d4ffdb; border:1px solid #50dfa6; font-weight:bold;
}
QPushButton#riskLevel:focus {border:2px solid #ffd15a;}
QPushButton#riskLevel:disabled {color:#71869a; background:#172b3c;}
"""


def risk_button(label: str) -> QPushButton:
    button = QPushButton(label)
    button.setObjectName("riskLevel")
    button.setCheckable(True)
    button.setStyleSheet(RISK_BUTTON_STYLE)
    button.setAccessibleName(f"Riesgo {label}")
    return button


class RiskSelector(QWidget):
    """Exclusive buttons, exposing the small selection API used by the app."""

    currentIndexChanged = Signal(int)
    currentTextChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("riskSelector")
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(3)
        self.items: list[tuple[str, object]] = []
        self.group.idClicked.connect(self._changed)

    def addItem(self, label: str, data: object = None) -> None:
        index = len(self.items)
        self.items.append((label, data))
        button = risk_button(label)
        self.group.addButton(button, index)
        self.row.addWidget(button)
        if index == 0:
            button.setChecked(True)

    def count(self) -> int:
        return len(self.items)

    def currentIndex(self) -> int:
        return self.group.checkedId()

    def currentData(self) -> object:
        index = self.currentIndex()
        return self.items[index][1] if index >= 0 else None

    def currentText(self) -> str:
        index = self.currentIndex()
        return self.items[index][0] if index >= 0 else ""

    def itemText(self, index: int) -> str:
        return self.items[index][0]

    def findText(self, label: str) -> int:
        return next((i for i, item in enumerate(self.items) if item[0] == label), -1)

    def findData(self, data: object) -> int:
        return next((i for i, item in enumerate(self.items) if item[1] == data), -1)

    def setCurrentText(self, label: str) -> None:
        self.setCurrentIndex(self.findText(label))

    def setCurrentIndex(self, index: int) -> None:
        if 0 <= index < len(self.items) and index != self.currentIndex():
            self.group.button(index).setChecked(True)
            self._changed(index)

    def _changed(self, index: int) -> None:
        self.currentIndexChanged.emit(index)
        self.currentTextChanged.emit(self.currentText())
