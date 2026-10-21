pytest_plugins = ("test_ui",)

import json
from dataclasses import replace

from PySide6.QtTest import QTest
from test_pleno_probabilities import with_goals

from quiniela_ai_studio.infrastructure.storage import Repository
from quiniela_ai_studio.ui.window import MainWindow


def test_normal_generator_is_graphical_compact_and_edits_exact_base(window):
    window.repository.save_round(with_goals()); window.load_rounds("DEMO/J01"); window.new_system()
    panel = window.normal_generator
    assert panel.probability_table.rowCount() == 14
    assert panel.action_table.rowCount() == 5
    assert panel._matrix_values()[0] == (.5, .3, .2)
    panel.assignment_mode.setCurrentIndex(panel.assignment_mode.findData("manual"))
    panel.triples.setValue(6); panel.doubles.setValue(6)
    panel.fill_base_button.click(); QTest.qWait(20)
    assert [len(signs) for signs in window.system.base].count(3) == 6
    assert [len(signs) for signs in window.system.base].count(2) == 6
    assert [len(signs) for signs in window.system.base].count(1) == 2
    report = json.loads(window.system.parameters)["normal_base_generation"]
    assert report["criteria"] == "maximizar_masa_probabilidad_independiente_v1"
    assert len(report["decisions"]) == 14


def test_normal_generator_manual_mode_chooses_counts_and_parties_by_probability(window):
    window.new_system(); panel = window.normal_generator
    assert panel.probability_table.columnCount() == 5
    panel.assignment_mode.setCurrentIndex(panel.assignment_mode.findData("manual"))
    assert panel.triples.isEnabled() and panel.doubles.isEnabled()
    panel.triples.setValue(1); panel.doubles.setValue(1)
    panel.fill_base_button.click(); QTest.qWait(20)
    assert [len(signs) for signs in window.system.base].count(3) == 1
    assert [len(signs) for signs in window.system.base].count(2) == 1
    report = json.loads(window.system.parameters)["normal_base_generation"]
    assert report["criteria"] == "maximizar_masa_probabilidad_independiente_v1"
    saved = window.repository.setting(f"normal_generator:{window.round.key}")
    assert saved["assignment_mode"] == "manual"
    assert "assignments" not in saved


def test_normal_generator_automatic_selects_counts_under_column_limit(window):
    window.new_system(); panel = window.normal_generator
    panel.assignment_mode.setCurrentIndex(panel.assignment_mode.findData("automatic"))
    assert not panel.triples.isEnabled() and not panel.doubles.isEnabled()
    panel.max_columns.setValue(6)
    panel.fill_base_button.click(); QTest.qWait(20)
    report = json.loads(window.system.parameters)["normal_base_generation"]
    assert report["criteria"] == "maximizar_probabilidad_conjunta_bajo_limite_columnas_v1"
    assert report["columns"] <= 6
    assert report["columns"] == 3 ** report["triples"] * 2 ** report["doubles"]
    assert sum(len(signs) == 3 for signs in window.system.base) == report["triples"]
    assert sum(len(signs) == 2 for signs in window.system.base) == report["doubles"]


def test_numeric_limits_matrix_normalization_and_saved_percentages(window):
    window.new_system(); panel = window.normal_generator
    panel.triples.setValue(14); panel.doubles.setValue(1)
    assert panel.triples.value() + panel.doubles.value() <= 14
    panel.triples.setValue(0); panel.doubles.setValue(0)
    panel.probability_table.item(0, 2).setText("40")
    assert not panel.fill_base_button.isEnabled()
    panel.normalize_button.click()
    assert sum(float(panel.probability_table.item(0, col).text()) for col in (2, 3, 4)) == 100
    panel.save_percentages.click()
    saved = [panel.probability_table.item(0, col).text() for col in (2, 3, 4)]
    panel.probability_table.item(0, 2).setText("50")
    panel.load_percentages.click()
    assert [panel.probability_table.item(0, col).text() for col in (2, 3, 4)] == saved


def test_terminations_are_tiny_independent_toggle_buttons_and_persist(window):
    window.new_system(); panel = window.normal_generator
    widget = panel._action_widgets[0]
    five, seven = widget["endings"][5], widget["endings"][7]
    five.click(); seven.click()
    assert five.isChecked() and seven.isChecked()
    assert "#18864b" in five.styleSheet()
    assert panel._action_config(0)["endings"] == [5, 7]
    five.click()
    assert not five.isChecked() and seven.isChecked()
    assert panel._action_config(0)["endings"] == [7]
    panel._action_widgets[0]["cp_min"].setValue(0.00000004)
    assert panel._action_config(0)["minimum_probability"] == 0.00000004


def test_source_switch_updates_unedited_matrix_but_preserves_manual_edits(window):
    window.new_system(); panel = window.normal_generator
    public = panel.probability_sources["snapshot:public"]
    window.ranking_source.setCurrentIndex(window.ranking_source.findData("public"))
    assert panel.matrix_origin == "snapshot:public"
    assert panel._matrix_values()[0] == public.values[0]
    panel.probability_table.item(0, 2).setText("45")
    panel.probability_table.item(0, 3).setText("35")
    panel.probability_table.item(0, 4).setText("20")
    edited = panel._matrix_values()
    window.ranking_source.setCurrentIndex(window.ranking_source.findData("sport"))
    assert panel.matrix_origin == "manual"
    assert panel._matrix_values() == edited


def test_same_round_source_refresh_populates_matrix_and_disables_missing_factors(window):
    round_ = replace(
        with_goals(), season="26-27", number=15, mode="current", snapshots=(),
        nominal_date="2026-10-21", editable_until="2026-10-22",
    )
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    system = window.service.new(round_, "Fuentes recién descargadas")
    window.set_system(system)
    panel = window.normal_generator
    assert panel.matrix_origin == "manual"
    assert panel.recalculate_button.isEnabled() is False
    assert all(spin.value() == 0 and not spin.isEnabled() for spin in panel.weight_spin.values())

    updated_round = replace(round_, snapshots=with_goals().snapshots)
    window.repository.save_round(updated_round)
    refreshed_system = window.service.refresh_sources(system)
    window.set_system(refreshed_system)

    market = updated_round.snapshot("sport")
    assert panel.matrix_origin == "snapshot:sport"  # Mercado es la selección inicial.
    assert panel._matrix_values() == market.values
    assert panel.recalculate_button.isEnabled() is False
    window.ranking_source.setCurrentIndex(window.ranking_source.findData("public"))
    public = updated_round.snapshot("public")
    assert panel.matrix_origin == "snapshot:public"
    assert panel._matrix_values() == public.values


def test_normal_configuration_is_saved_per_round_and_restored(window):
    window.new_system(); panel = window.normal_generator
    panel.triples.setValue(2); panel.doubles.setValue(4)
    panel._action_widgets[0]["endings"][9].click()
    panel._action_widgets[0]["cp_max"].setValue(0.000001)
    panel.weight_spin["classification"].setValue(0)
    repository = Repository(window.repository.path)
    restored = MainWindow(repository)
    try:
        restored.load_rounds(window.round.key)
        copy = restored.normal_generator
        assert copy.triples.value() == 2 and copy.doubles.value() == 4
        assert copy.weight_spin["classification"].value() == 0
        assert copy._action_config(0)["endings"] == [9]
        assert copy._action_config(0)["maximum_probability"] == 0.000001
    finally:
        restored.close(); repository.close()
