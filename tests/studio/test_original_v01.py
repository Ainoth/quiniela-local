"""Aceptación del encargo original: fixtures, streaming, capas y experiencia Local."""

import json
import tracemalloc
from dataclasses import replace
from itertools import islice
from pathlib import Path

import pytest

from quiniela_ai_studio.application.services import SystemService
from quiniela_ai_studio.domain.engine import Cancelled, evaluate, iter_bets
from quiniela_ai_studio.domain.selection import GameRuleset, Selection
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.files import (
    read_system,
    read_txt,
    write_development,
    write_system,
)
from quiniela_ai_studio.infrastructure.storage import Repository

ROOT = Path(__file__).resolve().parents[2]


def test_original_fixture_twelve_bets_900_cents_and_roundtrip(tmp_path):
    round_, system = read_system(ROOT / "fixtures/seleccion_demo_v1.json")
    assert system.quantity == 12 and system.cost(round_) == 900
    assert {b.pleno for b in system.bets} == {"01", "11"}
    path = tmp_path / "project.json"
    write_system(path, system, round_)
    restored_round, restored = read_system(path)
    assert restored == system and restored_round == round_
    original = json.loads(restored.parameters)["selection_project"]
    assert original["draw_id"] == "DEMO-2026-01" and original["ruleset_id"] == "demo-v1"
    txt = tmp_path / "bets.txt"
    write_development(txt, system, round_)
    assert read_txt(txt) == system.bets
    data = json.loads((ROOT / "fixtures/resultados_demo_v1.json").read_text())
    result = evaluate(
        system.bets,
        "".join(data["results14"]),
        "".join(data["full15"]),
        finalized=(True,) * 14,
    )
    assert result["counts"][14] == 2 and result["counts"][15] == 1


def test_four_million_universe_first_items_stay_lazy():
    tracemalloc.start()
    stream = iter_bets(("1X2",) * 14, ("M0",))
    first = list(islice(stream, 5))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert len(first) == 5 and peak < 1_000_000
    assert Selection(("1X2",) * 14, ("M0",)).quantity == 4_782_969


def test_stream_export_more_than_preview_and_cancellation_atomic(tmp_path):
    repo = Repository(tmp_path / "studio.sqlite3")
    round_ = demo_round()
    repo.save_round(round_)
    service = SystemService(repo)
    system = service.new(round_)
    system = service.edit(system, ("1X",) * 10 + ("1",) * 4, (False,) * 14, "M0")
    txt = tmp_path / "large.txt"
    assert write_development(txt, system, round_) == 1024
    assert len(txt.read_text().splitlines()) == 1024
    json_file = tmp_path / "large.json"
    assert write_development(json_file, system, round_, format="json") == 1024
    _, loaded = read_system(json_file)
    assert loaded.quantity == 1024
    original = txt.read_bytes()
    with pytest.raises(Cancelled):
        write_development(txt, system, round_, cancelled=lambda: True)
    assert txt.read_bytes() == original
    assert repo.load(system.system_id).bets == ()
    repo.close()


def test_rule_price_changes_new_systems_only(tmp_path):
    repo = Repository(tmp_path / "studio.sqlite3")
    round_ = demo_round()
    repo.save_round(round_)
    service = SystemService(repo)
    system = service.imported(
        round_, "Guardado", tuple(iter_bets(("1",) * 14, ("00",)))
    )
    changed = replace(round_, price_cents=90, rules_version="demo-90c")
    repo.change_rules(changed)
    assert system.cost(changed) == 75
    fresh = service.imported(changed, "Nuevo", system.bets)
    assert fresh.cost(changed) == 90
    assert any(row[1] == "change_rules" for row in repo.audit())
    repo.close()


@pytest.mark.parametrize(
    "base,plenos",
    [
        (("1",) * 13, ("00",)),
        (("1",) * 14, ()),
        (("1",) * 14, ("",)),
        (("1",) * 14, ("00", "00")),
    ],
)
def test_invalid_selection(base, plenos):
    with pytest.raises(ValueError):
        Selection(base, plenos)


def test_elige8_separate_and_unavailable():
    with pytest.raises(ValueError):
        GameRuleset("demo", 75, "elige8")
