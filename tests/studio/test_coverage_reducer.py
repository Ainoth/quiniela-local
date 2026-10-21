from itertools import product

from quiniela_ai_studio.domain.coverage import make_universe, verify_coverage
from quiniela_ai_studio.domain.coverage_reducer import (
    CoverageReductionConfig,
    reduce_coverage,
)
from quiniela_ai_studio.domain.models import Bet


def small_universe_bets():
    base=('1X','1X')+('1',)*12
    bets=tuple(Bet(''.join(signs)+('1'*12),'M0') for signs in product('1X',repeat=2))
    return base,bets


def test_hermes_returns_exactly_verified_full_14_cover():
    base,bets=small_universe_bets()
    result=reduce_coverage(bets,base,CoverageReductionConfig(14,300,75,'hermes',scenario_limit=20))
    assert len(result.bets)==4
    assert result.report['guarantee'] is True
    assert result.report['coverage']['minimum_hits']==14
    assert result.report['universe_total']==4


def test_athena_covers_all_two_match_results_to_13_with_two_columns():
    base,bets=small_universe_bets()
    result=reduce_coverage(bets,base,CoverageReductionConfig(13,150,75,'athena',scenario_limit=20))
    assert len(result.bets)==2
    assert result.report['guarantee'] is True
    assert result.report['coverage']['uniform']['13']==1.0


def test_artemisa_proves_minimum_number_for_small_cover():
    base,bets=small_universe_bets()
    result=reduce_coverage(bets,base,CoverageReductionConfig(13,300,75,'artemisa',scenario_limit=20))
    assert len(result.bets)==2
    assert result.report['search_optimal'] is True
    assert result.report['guarantee'] is True


def test_sampled_universe_is_never_reported_as_a_guarantee():
    base,bets=small_universe_bets()
    result=reduce_coverage(bets,base,CoverageReductionConfig(14,300,75,'hermes',scenario_limit=2,seed=7))
    assert result.report['universe_exact'] is False
    assert result.report['guarantee'] is False
    assert result.report['coverage']['minimum_hits'] is None


def test_independent_verifier_matches_small_exact_universe():
    base,bets=small_universe_bets()
    universe=make_universe(base,limit=20)
    report=verify_coverage(bets,universe)
    assert report['uniform']['14']==1.0
