"""Capture the prize panel with a clearly synthetic, local PRE fixture."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PySide6.QtWidgets import QApplication

from quiniela_ai_studio.domain.models import Bet
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.providers import load_win1x2
from quiniela_ai_studio.infrastructure.storage import Repository
from quiniela_ai_studio.ui.window import STYLE, MainWindow
from tests.studio.test_integration import data_folder

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "validacion_visual" / "escrutinio_premios_v1_0_27.png"
COMPACT_OUTPUT = ROOT / "docs" / "validacion_visual" / "escrutinio_premios_compacto_v1_0_27.png"


def main() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    with tempfile.TemporaryDirectory(prefix="escrutinio-visual-") as directory:
        root = Path(directory)
        folder = data_folder(root / "premios_sinteticos")
        historical = load_win1x2(folder)[0]
        repository = Repository(root / "studio.sqlite3")
        repository.save_round(demo_round())
        repository.save_round(historical)
        window = MainWindow(repository)
        window.resize(1600, 940)
        window.show()
        window.load_rounds(historical.key)
        repository.set_setting("data_directory", str(folder))
        bets = (Bet("1" * 14, "00", 2), Bet("2" + "1" * 13, "00", 3))
        window.set_system(window.service.imported(historical, "EJEMPLO SINTÉTICO · premios de prueba", bets))
        window.auto_live.setChecked(False)
        window.navigation.setCurrentRow(4)
        app.processEvents()
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        window.grab().save(str(OUTPUT))
        window.resize(1200, 780)
        app.processEvents()
        window.grab().save(str(COMPACT_OUTPUT))
        window.close()


if __name__ == "__main__":
    main()
