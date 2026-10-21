"""Reproduce the Cuenta v1.0.33 screenshots with an isolated demo repository."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.storage import Repository
from quiniela_ai_studio.ui.window import STYLE, MainWindow


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "docs/validacion_visual/v1_0_33"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    with tempfile.TemporaryDirectory(prefix="cuenta-unificada-") as directory:
        repository = Repository(Path(directory) / "demo.sqlite3")
        repository.save_round(demo_round())
        window = MainWindow(repository)
        window.resize(1920, 1040)
        window.show()
        window.new_system()
        window.navigation.setCurrentRow(8)
        window.reduction_tabs.setCurrentIndex(window.reduction_visible_indexes[0])
        for mode, name in ((0, "manual"), (2, "automatica")):
            window.mode_tabs["Cuenta"].setCurrentIndex(mode)
            if mode == 2:
                window.count_season_picker.choose_recent(5)
                window.mode_automatic_controls["Cuenta"][0].setCurrentText("Medio")
            app.processEvents()
            app.processEvents()
            window.grab().save(str(output / f"cuenta_{name}.png"))
        window.close()


if __name__ == "__main__":
    main()
