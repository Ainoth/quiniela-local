from dataclasses import replace
from datetime import date
import json
import sqlite3
import time

import pytest
from quiniela_studio.demo import demo_round
from quiniela_studio.domain import Bet, ProbabilitySnapshot
from quiniela_studio.engine import (generate, size, coverage_template, probability_mass,
    optimize, evaluate, Cancelled, column_id, decode_column)
from quiniela_studio.files import read_txt, write_txt, write_system, read_system
from quiniela_studio.providers import scrutiny_record, load_win1x2, migrate_legacy
from quiniela_studio.services import SystemService
from quiniela_studio.storage import Repository


@pytest.fixture
def repo(tmp_path):
    repo=Repository(tmp_path/'studio.sqlite3');repo.save_round(demo_round())
    yield repo
    repo.close()


def test_T01_cartesian_and_encoding():
    bets=generate(('1X','1','1X2')+('1',)*11,'M0')
    assert len(bets)==6 and len({b.column for b in bets})==6
    assert size(('1X2',)*14)==4_782_969
    for value in range(3**8):
        assert column_id(decode_column(value))==value
    assert decode_column(3**14-1)=='2'*14
    assert column_id('2'*14)==3**14-1


@pytest.mark.parametrize('level',range(11))
def test_T03_levels_and_locks(level):
    base=('X2',)+('1',)*13
    locks=(True,)+(False,)*13
    assert coverage_template(base,locks,level)[0]=='X2'
    assert size(coverage_template(('1',)*14,(False,)*14,10))==3456


@pytest.mark.parametrize('row',[(.5,.5,.2),(-.1,.5,.6),(float('nan'),.5,.5),(float('inf'),0,0),(50,30,20)])
def test_T04_invalid_sources(row):
    with pytest.raises(ValueError):
        ProbabilitySnapshot('sport','test',demo_round().captured_at,(row,)*14)


def test_T04_public_not_sport():
    round_=replace(demo_round(),snapshots=(demo_round().snapshot('public'),))
    assert round_.snapshot('sport') is None
    assert round_.snapshot('public').kind=='public'


def test_T02_versions_restart_and_season_isolation(repo):
    service=SystemService(repo);round_=repo.round('DEMO/J01')
    original=service.new(round_)
    edited=service.edit(original,('1X',)+('1',)*13,(False,)*14,'M2')
    generated=service.generated(edited,generate(edited.base,edited.pleno))
    path=repo.path
    repo2=Repository(path)
    assert repo2.load(original.system_id)==generated
    assert repo2.load(original.system_id,1)==original
    other=replace(round_,number=2,mode='past');repo.save_round(other)
    historical=service.imported(other,'Revisión',(Bet('X'*14,'00'),))
    with pytest.raises(ValueError):service.edit(historical,('1',)*14,(False,)*14,'00')
    assert len(repo.systems(other.key))==1 and len(repo.systems(round_.key))==1
    with pytest.raises(ValueError):repo.save(replace(generated,round_key=other.key,revision=4))
    repo2.close()


def test_T06_optimization_origin_budget_preserved(repo):
    service=SystemService(repo);system=service.new(repo.round('DEMO/J01'))
    system=service.edit(system,('1X2',)*3+('1',)*11,(False,)*14,'M0')
    system=service.generated(system,generate(system.base,system.pleno))
    reduced=service.optimized(system,151)
    assert reduced.quantity==2 and reduced.cost(repo.round(system.round_key))==150
    assert set(reduced.bets)<=set(system.bets)
    assert repo.load(system.system_id,system.revision)==system
    assert reduced.quantity!=size(reduced.base) or reduced.quantity==2
    with pytest.raises(ValueError):service.optimized(system,74)


def test_frozen_sources_and_price(repo):
    round_=repo.round('DEMO/J01');service=SystemService(repo)
    system=service.new(round_);system=service.edit(system,('1',)*14,(False,)*14,'00')
    system=service.generated(system,generate(system.base,system.pleno))
    changed=replace(round_,price_cents=999,snapshots=())
    repo.save_round(changed)
    assert system.cost(changed)==75
    optimized=service.optimized(system,75)
    assert optimized.quantity==1
    assert optimized.round_snapshot==system.round_snapshot


def test_T08_unique_probability_and_quantity():
    snapshot=demo_round().snapshot('sport')
    mass=probability_mass((Bet('1'*14,'00',4),Bet('1'*14,'11')),snapshot)
    assert mass==pytest.approx(.5**14)
    zeros=ProbabilitySnapshot('sport','test',snapshot.captured_at,((0,.5,.5),)*14)
    assert probability_mass((Bet('1'*14,'00'),),zeros)==0
    assert optimize((Bet('1'*14,'00',5),Bet('1'*14,'00',3)),225,75)==(Bet('1'*14,'00',3),)


def pre_record(number=10):
    # Jornada de dos columnas pegada al primer número de acertantes.
    return str(number).ljust(2)+''.join(str(n).ljust(7) for n in (1,2,3,4,5,6))+''.join(a.ljust(10) for a in ('1000,01','100,02','20,03','5,04','2,05','1,06'))+'1'*14+'B'+'ABCDEF'*15


