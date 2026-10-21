"""Capture SSeguidos and compare it to the bundled WIN1X2 reference."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from zipfile import ZipFile

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.storage import Repository
from quiniela_ai_studio.ui.window import STYLE, MainWindow

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ZIP = ROOT / "REFERENCIAS_Y_PROMPT_CODEX_QT.zip"
OUTPUT = ROOT / "docs" / "validacion_visual" / "sseguidos_v1_0_26"
REFERENCE_MEMBER = "referencias_originales/03_signos_seguidos_automatica.png"


def main() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    with tempfile.TemporaryDirectory(prefix="sseguidos-visual-") as directory:
        repository = Repository(Path(directory) / "visual.sqlite3")
        repository.save_round(demo_round())
        window = MainWindow(repository)
        window.resize(1536, 960)
        window.show()
        window.navigation.setCurrentRow(8)
        app.processEvents()
        window.reduction_tabs.setCurrentIndex(window.reduction_visible_indexes[1])
        window.mode_tabs["SSeguidos"].setCurrentWidget(window.run_mode_pages["Automática"])
        app.processEvents()
        actual = window.classic_reduction_canvases[1].grab().toImage().convertToFormat(QImage.Format.Format_RGB32)
        actual.save(str(OUTPUT / "sseguidos_automatica.png"))
        window.close()

    with ZipFile(REFERENCE_ZIP) as archive:
        reference = QImage.fromData(archive.read(REFERENCE_MEMBER)).convertToFormat(QImage.Format.Format_RGB32)
    reference.save(str(OUTPUT / "referencia_original_automatica.png"))
    fitted = reference.scaled(actual.size(), Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
    comparison = QImage(actual.width() * 2 + 20, actual.height() + 20, QImage.Format.Format_RGB32)
    comparison.fill(QColor("#071a33"))
    painter = QPainter(comparison)
    painter.drawImage(10 + (actual.width() - fitted.width()) // 2, 10, fitted)
    painter.drawImage(actual.width() + 20, 10, actual)
    painter.end()
    comparison.save(str(OUTPUT / "comparacion_lado_a_lado.png"))


if __name__ == "__main__":
    main()
