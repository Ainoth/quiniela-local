import pytest

from quiniela_ai_studio.domain.advanced_conditions import (
    AdvancedConditions,
    HitGroup,
    HitImplication,
    HitRelation,
    advanced_from_parameters,
)
from quiniela_ai_studio.domain.filters import BasicFilters, filters_from_parameters
from quiniela_ai_studio.domain.models import Bet


def test_group_hits_and_relation_filter_columns_without_changing_pleno_or_quantity():
    group_a = HitGroup('GrupoA', (0, 1), ('1', 'X'), 2, 2)
    group_b = HitGroup('GrupoB', (2, 3), ('2', '2'), 2, 2)
    relation = HitRelation('difference', ('GrupoA', 'GrupoB'), 0, 0)
    spec = AdvancedConditions((group_a, group_b), (relation,), 0)
    bets = (Bet('1X221111111111', 'M1', 2), Bet('1X111111111111', 'M1', 3))
    assert spec.apply(bets) == (bets[0],)
    assert bets[0].pleno == 'M1' and bets[0].quantity == 2
    assert spec.failure_counts(bets) == (('GrupoA', 0), ('GrupoB', 3), ('Relación 1 (diferencia)', 3))


def test_tolerance_counts_failed_group_conditions_and_roundtrips_parameters():
    groups = (
        HitGroup('GrupoA', (0, 1), ('1', '1'), 2, 2),
        HitGroup('GrupoB', (2, 3), ('X', 'X'), 2, 2),
    )
    one_tolerated = AdvancedConditions(groups, (), 1)
    column = '11X21111111111'
    assert one_tolerated.accepts(column)
    assert not AdvancedConditions(groups, (), 0).accepts(column)
    restored = advanced_from_parameters(one_tolerated.parameters())
    assert restored == one_tolerated
    filters = BasicFilters(advanced=one_tolerated)
    assert filters_from_parameters(filters.parameters()) == filters


@pytest.mark.parametrize('args', [
    ('GrupoA', (0, 0), ('1', '1'), 0, 1),
    ('GrupoA', (0, 1), ('1',), 0, 1),
    ('GrupoA', (0, 1), ('1', 'X'), 0, 3),
])
def test_invalid_groups_are_rejected(args):
    with pytest.raises(ValueError):
        HitGroup(*args)


def test_relation_requires_known_groups_and_valid_tolerance():
    with pytest.raises(ValueError, match='no existe'):
        AdvancedConditions((HitGroup('GrupoA', (0,), ('1',), 0, 1),),
                           (HitRelation('sum', ('GrupoA', 'GrupoB'), 0, 2),), 0)
    with pytest.raises(ValueError, match='tolerancia'):
        AdvancedConditions((HitGroup('GrupoA', (0,), ('1',), 0, 1),), (), 2)


def test_legacy_single_sign_group_is_migrated_to_visual_masks():
    restored = advanced_from_parameters({"groups": [{"name": "GrupoA", "positions": [0, 2],
                                                       "signs": "1X", "minimum": 1, "maximum": 2}]})
    assert restored.groups[0].accepted == ('1', 'X')


def test_if_then_conditions_are_distinct_serializable_and_tolerable():
    groups=(HitGroup('GrupoA',(0,),('1',),0,1),HitGroup('GrupoB',(1,),('1',),0,1))
    rule=HitImplication('GrupoA',1,1,'GrupoB',1,1)
    condition=AdvancedConditions(groups,(),0,(rule,))
    bets=(Bet('1X'+'1'*12,'00'),Bet('X1'+'1'*12,'00'))
    assert condition.apply(bets)==(bets[1],)
    assert advanced_from_parameters(condition.parameters())==condition
    tolerated=AdvancedConditions(groups,(),1,(rule,))
    assert tolerated.apply(bets)==bets


def test_column_sum_uses_maximum_hits_from_selected_groups():
    groups=(HitGroup('GrupoA',(0,),('1',),0,1),HitGroup('GrupoB',(1,),('1',),0,1))
    summed=AdvancedConditions(groups,(HitRelation('sum',('GrupoA','GrupoB'),2,2),),0)
    bets=(Bet('11'+'1'*12,'00'),Bet('1X'+'1'*12,'00'))
    assert summed.apply(bets)==(bets[0],)
