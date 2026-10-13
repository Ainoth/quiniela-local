"""Modos independientes, tabla específica y criterios originales transparentes."""
import json
import math
from dataclasses import replace

import pytest
from PySide6.QtTest import QTest
from test_pleno_probabilities import with_goals
from test_ui import wait_for_data, wait_for_generation

from quiniela_ai_studio.application.services import SystemService
from quiniela_ai_studio.domain.reduction_tables import TABLES
from quiniela_ai_studio.domain.reductions import (
    plan_reduction,
    reduced_bets,
    reduction_template,
)
from quiniela_ai_studio.domain.strategies import selection_weights
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.files import write_txt
from quiniela_ai_studio.infrastructure.storage import Repository

pytest_plugins = ('test_ui',)


@pytest.mark.parametrize('table', TABLES)
def test_each_specific_base_and_exact_matrix(table):
    round_ = with_goals()
    weights = selection_weights(round_)
    base, positions = reduction_template(('X',)*14, (False,)*14, table.number, weights)
    assert [len(s) for s in base].count(2) == table.widths.count(2)
    assert [len(s) for s in base].count(3) == table.widths.count(3)
    assert all(s=='1' for s in base if len(s)==1)
    plan = plan_reduction(base, ('10','M2'), table.number, positions)
    bets = reduced_bets(plan)
    assert len(bets) == len(table.patterns)*2
    assert len(set(bets)) == len(bets)
    assert {b.pleno for b in bets} == {'10','M2'}


def test_contrarian_is_weight_not_a_probability():
    round_ = demo_round()
    snapshots = tuple(replace(s, values=((.55,.27,.18) if s.kind=='sport' else (.78,.15,.07),)*14) for s in round_.snapshots)
    round_ = replace(round_, snapshots=snapshots)
    normal = selection_weights(round_, 'sport', 0)
    different = selection_weights(round_, 'sport', 10)
    assert normal.values[0].index(max(normal.values[0])) == 0
    assert different.values[0].index(max(different.values[0])) == 2
    assert round_.snapshot('sport').values[0] == (.55,.27,.18)
    assert 'no probabilidades' in different.source
    with pytest.raises(ValueError, match='Mercado'):
        selection_weights(round_, 'public', 5)
    with pytest.raises(ValueError):
        selection_weights(replace(round_, snapshots=(round_.snapshot('sport'),)), 'sport', 5)


def test_zero_popularity_and_impossible_sign_are_finite():
    round_ = demo_round()
    snapshots=tuple(replace(s, values=((.6,.4,0) if s.kind=='sport' else (1,0,0),)*14) for s in round_.snapshots)
    weights=selection_weights(replace(round_,snapshots=snapshots),'sport',10)
    assert all(math.isfinite(v) for v in weights.values[0])
    assert weights.values[0][2]==0


def test_reduced_template_preserves_locks_and_rejects_incompatible():
    weights=selection_weights(demo_round())
    base,positions=reduction_template(('X',)+('1',)*13,(True,)+(False,)*13,1,weights)
    assert base[0]=='X' and 0 not in positions
    with pytest.raises(ValueError,match='bloqueos'):
        reduction_template(('1X2',)*5+('1',)*9,(True,)*5+(False,)*9,1,weights)


def test_live_normal_slider_and_stale_navigation(window):
    window.repository.save_round(with_goals());window.load_rounds('DEMO/J01');window.new_system()
    before=window.system
    window.coverage.setValue(5);QTest.qWait(250)
    assert window.system.base!=before.base and window.system.revision==before.revision+1
    assert window.system.plenos
    window.coverage.setValue(6);window.coverage.setValue(7);window.coverage.setValue(8);QTest.qWait(250)
    assert window.system.revision==before.revision+2
    last=window.system
    window.coverage.setValue(9);window.navigation.setCurrentRow(3);QTest.qWait(250)
    assert window.system==last


