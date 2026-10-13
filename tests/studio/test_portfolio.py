"""Fixtures sintéticos explícitos, sin apuestas reales ni pagos."""
import math
from collections import Counter
from dataclasses import replace
from itertools import combinations
from pathlib import Path

import pytest

from quiniela_ai_studio.domain import engine
from quiniela_ai_studio.domain.coverage import (
    make_universe,
    pleno_joint,
    verify_coverage,
)
from quiniela_ai_studio.domain.models import Bet
from quiniela_ai_studio.domain.portfolio import (
    OptimizationConfig,
    normalized_percentages,
    optimize_portfolio,
    probabilities_from_odds,
)
from quiniela_ai_studio.domain.reductions import plan_reduction, reduced_bets
from quiniela_ai_studio.domain.tickets import group_tickets
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.files import read_txt
from quiniela_ai_studio.infrastructure.ticket_files import (
    parse_ticket_text,
    read_ticket_file,
    write_ticket_file,
)

BASE72=('1X',)*3+('1X2',)*2+('1',)*9


def test_72_budget_quality_reproducibility_and_tradeoff():
    bets=engine.generate(BASE72,'M0');sport=demo_round().snapshot('sport')
    config=OptimizationConfig(500,75,seed=123)
    result=optimize_portfolio(bets,BASE72,config,sport)
    again=optimize_portfolio(tuple(reversed(bets)),BASE72,config,sport)
    assert len(bets)==72 and len(result.bets)==6
    assert result.bets==again.bets and len(set(result.bets))==6
    report=result.report;after=report['after'];old=report['comparisons']['v0.1.13_probables']
    assert report['cost_cents']==450 and report['remaining_cents']==50
    assert after['weighted']['13']>old['weighted']['13']
    assert after['weighted']['12']>old['weighted']['12']
    assert after['mean_distance']>old['mean_distance']
    assert after['probability_mass']<old['probability_mass']  # No ocultar el compromiso.
    assert after['minimum_hits']==11 and after['universe_total']==72
    assert 'aproximación' in report['optimality']
    assert len(report['marginal'])==6
    assert all(x['gain_13']>=-1e-12 for x in report['marginal'])


def test_small_exhaustive_matches_independent_oracle():
    base=('1X',)*2+('1',)*12;bets=engine.generate(base,'01');sport=demo_round().snapshot('sport')
    result=optimize_portfolio(bets,base,OptimizationConfig(150,75),sport)
    universe=make_universe(base,sport)
    denominator=engine.probability_mass(bets,sport)
    scores=[]
    for count in (1,2):
        for subset in combinations(bets,count):
            report=verify_coverage(subset,universe)
            scores.append(.45*report['weighted']['13']+.25*report['weighted']['12']+.25*engine.probability_mass(subset,sport)/denominator+.05*report['mean_distance']/14)
    assert math.isclose(result.report['objective_score'],max(scores),abs_tol=1e-12)
    assert 'óptimo global' in result.report['optimality']


def test_reduction_three_216_actual_columns_independent_guarantee():
    base=('1X',)*3+('1X2',)*3+('2',)*8
    plan=plan_reduction(base,('M0',),3,tuple(range(6)))
    bets=reduced_bets(plan)
    profile=verify_coverage(bets,make_universe(base))
    assert len(bets)==24 and profile['universe_total']==216
    assert profile['minimum_hits']==13
    assert profile['uniform']['13']==1
    damaged=verify_coverage(bets[:1],make_universe(base))
    assert damaged['minimum_hits']<13


def test_probability_optimum_and_no_duplicate_stakes():
    bets=engine.generate(BASE72,'M0');sport=demo_round().snapshot('sport')
    result=optimize_portfolio(bets+(bets[0],),BASE72,OptimizationConfig(500,75,objective='probability'),sport)
    best=sorted(bets,key=lambda b:(-engine.log_probability(b.column,sport),b.column,b.pleno))[:6]
    assert set(result.bets)==set(best)
    assert 'óptimo global' in result.report['optimality']
    assert len(result.bets)==len(set(result.bets))


