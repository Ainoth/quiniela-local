"""Published matrices and explicit Pleno choices, verified independently."""
import json
from dataclasses import replace
from itertools import product

import pytest

from quiniela_ai_studio.application.services import SystemService
from quiniela_ai_studio.domain import engine
from quiniela_ai_studio.domain.reduction_tables import TABLES
from quiniela_ai_studio.domain.reductions import plan_reduction, reduced_bets
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.files import (
    read_system,
    write_development,
    write_system,
)
from quiniela_ai_studio.infrastructure.storage import Repository


@pytest.mark.parametrize('table,count,minimum',tuple(zip(TABLES,(9,16,24,64,81,132),(13,13,13,13,12,9))))
def test_published_matrix_cardinality_and_exact_conditional_coverage(table,count,minimum):
    assert len(table.patterns)==len(set(table.patterns))==count
    worst=14
    for outcome in product(*(range(width) for width in table.widths)):
        best=max(14-len(table.widths)+sum(a==b for a,b in zip(outcome,column)) for column in table.patterns)
        worst=min(worst,best)
    assert worst==minimum==table.minimum_hits


def test_reduction_one_literal_columns_and_extra_direct_with_multiple_plenos():
    base=('1X2',)*4+('X2',)+('1',)*9
    plan=plan_reduction(base,('01','M2'),1,(0,1,2,3))
    assert (plan.before,plan.after)==(324,36)
    bets=reduced_bets(plan)
    assert len(bets)==36
    columns={b.column[:4] for b in bets}
    assert columns=={'1111','1XXX','1222','X1X2','XX21','X21X','212X','2X12','22X1'}
    assert {b.column[4] for b in bets}=={'X','2'}
    assert {b.pleno for b in bets}=={'01','M2'}


def test_doubles_mapping_and_selected_ordinals():
    base=('1',)*2+('X2',)*7+('2',)*5
    bets=reduced_bets(plan_reduction(base,('M1',),2,tuple(reversed(range(2,9)))))
    assert len(bets)==16
    assert all(b.column[:2]=='11' and set(b.column[2:9])<={'X','2'} and b.column[9:]=='2'*5 for b in bets)


def test_multiple_pleno_cost_persistence_roundtrip_and_streaming(tmp_path):
    repo=Repository(tmp_path/'studio.sqlite3');round_=demo_round();repo.save_round(round_)
    service=SystemService(repo);system=service.new(round_)
    system=service.edit(system,('1X',)+('1',)*13,(False,)*14,'',pleno_choices=['01','2M'])
    assert system.plenos==('02','0M','12','1M')
    bets=engine.generate(system.base,system.plenos)
    system=service.generated(system,bets)
    assert system.quantity==8 and system.cost(round_)==600
    assert repo.load(system.system_id).plenos==system.plenos
    path=tmp_path/'multiple.json';write_system(path,system,round_)
    assert read_system(path)[1].bets==bets
    path=tmp_path/'direct.txt';write_development(path,replace(system,bets=()),round_)
    assert len(path.read_text().splitlines())==8
    copied=service.reduced_copy(service.edit(system,('1X2',)*4+('1',)*10,(False,)*14,system.pleno),
                                plan_reduction(('1X2',)*4+('1',)*10,system.plenos,1,(0,1,2,3)),
                                reduced_bets(plan_reduction(('1X2',)*4+('1',)*10,system.plenos,1,(0,1,2,3))))
    assert copied.quantity==36 and copied.system_id!=system.system_id
    assert json.loads(copied.parameters)['reduction']==1
    repo.close()


def test_reduction_invalid_groups_and_generation_global_pleno_limit():
    with pytest.raises(ValueError):plan_reduction(('1X2',)*4+('1',)*10,('M1',),1,(0,0,2,3))
    with pytest.raises(ValueError):plan_reduction(('1X',)*4+('1',)*10,('M1',),1,(0,1,2,3))
    with pytest.raises(ValueError):engine.generate(('1X2',)*10+('1',)*4,('01','M2'))


@pytest.mark.parametrize('result,flags,p15final,expected',[
    ('1'*14,(True,)*14,True,1),('1'*13+'X',(True,)*14,True,0),
    ('1'*14,(True,)*14,False,0),('1'*13+'-',(True,)*13+(False,),True,0),
])
def test_pleno_category_requires_all_fourteen_and_final_goals(result,flags,p15final,expected):
    from quiniela_ai_studio.domain.models import Bet
    outcome=engine.evaluate((Bet('1'*14,'01'),),result,'01',finalized=flags,pleno_final=p15final)
    assert outcome['counts'][15]==expected
    assert outcome['rows'][0]['full15_hit']==bool(expected)


def test_imported_non_cartesian_pleno_pairs_survive_base_template(tmp_path):
    from quiniela_ai_studio.domain.models import Bet
    repo=Repository(tmp_path/'studio.sqlite3');round_=demo_round();repo.save_round(round_)
    service=SystemService(repo)
    source=service.imported(round_,'Parejas exactas',(Bet('1'*14,'00'),Bet('1'*14,'11')))
    assert source.plenos==('00','11')
    edited=service.template(source,0)
    assert edited.plenos==('00','11')
    assert engine.generate(edited.base,edited.plenos)==(Bet('1'*14,'00'),Bet('1'*14,'11'))
    repo.close()
