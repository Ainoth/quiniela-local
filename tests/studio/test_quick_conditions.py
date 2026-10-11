"""Reference and exhaustive checks for the recovered local quick presets."""
import itertools

import pytest

from quiniela_ai_studio.domain.filters import BasicFilters, quick_conditions
from quiniela_ai_studio.domain.models import Bet


def test_strict_preset_reference_and_neutral_maximum():
    spec = quick_conditions(0)
    assert spec.variants == (5, 8)
    assert spec.x_count == (2, 6)
    assert spec.two_count == (1, 5)
    assert spec.changes == (5, 10)
    assert (spec.max_one_run, spec.max_x_run, spec.max_two_run) == (4, 2, 2)
    assert quick_conditions(10) == BasicFilters()
    assert spec.parameters()['version'] == 2


def test_relaxing_levels_keeps_more_exact_bets_and_matches_independent_oracle():
    bets = tuple(Bet(''.join(signs) + '1X21X21X', 'M1', 2)
                 for signs in itertools.product('1X2', repeat=6))
    previous = set()
    for level in range(11):
        current = set(quick_conditions(level).apply(bets))
        assert previous <= current
        previous = current
    assert previous == set(bets)
    # Oracle for the strict preset, using literal historical endpoint values.
    def accepts(column):
        signs = list(column)
        totals = {sign: sum(value == sign for value in signs) for sign in '1X2'}
        changes = sum(a != b for a, b in itertools.pairwise(signs))
        runs = {sign: 0 for sign in '1X2'}
        for sign, group in itertools.groupby(signs):
            runs[sign] = max(runs[sign], len(list(group)))
        return (5 <= totals['X'] + totals['2'] <= 8 and 2 <= totals['X'] <= 6
                and 1 <= totals['2'] <= 5 and 5 <= changes <= 10
                and runs['1'] <= 4 and runs['X'] <= 2 and runs['2'] <= 2)
    expected = tuple(bet for bet in bets if accepts(bet.column))
    assert expected and len(expected) < len(bets)
    assert quick_conditions(0).apply(bets) == expected


@pytest.mark.parametrize('level', [-1, 11, True, 2.5])
def test_invalid_level(level):
    with pytest.raises(ValueError, match='nivel'):
        quick_conditions(level)


@pytest.mark.parametrize('parameters', [{'changes': (0, 14)}, {'max_one_run': 0}])
def test_invalid_new_condition(parameters):
    with pytest.raises(ValueError):
        BasicFilters(**parameters)


def test_cancel_mid_filter_does_not_return_partial_selection():
    from quiniela_ai_studio.domain.engine import Cancelled
    bets = tuple(Bet(''.join(signs) + '1X21X21X', 'M1')
                 for signs in itertools.product('1X2', repeat=6))
    calls = 0
    def cancelled():
        nonlocal calls
        calls += 1
        return calls == 2
    with pytest.raises(Cancelled):
        quick_conditions(0).apply(bets, cancelled)