def test_T09_fixed_pre_fields():
    scrutiny=scrutiny_record(pre_record())
    assert scrutiny['round_no']==10
    assert scrutiny['prizes'][15]==100001 and scrutiny['winners'][14]==2
    assert scrutiny['pleno']=='2M'
    assert scrutiny_record(pre_record().replace('1'*14,'-'*14)) is None


def test_T10_accumulated_prizes_and_pending():
    bets=(Bet('1'*14,'2M',2),Bet('1'*14,'11'),Bet('2'+'1'*13,'2M'))
    result=evaluate(bets,'1'*14,'2M',(True,)*14,{14:10000,15:100000,13:1000},True)
    assert result['counts'][14]==3 and result['counts'][15]==2 and result['counts'][13]==1
    assert result['prize_cents']==231000
    pending=evaluate(bets,'1'+'-'*13)
    assert pending['known']==1 and pending['prize_cents'] is None
    assert pending['rows'][0]['confirmed']==0 and pending['rows'][0]['maximum']==14
    with pytest.raises(ValueError):evaluate(bets,'-'*14,prizes={14:10000},official=True)


def test_T12_roundtrip_quantity_and_full_export(repo,tmp_path):
    bets=tuple(Bet(('1X'*7 if i%2 else '2'*14),'M0') for i in range(150))
    txt=tmp_path/'bets.txt';write_txt(txt,bets)
    assert len(txt.read_text().splitlines())==150
    imported=read_txt(txt);assert sum(b.quantity for b in imported)==150 and len(imported)==2
    assert sum(b.quantity for b in read_txt(txt,False))==2
    service=SystemService(repo);round_=repo.round('DEMO/J01')
    system=service.imported(round_,'Archivo',imported)
    target=tmp_path/'system.json';write_system(target,system,round_)
    assert read_system(target)==(round_,system)
    with pytest.raises(ValueError):write_txt(txt,(Bet('1'*14),))


def test_invalid_txt_json_and_cross_round(repo,tmp_path):
    path=tmp_path/'bad.txt';path.write_text('1'*13)
    with pytest.raises(ValueError):read_txt(path)
    path.write_text('1'*14+'33')
    with pytest.raises(ValueError):read_txt(path)
    service=SystemService(repo);system=service.new(repo.round('DEMO/J01'))
    path=tmp_path/'bad.json';write_system(path,system,repo.round('DEMO/J01'))
    payload=json.loads(path.read_text());payload['round']['number']=2;path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):read_system(path)


def test_T16_cancel_and_limit_keeps_origin(repo):
    service=SystemService(repo);system=service.new(repo.round('DEMO/J01'))
    started=time.monotonic()
    with pytest.raises(Cancelled):generate(('1X',)*14,'00',cancelled=lambda:True)
    assert time.monotonic()-started<1
    assert repo.load(system.system_id)==system
    with pytest.raises(ValueError):generate(('1X2',)*14,'00')


def test_stale_generation_rejected(repo):
    service=SystemService(repo);system=service.new(repo.round('DEMO/J01'))
    service.edit(system,('X',)*14,(False,)*14,'00')
    with pytest.raises(ValueError):service.generated(system,generate(system.base,'00'))


def test_backup_integrity_and_corruption_detection(repo,tmp_path):
    service=SystemService(repo);system=service.new(repo.round('DEMO/J01'))
    target=tmp_path/'backup.sqlite3';repo.backup(target)
    with sqlite3.connect(target) as db:assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    with pytest.raises(ValueError):repo.backup(repo.path)
    with repo.db:repo.db.execute("UPDATE versions SET hash='incorrect' WHERE system_id=?",(system.system_id,))
    with pytest.raises(ValueError):repo.load(system.system_id)


def test_T02_migration_backup_unassigned(repo,tmp_path):
    round_=replace(repo.round('DEMO/J01'),season='26-27',number=10,mode='past');repo.save_round(round_)
    path=tmp_path/'pronosticos.json';payload=dict(predictions={'26-27-10-1':'1X','26-27-10-15':'M-0'},development_columns=['1'*14])
    path.write_text(json.dumps(payload));original=path.read_bytes()
    count,target=migrate_legacy(path,repo,SystemService(repo))
    assert count==1 and path.read_bytes()==original and (target/path.name).read_bytes()==original
    assert json.loads((target/'sin-asignar.json').read_text())['development_columns']==['1'*14]
    assert repo.systems(round_.key)[0].bets==()
    assert repo.systems(round_.key)[0].base[0]=='1X'


def test_local_win1x2_uses_fixed_round_and_provider_ids(tmp_path):
    (tmp_path/'PRE26-27.txt').write_text(pre_record(10),encoding='cp1252')
    (tmp_path/'FEC26-27.txt').write_text('10:09/10/2026')
    rounds=load_win1x2(tmp_path,today=date(2026,10,9))
    # Un PRE con escrutinio definitivo ya es histórico, incluso en su fecha nominal.
    assert rounds[0].number==10 and rounds[0].mode=='past'
    assert rounds[0].matches[0].home_id.startswith('win1x2:26-27:')
    assert rounds[0].snapshot('sport') is None
