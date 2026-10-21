"""Capture isolated demo states for visual QA without reading user settings.

Run from the repository root with QT_QPA_PLATFORM=offscreen. The reference ZIP
is used only to create comparison overlays; it is not displayed by the app.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from zipfile import ZipFile

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from quiniela_studio.demo import demo_round
from quiniela_studio.storage import Repository
from quiniela_studio.ui import STYLE, MainWindow

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "validacion_visual" / "reducciones_v1_0_22"
ZIP = ROOT / "REFERENCIAS_Y_PROMPT_CODEX_QT.zip"
VIEWS = (
    ("cuenta_manual", 0, "Manual", 0, None),
    ("cuenta_automatica", 0, "Automática", 0, None),
    ("sseguidos_manual", 1, "Manual", 0, "01_signos_seguidos_manual_A.png"),
    ("sseguidos_automatica", 1, "Automática", 0, "03_signos_seguidos_automatica.png"),
    ("fsseguidos_manual", 17, "Manual", 0, "04_figuras_signos_seguidos_manual.png"),
    ("interrupciones_manual", 18, "Manual", 0, "05_interrupciones_manual_A.png"),
    ("distancias_manual", 18, "Manual", 1, "08_distancias_manual.png"),
    ("grupo", 9, "", 0, None),
)


def main() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    with tempfile.TemporaryDirectory(prefix="quiniela-visual-") as temporary:
        repository = Repository(Path(temporary) / "visual.sqlite3")
        repository.save_round(demo_round())
        window = MainWindow(repository)
        window.resize(1536, 960)
        window.show()
        window.navigation.setCurrentRow(8)
        app.processEvents()
        # Static fixture choices are explicitly declared and never persisted to
        # the user's database. They show populated controls for comparison.
        for sign in ("1", "X", "2", "V"):
            available = window.run_possible_figures[sign]
            if available:
                total = min(available, key=lambda candidate: abs(candidate - 7))
                window.run_figure_total_squares[sign][total].setChecked(True)
        for sign, total in (("1", 7), ("X", 3), ("2", 3), ("V", 7)):
            window.fss_total_controls[sign].setValue(total)
        if 7 in window.interruption_total_buttons:
            window.interruption_total_buttons[7].setChecked(True)
        for name, index, mode, subtab, original_name in VIEWS:
            window.reduction_tabs.setCurrentIndex(window.reduction_visible_indexes[index])
            if index != 9:
                title = {0:"Cuenta",1:"Racha",17:"FSSeguidos",18:"Interrupciones"}[index]
                tabs = window.mode_tabs[title]
                tabs.setCurrentIndex(next(number for number in range(tabs.count()) if tabs.tabText(number) == mode))
            if index == 18:
                window._show_interruption_subtab(subtab)
            app.processEvents()
            widget = window.classic_reduction_canvases[index]
            result = OUTPUT / f"{name}.png"
            widget.grab().save(str(result))
            if original_name and ZIP.exists():
                with ZipFile(ZIP) as archive, archive.open(
                    f"referencias_originales/{original_name}"
                ) as stream:
                    reference = QImage.fromData(stream.read()).convertToFormat(QImage.Format.Format_RGB32)
                actual = QImage(str(result))
                fitted = actual.scaled(reference.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
                aligned = fitted.copy((fitted.width()-reference.width())//2,
                                      (fitted.height()-reference.height())//2,
                                      reference.width(), reference.height())
                overlay = QImage(reference)
                painter = QPainter(overlay)
                painter.setOpacity(.5)
                painter.drawImage(0, 0, aligned)
                painter.end()
                overlay.save(str(OUTPUT / f"{name}_overlay.png"))
                difference = QImage(reference.size(), QImage.Format.Format_RGB32)
                for y in range(reference.height()):
                    for x in range(reference.width()):
                        left = reference.pixelColor(x, y)
                        right = aligned.pixelColor(x, y)
                        difference.setPixelColor(x, y, QColor(abs(left.red()-right.red()),
                                                              abs(left.green()-right.green()),
                                                              abs(left.blue()-right.blue())))
                difference.save(str(OUTPUT / f"{name}_diff.png"))
        window.close()


if __name__ == "__main__":
    main()
