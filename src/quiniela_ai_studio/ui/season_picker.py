"""Compact historical season selection with explicit, batched presets."""

from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SeasonPicker(QWidget):
    """Select complete seasons; search only changes visibility, never selection."""

    selectionChanged = Signal(object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("seasonPicker")
        self.setMinimumHeight(260)
        self.counts: dict[str, int] = {}
        self.boxes: dict[str, QCheckBox] = {}
        root = QVBoxLayout(self)
        root.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)
        presets = QHBoxLayout()
        presets.setSpacing(4)
        for label, count in (("Últimas 5", 5), ("Últimas 10", 10),
                             ("Todas", None), ("Ninguna", 0)):
            button = QPushButton(label)
            button.setObjectName("seasonPreset")
            button.clicked.connect(lambda _checked=False, n=count: self.choose_recent(n))
            presets.addWidget(button)
        root.addLayout(presets)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar temporada… p. ej. 2023")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(150)
        host = QWidget()
        self.grid = QGridLayout(host)
        self.grid.setContentsMargins(2, 2, 2, 2)
        self.grid.setSpacing(5)
        self.scroll.setWidget(host)
        root.addWidget(self.scroll)
        self.summary = QLabel()
        self.summary.setObjectName("seasonSummary")
        self.summary.setWordWrap(True)
        self.summary.setMinimumHeight(28)
        root.addWidget(self.summary)
        self.setStyleSheet("""
            QWidget#seasonPicker QCheckBox {
                background:#123657; color:#dcedfa; border:1px solid #315c7c;
                border-radius:4px; padding:6px 4px; font-size:11px;
            }
            QWidget#seasonPicker QCheckBox:checked {
                background:#123f3a; border-color:#269b6a; color:#b7ffd5;
            }
            QWidget#seasonPicker QCheckBox::indicator {
                width:12px; height:12px; border:1px solid #91bed7;
                background:#edf6ff; border-radius:2px;
            }
            QWidget#seasonPicker QCheckBox::indicator:checked {
                background:#19b56b; border-color:#5cf1a4; image:none;
            }
            QWidget#seasonPicker QPushButton#seasonPreset {
                padding:4px 5px; font-size:10px; min-height:20px;
            }
            QWidget#seasonPicker QLineEdit {
                background:#0b223c; color:#deefff; border:1px solid #37698e;
                border-radius:4px; padding:5px; font-size:11px;
            }
            QWidget#seasonPicker QScrollArea {border:0; background:transparent;}
            QWidget#seasonPicker QLabel#seasonSummary {
                color:#73e7b1; font-size:11px; background:transparent;
            }
        """)

    def set_seasons(self, counts: Mapping[str, int], selected: set[str]) -> None:
        """Replace available seasons only when the history inventory changes."""
        if dict(counts) != self.counts:
            self.counts = dict(counts)
            for box in self.boxes.values():
                box.deleteLater()
            while self.grid.count():
                self.grid.takeAt(0)
            self.boxes = {}
            for season in sorted(counts, reverse=True):
                box = QCheckBox(season)
                box.setAccessibleName(f"Incluir temporada {season}")
                box.setToolTip(f"{counts[season]} jornadas con resultado final")
                box.toggled.connect(self._edited)
                self.boxes[season] = box
            self._filter()
        self.set_selection(selected)

    def selected_seasons(self) -> set[str]:
        return {season for season, box in self.boxes.items() if box.isChecked()}

    def set_selection(self, selected: set[str]) -> None:
        for season, box in self.boxes.items():
            box.blockSignals(True)
            box.setChecked(season in selected)
            box.blockSignals(False)
        total = sum(self.counts[season] for season in self.selected_seasons())
        self.summary.setText(
            f"{len(self.selected_seasons())} temporadas · {total:,} jornadas para analizar"
            if total else "Selecciona al menos una temporada con resultados."
        )

    def choose_recent(self, count: int | None) -> None:
        seasons = sorted(self.counts, reverse=True)
        selected = set(seasons if count is None else seasons[:count])
        self.set_selection(selected)
        self.selectionChanged.emit(selected)

    def _edited(self, _checked: bool) -> None:
        selected = self.selected_seasons()
        self.set_selection(selected)
        self.selectionChanged.emit(selected)

    def _filter(self, _text: str = "") -> None:
        previous_rows = self.grid.rowCount()
        while self.grid.count():
            self.grid.takeAt(0)
        for row in range(previous_rows):
            self.grid.setRowStretch(row, 0)
        query = self.search.text().strip().lower()
        visible = 0
        for season, box in self.boxes.items():
            matches = query in season.lower()
            box.setVisible(matches)
            if matches:
                self.grid.addWidget(box, visible // 3, visible % 3)
                visible += 1
        self.grid.setRowStretch((visible + 2) // 3, 1)
