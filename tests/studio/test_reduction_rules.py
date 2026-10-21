import math

import pytest

from quiniela_ai_studio.domain.filters import BasicFilters, filters_from_parameters
from quiniela_ai_studio.domain.models import Bet
from quiniela_ai_studio.domain.reduction_rules import ReductionRule


def rule(kind, minimum, maximum, **values):
    return ReductionRule('manual-test', kind, minimum, maximum, **values)


@pytest.mark.parametrize(
    ('column', 'expected'),
    [('1111XXXXXXXXXX', 1), ('1X1X1X1X1X1X1X', 13), ('22222222222222', 0)],
)
def test_interruption_count_matches_adjacent_sign_changes(column, expected):
    assert rule('changes', expected, expected).measure(column) == expected


def test_selected_party_scope_and_variants_are_counted():
    condition = rule('count_sign', 2, 2, sign='V', positions=(0, 2, 4, 6))
    assert condition.measure('1X2X1X2X111111') == 2
    assert condition.accepts('1X2X1X2X111111')
    assert not condition.accepts('11111111111111')


def test_overlapping_pair_patterns_and_longest_run():
    pairs = rule('pattern_occurrences', 3, 3, patterns=('11',), positions=tuple(range(14)))
    assert pairs.measure('1111XXXXXXXXXX') == 3
    run = rule('longest_run', 4, 4, sign='1')
    assert run.measure('1111XXXXXXXXXX') == 4


def test_reference_and_equal_pair_conditions():
    column = '1X21X21X21X21X'
    identical = rule('reference_hits', 14, 14, reference=column)
    assert identical.accepts(column)
    pairs = rule('equal_pairs', 7, 7, groups=tuple((i, i + 7) for i in range(7)))
    assert pairs.measure('11111112222222') == 0


def test_reference_frequency_can_remove_identical_columns_without_text_entry():
    exact_duplicate=rule('hit_frequency',0,0,references=('1'*14,),
                         reference_minimum=14,reference_maximum=14)
    assert not exact_duplicate.accepts('1'*14)
    assert exact_duplicate.accepts('X'+'1'*13)


def test_weighted_sum_and_joint_log_probability_are_distinct_measures():
    weights=((0.8,0.1,0.1),)*14
    likely=rule('weighted_sum',11.2,11.2,weights=weights)
    less_likely=rule('weighted_sum',1.4,1.4,weights=weights)
    joint=rule('weighted_log_probability',14*math.log(0.8),
               14*math.log(0.8),weights=weights)
    assert likely.measure('1'*14)==pytest.approx(11.2)
    assert less_likely.measure('X'*14)==pytest.approx(1.4)
    assert joint.accepts('1'*14)


def test_allowed_counts_and_exact_non_overlapping_run_figures():
    column='1XX2211'+'1'*7
    variants=rule('allowed_count',0,14,sign='V',allowed_values=(4,))
    assert variants.accepts(column)
    longest=rule('allowed_run_length',0,14,sign='V',allowed_values=(4,))
    assert longest.accepts(column)
    exact_figure=rule('run_frequency',0,14,sign='V',run_limits=((4,1,1),(2,0,0)))
    assert exact_figure.accepts(column)
    assert not rule('run_frequency',0,14,sign='V',run_limits=((2,1,3),)).accepts(column)


def test_sseguidos_exact_run_counts_and_partition_figures_round_trip():
    four_pairs='11X11X11X11XXX'
    pair_count=ReductionRule('streak-count-1-2','allowed_run_count',0,14,sign='1',run_length=2,
                             allowed_values=(0,1,2,3))
    assert not pair_count.accepts(four_pairs)
    assert pair_count.accepts('11X11X1'+'X'*7)

    partition='111X11XX1XXXXX'
    figure=ReductionRule('streak-figure-1-6','allowed_run_figure',0,1,sign='1',allowed_figures=('3-2-1',))
    assert figure.accepts(partition)
    assert not figure.accepts('11X11X11X1XXXX')
    restored=filters_from_parameters(BasicFilters(reduction_rules=(pair_count,figure)).parameters())
    assert restored.reduction_rules==(pair_count,figure)


