"""Boleto estable y espacio de Aciertos para todos los marcadores."""
from dataclasses import replace

from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest

from live_results import LiveMatch
from quiniela_ai_studio.domain.engine import generate

pytest_plugins = ('test_ui',)


def fill_results(window):
    system = window.service.imported(window.round, 'Distribución de prueba',
                                     generate(('1X2',)*4+('1',)*10, 'M0'))
    window.set_system(system)
    window.auto_live.setChecked(False)
    matches = tuple(LiveMatch(m.number, m.home, m.away, '3 - 0' if m.number == 15 else '1 - 0',
                              '1', 'M0' if m.number == 15 else '', 'Finalizado', True, 90)
                    for m in window.round.matches)
    window.display_live(matches, window.round.captured_at, cached=True)
    return system


def ballot_positions(window):
    widgets = [window.sign_buttons[i][sign] for i in range(14) for sign in '1X2']
    widgets += [window.goal_buttons[side][goal] for side in range(2) for goal in '012M']
    return [(widget.mapTo(window.ballot, QPoint(0, 0)).x(),
             widget.mapTo(window.ballot, QPoint(0, 0)).y()) for widget in widgets]


def test_ballot_width_and_sign_positions_do_not_expand_with_window(window):
    fill_results(window)
    window.resize(1200, 975);QTest.qWait(30)
    original = ballot_positions(window)
    assert window.ballot.width() == 550
    window.resize(1920, 1080);QTest.qWait(30)
    assert window.ballot.width() == 550
    assert ballot_positions(window) == original
    window.splitter.moveSplitter(850, 1);QTest.qWait(10)
    assert window.ballot.width() == 550
    last = window.sign_buttons[13]['2']
    assert last.mapTo(window.ballot_scroll.viewport(), last.rect().bottomRight()).y() < window.ballot_scroll.viewport().height()


def test_all_fourteen_results_and_pleno_fit_above_smaller_bet_table(window):
    original = fill_results(window)
    window.resize(1920, 975)
    window.navigation.setCurrentRow(4);QTest.qWait(50)
    assert window.live_model.rowCount() == 15
    assert window.live_view.verticalScrollBar().maximum() == 0
    for row in (13, 14):
        rectangle = window.live_view.visualRect(window.live_model.index(row, 0))
        assert rectangle.bottom() < window.live_view.viewport().height()
    assert window.eval_view.isHidden()
    assert window.eval_detail_button.isEnabled()
    window.eval_detail_button.click();QTest.qWait(20)
    assert window.eval_view.isVisible()
    window.eval_view.setCurrentIndex(window.eval_model.index(20, 0))
    window.eval_detail_button.click();QTest.qWait(20)
    assert window.eval_view.isHidden()
    window.resize(1200, 975);QTest.qWait(50)
    assert window.live_view.verticalScrollBar().maximum() == 0
    assert window.eval_view.currentIndex().row() == 20
    assert window.system.hash == original.hash


def test_small_screen_keeps_generation_accessible_and_manual_results_work(window):
    fill_results(window)
    window.resize(1024, 768)
    window.navigation.setCurrentRow(4);QTest.qWait(30)
    assert window.minimumSizeHint().height() <= 768
    assert window.generate_button.mapTo(window, window.generate_button.rect().bottomRight()).y() < window.height()
    window.manual_mode.setChecked(True);QTest.qWait(30)
    assert window.manual_container.isVisible() and not window.live_view.isVisible()
    window.manual_mode.setChecked(False);QTest.qWait(30)
    assert window.live_view.isVisible() and not window.manual_container.isVisible()


def test_classic_table_shows_schedule_and_selected_source_without_changing_bets(window):
    original_round=window.round
    matches=(replace(original_round.matches[0],kickoff='14/10/202618:45'),)+original_round.matches[1:]
    snapshots=tuple(replace(s,values=((.26,.28,.46) if s.kind=='sport' else (.45,.30,.25),)*14) for s in original_round.snapshots)
    round_=replace(original_round,matches=matches,snapshots=snapshots)
    window.repository.save_round(round_);window.load_rounds(round_.key)
    original=window.service.imported(round_,'Fuentes de la tabla',generate(('1X',)+('1',)*13,'M0'))
    window.set_system(original);window.navigation.setCurrentRow(4);QTest.qWait(30)
    assert '14/10/2026 18:45' in window.match_labels[0].toolTip()
    assert all(label.isVisible() for label in window.prob_labels[0])
    assert [label.text() for label in window.prob_labels[0]]==['26%','28%','46%']
    window.ranking_source.setCurrentIndex(1)
    assert [label.text() for label in window.prob_labels[0]]==['45%','30%','25%']
    assert round_.snapshot('public').source in window.prob_labels[0][0].toolTip()
    assert window.system==original
    assert window.repository.load(original.system_id).hash==original.hash
    assert [label.text() for label in window.pleno_team_labels]==[round_.matches[14].home,round_.matches[14].away]


def test_classic_table_does_not_invent_missing_percentages_or_schedules(window):
    round_=replace(window.round,snapshots=(),matches=tuple(replace(m,kickoff='') for m in window.round.matches))
    window.repository.save_round(round_);window.load_rounds(round_.key);window.new_system()
    assert all(label.text()=='—' for row in window.prob_labels for label in row)
    assert all(not label.toolTip().splitlines()[1].strip() for label in window.match_labels)


def test_scrutiny_failure_panel_explains_missed_matches_and_reduction(window):
    from quiniela_ai_studio.domain.filters import BasicFilters
    from quiniela_ai_studio.domain.models import Bet
    from quiniela_ai_studio.domain.reduction_rules import ReductionRule

    winning = '1' * 14
    surviving = 'X' + '1' * 13
    source = window.service.imported(window.round, 'Diagnóstico', (Bet(winning, '00'), Bet(surviving, '00')))
    window.set_system(source)
    spec = BasicFilters(
        reduction_rules=(ReductionRule('fss-current-X', 'allowed_count', 0, 14,
                                       sign='X', allowed_values=(1,), tab_index=17),),
        reduction_tabs_enabled=(17,),
    )
    candidates = source.bets
    filtered = spec.apply(candidates)
    window.set_system(window.service.save_filtered(source, spec, filtered, candidates))
    outcome = __import__('quiniela_ai_studio.domain.engine', fromlist=['evaluate']).evaluate(
        window.system.bets, winning, '00', finalized=(True,) * 14,
    )
    text = window.scrutiny_diagnostic_text(winning, outcome)
    assert 'Mejor apuesta (13/14)' in text
    assert f"1. {window.round.matches[0].home}" in text
    assert 'eliminó en la revisión' in text
    assert 'FSSeguidos' in text
    assert 'salió 0' in text and 'valores 1' in text


def test_scrutiny_diagnostic_panel_is_collapsed_until_requested(window):
    assert window.scrutiny_diagnostic_panel.isHidden()
    window.toggle_scrutiny_diagnostics()
    assert not window.scrutiny_diagnostic_panel.isHidden()
    assert window.scrutiny_diagnostic_button.text().startswith('Ocultar')
