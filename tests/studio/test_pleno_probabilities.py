"""Marginales del Pleno, preselección y multiplicación exacta del coste."""
import json
from dataclasses import replace

import pytest
from test_integration import data_folder, load_win1x2
from test_probability_sources import market_xml

from quiniela_ai_studio.domain.engine import pleno_template, size
from quiniela_ai_studio.domain.models import (
    ProbabilitySnapshot,
    round_dict,
    round_from_dict,
)
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.integration import probability_snapshots

pytest_plugins = ('test_ui',)


def goal_xml():
    fields = []
    for prefix, suffix, rows in [('p_bf_', 'desc', ((10, 50, 30, 10), (40, 10, 20, 30))),
                                  ('p_jugados_', '', ((70, 10, 10, 10), (10, 60, 20, 10)))]:
        for side, values in zip('LV', rows):
            fields.extend(f'{prefix}{g}{side}{suffix}="{v}"' for g, v in zip('012M', values))
    return market_xml().replace(b'num="15"', ('num="15" ' + ' '.join(fields)).encode())


def test_xml_full15_market_and_popularity(tmp_path):
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    updated = probability_snapshots(round_, goal_xml())
    assert updated.snapshot('sport').pleno_values == ((.1, .5, .3, .1), (.4, .1, .2, .3))
    assert updated.snapshot('public').pleno_values == ((.7, .1, .1, .1), (.1, .6, .2, .1))
    assert round_from_dict(round_dict(updated)) == updated
    old = round_dict(round_)
    old['snapshots'] = [dict(kind='sport', source='Antigua', captured_at=round_.captured_at, values=[(.5, .3, .2)] * 14)]
    assert round_from_dict(old).snapshot('sport').pleno_values == ()


@pytest.mark.parametrize('payload', [
    goal_xml().replace(b'p_bf_0Ldesc="10"', b'p_bf_0Ldesc="nan"'),
    goal_xml().replace(b'p_bf_0Ldesc="10"', b'p_bf_0Ldesc="-10"'),
    goal_xml().replace(b'p_bf_0Ldesc="10"', b'p_bf_0Ldesc="80"'),
    goal_xml().replace(b'p_bf_0Ldesc="10"', b''),
    goal_xml().replace(b'p_jugados_0L="70"', b'p_jugados_0L="101"'),
])
def test_invalid_pleno_rejected(tmp_path, payload):
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    with pytest.raises(ValueError):
        probability_snapshots(round_, payload)


def with_goals():
    round_ = demo_round()
    snapshots = tuple(replace(s, pleno_values=((.1, .5, .3, .1), (.4, .1, .2, .3)) if s.kind == 'sport' else ((.7, .1, .1, .1), (.1, .6, .2, .1))) for s in round_.snapshots)
    return replace(round_, snapshots=snapshots)


def test_levels_and_invalid_domain():
    snapshot = with_goals().snapshot('sport')
    widths = (1, 1, 2, 2, 4, 4, 6, 6, 9, 12, 16)
    for level, count in enumerate(widths):
        a, b = pleno_template(snapshot, level)
        assert len(a) * len(b) == count
    assert pleno_template(snapshot, 0) == ('1', '0')
    assert pleno_template(snapshot, 4) == ('12', '0M')
    with pytest.raises(ValueError):
        pleno_template(snapshot, 11)
    with pytest.raises(ValueError):
        ProbabilitySnapshot('sport', 'Invalid', snapshot.captured_at, snapshot.values, pleno_values=((.2,) * 4, (.25,) * 4))


def test_ui_autoselection_multiple_price_and_exports(window, tmp_path):
    from test_ui import wait_for_generation

    from quiniela_ai_studio.infrastructure.files import (
        read_system,
        write_system,
        write_txt,
    )
    round_ = with_goals()
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    window.new_system()
    window.coverage.setValue(4)
    window.apply_template()
    assert window.system.goal_masks == ('12', '0M')
    assert len(window.system.plenos) == 4
    assert window.goal_percentages[0]['1'].text() == '50.0%'
    assert window.goal_percentages[1]['0'].text() == '40.0%'
    assert '16 columnas × 4 Plenos = 64 apuestas' in window.pleno_selection_info.text()
    window.start_generation()
    wait_for_generation(window)
    assert window.system.quantity == 64
    assert window.system.cost(round_) == 4800
    assert len({(b.column, b.pleno) for b in window.system.bets}) == 64
    target = tmp_path / 'pleno.txt'
    write_txt(target, window.system.bets)
    assert len(target.read_text().splitlines()) == 64
    target = tmp_path / 'pleno.json'
    write_system(target, window.system, round_)
    assert read_system(target)[1].bets == window.system.bets
    assert window.repository.load(window.system.system_id).goal_masks == ('12', '0M')
    window.ranking_source.setCurrentIndex(1)
    window.coverage.setValue(0)
    window.apply_template()
    assert window.system.plenos == ('01',)
    assert window.goal_percentages[0]['0'].text() == '70.0%'


def test_missing_goals_preserves_manual_selection(window):
    window.new_system()
    window.toggle_goal(0, 'M')
    window.toggle_goal(1, '2')
    original = window.system.plenos
    window.apply_template()
    assert window.system.plenos == original == ('M2',)
    assert 'no publica porcentajes del Pleno' in window.data_message.text()
    assert window.goal_percentages[0]['0'].text() == '—'


def test_undo_restores_manual_pleno_after_template(window):
    round_ = with_goals()
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    window.new_system()
    window.toggle_goal(0, 'M')
    window.toggle_goal(1, '2')
    original = window.system
    window.coverage.setValue(4)
    window.apply_template()
    assert window.system.plenos != original.plenos
    window.undo()
    assert window.system.plenos == original.plenos == ('M2',)
    assert window.system.goal_masks == original.goal_masks


def test_maximum_includes_full_fifteen(window):
    round_ = with_goals()
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    window.new_system()
    window.coverage.setValue(10)
    window.apply_template()
    assert size(window.system.base) * len(window.system.plenos) == 55296
    assert json.loads(window.system.parameters)['plenos'] == list(window.system.plenos)