def test_normal_and_reduced_independent_with_all_choices(window,tmp_path):
    window.repository.save_round(with_goals());window.load_rounds('DEMO/J01');window.new_system()
    window.coverage.setValue(2);QTest.qWait(250)
    window.start_generation();wait_for_generation(window)
    normal=window.system
    window.navigation.setCurrentRow(7)
    assert window.system.system_id!=normal.system_id
    assert window.system_mode(window.system)=='reduced'
    assert window.reduction_options_model.rowCount()==6
    for number in range(1,7):
        window.reduction_picker.setCurrentIndex(number-1);QTest.qWait(250)
        assert window.reduction_apply.isEnabled()
        assert [len(s) for s in window.system.base].count(2)==TABLES[number-1].widths.count(2)
        assert [len(s) for s in window.system.base].count(3)==TABLES[number-1].widths.count(3)
    window.start_generation();wait_for_data(window)
    reduced=window.system
    assert reduced.quantity==132
    path=tmp_path/'reduced.txt';write_txt(path,reduced.bets)
    assert len(path.read_text().splitlines())==132
    window.navigation.setCurrentRow(1)
    assert window.system==normal
    window.navigation.setCurrentRow(7)
    assert window.system==reduced
    assert window.repository.load(normal.system_id)==normal


def test_reduced_pleno_multiplier_and_differentiation(window):
    window.repository.save_round(with_goals());window.load_rounds('DEMO/J01')
    window.navigation.setCurrentRow(7)
    window.reduction_pleno_level.setValue(4);QTest.qWait(250)
    assert len(window.system.plenos)==4
    window.reduction_differentiation.setValue(5);QTest.qWait(250)
    assert json.loads(window.system.parameters)['differentiation_level']==5
    window.apply_reduction();wait_for_data(window)
    assert window.system.quantity==36 and window.system.cost(window.round)==2700
    assert window.system_mode(window.system)=='reduced'


def test_service_preserves_mode_through_generate_and_reopen(tmp_path):
    path=tmp_path/'studio.sqlite3';repo=Repository(path);round_=with_goals();repo.save_round(round_)
    service=SystemService(repo)
    normal=service.new(round_)
    reduced=service.new(round_,mode='reduced')
    reduced=service.reduced_template(reduced,2,differentiation=3)
    plan=plan_reduction(reduced.base,reduced.plenos,2,json.loads(reduced.parameters)['positions'])
    copy=service.reduced_copy(reduced,plan,reduced_bets(plan))
    assert json.loads(copy.parameters)['construction_mode']=='reduced'
    assert repo.load(normal.system_id)==normal
    repo.close();repo=Repository(path)
    assert repo.load(copy.system_id)==copy
    repo.close()


def test_builder_choices_survive_gui_restart(window):
    from quiniela_ai_studio.ui.window import MainWindow
    window.repository.save_round(with_goals());window.load_rounds('DEMO/J01');window.new_system()
    normal=window.system
    window.navigation.setCurrentRow(7)
    window.reduction_picker.setCurrentIndex(2);QTest.qWait(250)
    reduced=window.system
    restored=MainWindow(Repository(window.repository.path))
    try:
        restored.navigation.setCurrentRow(7)
        assert restored.system==reduced and restored.reduction_picker.currentData()==3
        restored.navigation.setCurrentRow(1)
        assert restored.system==normal
    finally:
        restored.close()


def test_pending_slider_cannot_edit_another_round_or_manual_revision(window):
    window.new_system()
    window.coverage.setValue(5)
    window.toggle_goal(0,'M')
    manual=window.system
    QTest.qWait(250)
    assert window.system==manual
    window.coverage.setValue(6)
    past=replace(window.round,number=2,mode='past')
    window.repository.save_round(past);window.load_rounds(past.key);QTest.qWait(250)
    assert window.system is None
    window.navigation.setCurrentRow(7)
    assert window.system is None
    window.load_rounds('DEMO/J01');window.navigation.setCurrentRow(1)
    assert window.system==manual


def test_old_reduced_copy_is_not_used_as_new_specific_base(window):
    import uuid
    window.new_system()
    normal=window.system
    legacy=replace(normal,system_id=str(uuid.uuid4()),revision=1,name='Copia antigua',parameters=json.dumps(dict(reduction=1,plenos=['00'])))
    window.repository.save(legacy)
    window.navigation.setCurrentRow(7)
    assert window.system.system_id not in (normal.system_id,legacy.system_id)
    assert json.loads(window.system.parameters)['construction_mode']=='reduced'
    assert window.repository.load(legacy.system_id)==legacy
