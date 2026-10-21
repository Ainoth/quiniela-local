"""Behavioral checks for season presets and visible risk selection."""

pytest_plugins = ("test_ui",)

from PySide6.QtTest import QSignalSpy

from quiniela_ai_studio.ui.risk_selector import RiskSelector
from quiniela_ai_studio.ui.season_picker import SeasonPicker


def test_season_presets_are_one_change_and_search_preserves_hidden_choices(application):
    picker = SeasonPicker()
    counts = {f"{year}-{year + 1}": 40 for year in range(2000, 2026)}
    picker.set_seasons(counts, set(counts))
    signals = QSignalSpy(picker.selectionChanged)
    picker.choose_recent(5)
    expected = set(sorted(counts, reverse=True)[:5])
    assert picker.selected_seasons() == expected
    assert signals.count() == 1
    assert "200 jornadas" in picker.summary.text()
    picker.search.setText("2001")
    assert picker.selected_seasons() == expected
    picker.boxes["2001-2002"].click()
    assert picker.selected_seasons() == expected | {"2001-2002"}
    picker.choose_recent(0)
    assert not picker.selected_seasons()
    picker.choose_recent(None)
    assert picker.selected_seasons() == set(counts)
    picker.close()


def test_risk_buttons_are_exclusive_and_restore_saved_labels(application):
    control = RiskSelector()
    for label, value in (("Mínimo", 0), ("Medio", 1), ("Máximo", 2)):
        control.addItem(label, value)
    signals = QSignalSpy(control.currentIndexChanged)
    control.group.button(2).click()
    assert control.currentData() == 2
    assert control.currentText() == "Máximo"
    assert sum(button.isChecked() for button in control.group.buttons()) == 1
    assert signals.count() == 1
    control.setCurrentText("Medio")
    assert control.currentData() == 1
    control.setCurrentIndex(control.findData(0))
    assert control.currentText() == "Mínimo"
    control.close()
