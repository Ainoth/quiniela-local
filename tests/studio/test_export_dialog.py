"""Export guidance is explicit, exact and never opens a site by itself."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import json
from dataclasses import replace
from datetime import date

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

from quiniela_ai_studio.domain.models import Bet, SystemVersion, utcnow
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.ui import export_dialog


@pytest.fixture(scope="session")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def rounds_and_system():
    round_ = replace(
        demo_round(),
        season="26-27",
        number=12,
        mode="current",
        price_cents=125,
        editable_until=date.today().isoformat(),
    )
    system = SystemVersion(
        "export-test",
        1,
        round_.key,
        "Mi quiniela reducida",
        ("1X2",) * 4 + ("1",) * 10,
        (False,) * 14,
        "",
        (Bet("1" * 14, "02", 2), Bet("X" * 14, "0M")),
        utcnow(),
        parameters=json.dumps({"plenos": ["02", "0M"]}),
    )
    return round_, system


def test_receipt_uses_exact_exported_quantity_and_supplied_price(
    application, rounds_and_system, tmp_path, monkeypatch
):
    round_, system = rounds_and_system
    opened = []
    monkeypatch.setattr(export_dialog.QDesktopServices, "openUrl", opened.append)
    path = tmp_path / "mis apuestas.txt"
    # A streamed export can contain more lines than the materialized preview.
    dialog = export_dialog.build_export_dialog(None, path, system, round_, 12)
    assert not opened
    summary = dialog.findChild(QLabel, "exportSummary").text()
    assert system.name in summary
    assert "Temporada: 26-27 · Jornada: 12" in summary
    assert "Apuestas del TXT: 12" in summary
    assert "15,00 €" in summary and "1,25 € por apuesta" in summary
    assert "0–2, 0–M" in summary
    assert "incluye las copias" in summary
    assert "todavía no están jugadas" in dialog.findChild(QLabel, "exportStatus").text()
    file_input = dialog.findChild(QLineEdit, "exportPath")
    assert file_input.isReadOnly()
    assert file_input.text() == str(path.resolve())
    file_input.selectAll()
    assert file_input.selectedText() == str(path.resolve())
    assert dialog.findChild(QPushButton, "exportClose").isDefault()
    assert not dialog.findChild(QPushButton, "openExportWebsite").autoDefault()
    dialog.close()


def test_external_actions_only_happen_when_their_buttons_are_clicked(
    application, rounds_and_system, tmp_path, monkeypatch
):
    round_, system = rounds_and_system
    opened = []
    monkeypatch.setattr(export_dialog.QDesktopServices, "openUrl", opened.append)
    path = tmp_path / "carpeta con espacios" / "apuestas.txt"
    dialog = export_dialog.build_export_dialog(None, path, system, round_, 3)
    dialog.show()
    application.processEvents()
    assert not opened
    dialog.findChild(QPushButton, "openExportFolder").click()
    assert len(opened) == 1 and opened[0].isLocalFile()
    assert opened[0].toLocalFile() == str(path.parent.resolve())
    web = dialog.findChild(QPushButton, "openExportWebsite")
    assert web.isEnabled()
    web.click()
    assert len(opened) == 2 and opened[1].toString() == export_dialog.UPLOAD_URL
    dialog.findChild(QPushButton, "exportClose").click()
    assert not dialog.isVisible()


def test_receipt_only_announces_plenos_remaining_in_exported_bets(
    application, rounds_and_system, tmp_path
):
    round_, system = rounds_and_system
    system = replace(
        system,
        bets=(Bet("1" * 14, "02", 2),),
        parameters=json.dumps({"pleno_masks": ["0", "2M"]}),
    )
    assert system.plenos == ("02", "0M")
    dialog = export_dialog.build_export_dialog(
        None, tmp_path / "filtradas.txt", system, round_, 2
    )
    summary = dialog.findChild(QLabel, "exportSummary").text()
    assert "Pleno al 15: 0–2." in summary
    assert "0–M" not in summary
    dialog.close()


def test_streamed_draft_receipt_announces_all_selected_plenos(
    application, rounds_and_system, tmp_path
):
    round_, system = rounds_and_system
    system = replace(system, bets=())
    dialog = export_dialog.build_export_dialog(
        None, tmp_path / "todas.txt", system, round_, 162
    )
    assert "Pleno al 15: 0–2, 0–M." in dialog.findChild(QLabel, "exportSummary").text()
    dialog.close()


@pytest.mark.parametrize("mode", ["simulation", "past", "future", "expired"])
def test_non_current_or_demo_receipt_blocks_website_but_keeps_folder(
    application, rounds_and_system, tmp_path, monkeypatch, mode
):
    round_, system = rounds_and_system
    if mode == "simulation":
        round_ = replace(round_, season="DEMO", mode="simulation")
    elif mode == "expired":
        round_ = replace(round_, editable_until="2000-01-01")
    else:
        round_ = replace(round_, mode=mode)
    system = replace(system, round_key=round_.key)
    opened = []
    monkeypatch.setattr(export_dialog.QDesktopServices, "openUrl", opened.append)
    dialog = export_dialog.build_export_dialog(
        None, tmp_path / "apuestas.txt", system, round_, 3
    )
    web = dialog.findChild(QPushButton, "openExportWebsite")
    assert not web.isEnabled()
    web.click()
    assert not opened
    availability = dialog.findChild(QLabel, "exportAvailability").text()
    if mode == "simulation":
        assert "demostración" in availability and "no jugar" in availability
    elif mode == "future":
        assert "aún no está en curso" in availability
    else:
        assert "ya no permite jugar" in availability
    assert dialog.findChild(QLabel, "exportInstructions").text() == (
        "Para jugar, crea una quiniela de la jornada en curso."
    )
    assert dialog.findChild(QPushButton, "openExportFolder").isEnabled()
    dialog.close()


@pytest.mark.parametrize("quantity", [0, -1, True, 1.5])
def test_receipt_rejects_invalid_quantities(
    application, rounds_and_system, tmp_path, quantity
):
    round_, system = rounds_and_system
    with pytest.raises(ValueError, match="al menos una apuesta"):
        export_dialog.build_export_dialog(
            None, tmp_path / "apuestas.txt", system, round_, quantity
        )