def test_filters_scope_and_missing_probabilities():
    bets=engine.generate(BASE72,'M0')
    result=optimize_portfolio(bets,BASE72,OptimizationConfig(500,75),eligible=lambda b:b.column.count('X')>=2)
    assert all(b.column.count('X')>=2 for b in result.bets)
    assert result.report['rejected_by_conditions']>0 and result.report['after']['weighted'] is None
    assert result.report['after']['universe_total']==72
    narrowed=optimize_portfolio(bets,BASE72,OptimizationConfig(500,75,universe_scope='candidates'),eligible=lambda b:b.column.count('X')>=2)
    assert narrowed.report['after']['universe_total']<72
    with pytest.raises(ValueError,match='deportiva'):
        optimize_portfolio(bets,BASE72,OptimizationConfig(500,75,objective='probability'))
    with pytest.raises(ValueError,match='ROI'):
        optimize_portfolio(bets,BASE72,OptimizationConfig(500,75,objective='expected'))


@pytest.mark.parametrize('bad', [(-1,.5,.5),(float('nan'),0,0),(0,0,0),(True,0,0),(40,40,40)])
def test_invalid_percentages(bad):
    with pytest.raises(ValueError):normalized_percentages([bad]*14)


def test_normalization_and_margin():
    assert normalized_percentages([(50,30,20)]*14)[0]==(.5,.3,.2)
    assert math.isclose(sum(probabilities_from_odds([(2,3.5,4)]*14)[0]),1)
    with pytest.raises(ValueError):probabilities_from_odds([('x',3,4)]*14)


def test_cancel_and_sampled_guarantee_not_claimed():
    with pytest.raises(engine.Cancelled):
        optimize_portfolio(engine.generate(BASE72,'00'),BASE72,OptimizationConfig(500,75),cancelled=lambda:True)
    universe=make_universe(('1X2',)*14,limit=100,seed=7)
    report=verify_coverage((Bet('1'*14,'00'),),universe)
    assert report['minimum_hits'] is None and report['status'].startswith('estimada')
    assert universe.outcomes==make_universe(('1X2',)*14,limit=100,seed=7).outcomes


def test_explicit_pleno_model_and_preserved_pairs():
    sport=replace(demo_round().snapshot('sport'),pleno_values=((.1,.5,.3,.1),(.4,.1,.2,.3)))
    assert math.isclose(sum(pleno_joint(sport).values()),1)
    bets=tuple(Bet('1'*14,p) for p in ('00','10','MM'))
    result=optimize_portfolio(bets,('1',)*14,OptimizationConfig(150,75,objective='probability',include_pleno_probability=True),sport)
    assert len(result.bets)==2 and all(b in bets for b in result.bets)
    assert any('independencia' in w for w in result.report['warnings'])


def test_tulotero_groups_three_plenos_and_minimums(tmp_path):
    bets=tuple(Bet('1'*13+s,p) for p in ('M0','M1','20') for s in '1X')
    tickets=group_tickets(bets)
    assert len(tickets)==3 and all(len(t.bets)==2 for t in tickets)
    for format in ('csv','txt'):
        path=tmp_path/f'tickets.{format}';write_ticket_file(path,bets,75,format=format)
        assert Counter(read_ticket_file(path,format))==Counter(bets)
    with pytest.raises(ValueError,match='No se cambian'):
        group_tickets((Bet('1'*14,'00'),))
    nine=tuple(Bet('1'*13+s,'00') for s in '1X2')*3
    assert sorted(len(t.bets) for t in group_tickets(nine))==[2,7]
    with pytest.raises(ValueError):parse_ticket_text('Boleto;mal','csv')


def test_channel_constraints_in_optimizer_and_baselines():
    bets=engine.generate(('1X',)*2+('1',)*12,('00','11','M0'))
    result=optimize_portfolio(bets,('1X',)*2+('1',)*12,OptimizationConfig(450,75,min_per_pleno=2),demo_round().snapshot('sport'))
    assert group_tickets(result.bets)
    assert all(r['channel_feasible'] for r in result.report['comparisons'].values())
    assert result.report['cost_cents']<=450


@pytest.mark.parametrize('name', [
    'Mi quiniela normal-26-27-J13-v33.txt',
    'Mi reducida · Reducida 1 · Reducida 3 · Reducida 3 · Reducida 3-26-27-J13-v1.txt',
])
def test_personal_fixture_if_available_without_copying_into_git(name):
    path=Path(__file__).resolve().parents[2]/name
    if not path.exists():pytest.skip('TXT personal no versionado; no se inventa su contenido.')
    bets=read_txt(path);base=engine.union_base(bets,('1',)*14)
    report=verify_coverage(bets,make_universe(base,limit=10000))
    assert all(b.pleno and len(b.column)==14 for b in bets)
    assert report['status']=='exacta'
    if len(bets)==24 and report['universe_total']==216:assert report['minimum_hits']==13