def test_interruption_matrix_and_distance_figures_are_independent_and_round_trip():
    matrix=ReductionRule('interruption-matrix','allowed_interruption_profile',0,1,
        profile_kind='interruptions',allowed_profiles=((7,3),),tab_index=18)
    distance=ReductionRule('interruption-figure','allowed_interruption_figure',0,1,
        run_length=7,allowed_figures=('3-2-1-1',),tab_index=18)
    example='12X22X11221111'
    bits=(1,1,1,0,1,1,0,1,1,0,0,0,0)
    alternate=['1']
    for changed in bits:
        alternate.append(('X' if alternate[-1]=='1' else '1') if changed else alternate[-1])
    alternate=''.join(alternate)
    assert matrix.accepts(example) and distance.accepts(example)
    assert matrix.accepts(alternate) and not distance.accepts(alternate)
    spec=BasicFilters(reduction_rules=(matrix,distance),reduction_tabs_enabled=(18,))
    bets=(Bet(example,'M0'),Bet(alternate,'M0'))
    assert spec.apply(bets)==(bets[0],)
    assert filters_from_parameters(spec.parameters())==spec


def test_interruption_tab_must_be_explicitly_enabled():
    matrix=ReductionRule('interruption-matrix','allowed_interruption_profile',0,1,
        profile_kind='interruptions',allowed_profiles=((7,3),),tab_index=18)
    example='12X22X11221111'
    alternate=['1']
    for changed in (1,1,0,1,1,0,1,0,1,0,1,0,0):
        alternate.append(('X' if alternate[-1]=='1' else '1') if changed else alternate[-1])
    bets=(Bet(example,'M0'),Bet(''.join(alternate),'M0'))
    assert BasicFilters(reduction_rules=(matrix,)).apply(bets)==bets
    assert BasicFilters(reduction_rules=(matrix,),reduction_tabs_enabled=(18,)).apply(bets)==(bets[0],)


def test_joint_automatic_profile_keeps_categories_dependent():
    profile=rule('allowed_profile',0,14,profile_kind='counts',allowed_profiles=((4,2,2),))
    assert profile.accepts('1X22X'+'1'*9)
    assert not profile.accepts('1X2'+'1'*11)
    with pytest.raises(ValueError,match=r'V = X \+ 2'):
        rule('allowed_profile',0,14,profile_kind='counts',allowed_profiles=((5,2,2),))


def test_inactive_rule_and_tab_keep_configuration_but_do_not_filter():
    inactive=ReductionRule('count-values-X','allowed_count',0,14,sign='X',allowed_values=(14,),active=True,tab_index=0)
    spec=BasicFilters(reduction_rules=(inactive,),reduction_tabs_enabled=tuple(i for i in range(17) if i!=0))
    bets=(Bet('1'*14,'M0'),Bet('X'*14,'M0'))
    assert spec.apply(bets)==bets
    restored=filters_from_parameters(spec.parameters())
    assert restored.reduction_rules[0].allowed_values==(14,)
    assert 0 not in restored.reduction_tabs_enabled


def test_rules_filter_and_round_trip_with_legacy_empty_defaults():
    selected = rule('count_sign', 14, 14, sign='1')
    spec = BasicFilters(reduction_rules=(selected,))
    bets = (Bet('1' * 14, 'M0'), Bet('X' + '1' * 13, 'M0'))
    assert spec.apply(bets) == (bets[0],)
    restored = filters_from_parameters(spec.parameters())
    assert restored == spec
    assert filters_from_parameters({'variants': [0, 14]}).reduction_rules == ()


def test_invalid_rule_rejected_before_filtering():
    with pytest.raises(ValueError, match='recuento'):
        rule('count_sign', 0, 14, sign='M')
