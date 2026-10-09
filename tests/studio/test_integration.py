"""Integración sintética de adaptadores antiguos y persistencia Qt, sin red real."""

import json
import sqlite3
import zipfile
from dataclasses import replace
from datetime import date, timedelta
from io import BytesIO

import pytest

import data_updater
from live_results import LiveMatch
from pc_store import SystemStore
from quiniela_studio.domain import Bet
from quiniela_studio.engine import Cancelled
from quiniela_studio.integration import (
    live_for_round,
    prepare_data,
    public_snapshot,
    read_legacy_systems,
    reconcile_import,
    scrutiny_from_cache,
)
from quiniela_studio.providers import load_win1x2
from quiniela_studio.services import SystemService
from quiniela_studio.storage import Repository


def records():
    codes = "ABCDEF" * 15
    future = "12" + (" " * 102) + ("-" * 14) + " " + codes
    historical = (
        "11"
        + "".join(str(1).rjust(7) for _ in range(6))
        + "".join("2,00".rjust(10) for _ in range(6))
        + "1" * 14
        + "0"
        + codes
    )
    return historical + "\n" + future


def data_folder(path):
    path.mkdir(exist_ok=True)
    (path / "PRE26-27.TXT").write_text(records(), encoding="cp1252")
    day = date.today()
    (path / "FEC26-27.TXT").write_text(
        f"11:{day:%d/%m/%Y}\n12:{day + timedelta(days=1):%d/%m/%Y}"
    )
    (path / "EQ126-27.TXT").write_text(
        "ABC-Equipo A\nDEF-Equipo B\n", encoding="cp1252"
    )
    return path


def xml(round_no=12, home="Equipo A", values=(50, 30, 20), season=2027):
    return (
        f'<quinielista><porcentajes temporada="{season}" jornada="{round_no}">'
        + "".join(
            f'<partido num="{n}" local="{home}" visitante="Equipo B" p_jugados_1="{values[0]}" p_jugados_X="{values[1]}" p_jugados_2="{values[2]}"/>'
            for n in range(1, 16)
        )
        + "</porcentajes></quinielista>"
    ).encode()


def archive(folder):
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        for p in folder.iterdir():
            z.writestr("DATOSG/" + p.name, p.read_bytes())
    return stream.getvalue()


def test_folder_zip_and_online_have_same_identity_and_public_only(
    tmp_path, monkeypatch
):
    folder = data_folder(tmp_path / "source")
    a = prepare_data(tmp_path / "cache", folder=folder)
    z = tmp_path / "datos.zip"
    z.write_bytes(archive(folder))
    b = prepare_data(tmp_path / "cache", zip_path=z)
    monkeypatch.setattr(
        data_updater,
        "_download",
        lambda url: archive(folder) if url == data_updater.WIN1X2_ZIP else xml(),
    )
    c = prepare_data(tmp_path / "cache", online=True)
    assert (
        [r.key for r in a.rounds]
        == [r.key for r in b.rounds]
        == [r.key for r in c.rounds]
    )
    current = next(r for r in c.rounds if r.mode == "current")
    assert current.key == "26-27/J12" and current.editable
    assert current.snapshot("public").values[0] == (0.5, 0.3, 0.2)
    assert current.snapshot("sport") is None
    assert folder != c.directory and (folder / "PRE26-27.TXT").exists()
    assert next(r for r in c.rounds if r.number == 11).mode == "past"


@pytest.mark.parametrize(
    "entry", ["../evil.txt", "DATOSG/../evil", "DATOSG/..", "DATOSG/x/evil"]
)
def test_malicious_zip_no_active_change(tmp_path, entry):
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr(entry, "bad")
    path = tmp_path / "bad.zip"
    path.write_bytes(stream.getvalue())
    with pytest.raises(ValueError):
        prepare_data(tmp_path / "cache", zip_path=path)
    assert list((tmp_path / "cache").iterdir()) == []


def test_duplicates_and_cancellation_leave_no_staged_files(tmp_path):
    folder = data_folder(tmp_path / "source")
    with pytest.raises(Cancelled):
        prepare_data(tmp_path / "cache", folder=folder, cancelled=lambda: True)
    assert list((tmp_path / "cache").iterdir()) == []
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("DATOSG/FEC26-27.TXT", "one")
        z.writestr("DATOSG/fec26-27.txt", "two")
    with pytest.raises(ValueError):
        data_updater.unpack_win1x2(stream.getvalue(), tmp_path / "unused")


@pytest.mark.parametrize(
    "payload",
    [
        xml(round_no=11),
        xml(home="Otro equipo"),
        xml(values=(50, 30, 40)),
        xml(season=2026),
        b'<!DOCTYPE x [<!ENTITY a "boom">]><x/>',
    ],
)
def test_public_crossed_or_invalid_rejected(tmp_path, payload):
    round_ = load_win1x2(data_folder(tmp_path / "source"))[-1]
    with pytest.raises(ValueError):
        public_snapshot(round_, payload)


def test_failed_percentage_preserves_previous_snapshot_and_bets(tmp_path, monkeypatch):
    folder = data_folder(tmp_path / "source")
    round_ = public_snapshot(load_win1x2(folder)[-1], xml())
    repo = Repository(tmp_path / "studio.sqlite3")
    repo.save_round(round_)
    service = SystemService(repo)
    system = service.imported(round_, "Guardado", (Bet("1" * 14, "M0", 3),))
    snapshot = system.round_snapshot
    monkeypatch.setattr(
        data_updater,
        "_download",
        lambda url: (
            archive(folder) if url == data_updater.WIN1X2_ZIP else xml(round_no=11)
        ),
    )
    prepared = prepare_data(tmp_path / "cache", online=True)
    reconciled = reconcile_import(prepared, repo.rounds())
    repo.import_rounds(reconciled.rounds, reconciled.directory)
    assert reconciled.warnings
    assert repo.round(round_.key).snapshot("public") == round_.snapshot("public")
    assert repo.load(system.system_id).round_snapshot == snapshot
    assert repo.load(system.system_id).bets == system.bets
    repo.close()


def test_manual_round_protected(tmp_path):
    p = prepare_data(tmp_path / "cache", folder=data_folder(tmp_path / "source"))
    existing = replace(p.rounds[-1], source="JSON manual")
    merged = reconcile_import(p, [existing])
    assert existing.key not in [r.key for r in merged.rounds]
    assert merged.warnings


def test_sources_refresh_new_version_preserves_price_and_exact_bets(tmp_path):
    round_ = load_win1x2(data_folder(tmp_path / "source"))[-1]
    repo = Repository(tmp_path / "studio.sqlite3")
    repo.save_round(round_)
    service = SystemService(repo)
    original = service.imported(round_, "Guardado", (Bet("X" * 14, "M2", 2),))
    repo.save_round(replace(public_snapshot(round_, xml()), price_cents=100))
    updated = service.refresh_sources(original)
    assert updated.bets == original.bets and updated.cost(repo.round(round_.key)) == 150
    assert json.loads(updated.round_snapshot)["snapshots"][0]["kind"] == "public"
    assert repo.load(original.system_id, 1) == original
    repo.close()


def test_cache_scrutiny_bound_to_team_identity(tmp_path):
    folder = data_folder(tmp_path / "source")
    historical = load_win1x2(folder)[0]
    result = scrutiny_from_cache(folder, historical)
    assert result["result"] == "1" * 14 and result["prizes"][14] == 200
    wrong = replace(
        historical,
        matches=(replace(historical.matches[0], home_id="other:ZZZ"),)
        + historical.matches[1:],
    )
    with pytest.raises(ValueError):
        scrutiny_from_cache(folder, wrong)


def test_legacy_sqlite_readonly_round_separation_quantities_and_idempotence(tmp_path):
    rounds = load_win1x2(data_folder(tmp_path / "source"))
    path = tmp_path / "old.sqlite3"
    old = SystemStore(path)
    sid = old.create(
        "26-27",
        12,
        "Anterior",
        {
            "picks": ["1X"] * 14,
            "columns": ["1" * 14, "1" * 14, "X" * 14],
            "original": ["1" * 14, "X" * 14, "2" * 14],
            "pleno": "M-0",
        },
    )
    old.append(
        sid,
        {
            "picks": ["1"] * 14,
            "columns": ["1" * 14],
            "original": ["1" * 14, "X" * 14],
            "pleno": "M-0",
        },
    )
    old.create("26-27", 99, "No publicada", {"picks": ["1"] * 14})
    old.close()
    before = path.read_bytes()
    systems, warnings = read_legacy_systems(path, list(rounds))
    assert len(systems) == 2 and warnings and systems[0].quantity == 3
    assert [b.column for b in systems[0].bets] == ["1" * 14, "1" * 14, "X" * 14]
    assert systems[0].pleno == "M0"
    assert json.loads(systems[0].parameters)["legacy_parameters"]["original"] == [
        "1" * 14,
        "X" * 14,
        "2" * 14,
    ]
    repo = Repository(tmp_path / "studio.sqlite3")
    for r in rounds:
        repo.save_round(r)
    assert repo.import_system_copies(systems) == 2
    assert repo.import_system_copies(systems) == 0
    assert path.read_bytes() == before
    repo.close()


def test_import_rounds_transaction_rollback(tmp_path):
    round_ = load_win1x2(data_folder(tmp_path / "source"))[-1]
    repo = Repository(tmp_path / "studio.sqlite3")
    repo.save_round(round_)
    repo.db.execute(
        "CREATE TRIGGER reject_settings BEFORE INSERT ON settings BEGIN SELECT RAISE(ABORT,'test'); END"
    )
    with pytest.raises(sqlite3.IntegrityError):
        repo.import_rounds([replace(round_, price_cents=200)], tmp_path / "cache")
    assert (
        repo.round(round_.key).price_cents == 75
        and repo.setting("data_directory") is None
    )
    repo.close()


def test_schema_v1_migration_backup(tmp_path):
    path = tmp_path / "studio.sqlite3"
    repo = Repository(path)
    repo.db.execute("DROP TABLE settings")
    repo.db.execute("PRAGMA user_version=1")
    repo.db.commit()
    repo.close()
    repo = Repository(path)
    assert repo.db.execute("PRAGMA user_version").fetchone()[0] == 2
    assert list(tmp_path.glob("studio-pre-v2-*.sqlite3"))
    repo.close()


def test_live_strict_identity_and_no_other_round_fallback(tmp_path, monkeypatch):
    from quiniela_studio import integration

    round_ = load_win1x2(data_folder(tmp_path / "source"))[-1]
    matches = [
        LiveMatch(n, "Equipo A", "Equipo B", "—", "", "", "Pendiente", False, 0)
        for n in range(1, 16)
    ]
    monkeypatch.setattr(
        integration, "fetch_live_results", lambda season, number: matches
    )
    assert not any(m.sign for m in live_for_round(round_))
    matches[0] = replace(matches[0], home="Incorrecto")
    with pytest.raises(ValueError):
        live_for_round(round_)


def test_provider_team_aliases_are_explicit():
    from quiniela_studio.integration import team_key

    assert team_key("Andorra") == team_key("ANDORRA FC")
    assert team_key("Ath.Club Bilbao") == team_key("ATH.CLUB")
    assert team_key("Córdoba") == team_key("CORDOBA")
    assert team_key("Barcelona") != team_key("Barcelona B")


def test_utf16_xml_entities_rejected(tmp_path):
    round_ = load_win1x2(data_folder(tmp_path / "source"))[-1]
    payload = '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE x [<!ENTITY a "bad">]><x>&a;</x>'.encode(
        "utf-16"
    )
    with pytest.raises(ValueError):
        public_snapshot(round_, payload)


def test_legacy_copy_freezes_legacy_price_and_marks_incomplete(tmp_path):
    round_ = replace(load_win1x2(data_folder(tmp_path / "source"))[-1], price_cents=100)
    path = tmp_path / "old.sqlite3"
    old = SystemStore(path)
    old.create(
        "26-27",
        12,
        "Con apuestas",
        {"columns": ["1" * 14], "picks": ["1"] * 14, "pleno": "0-0"},
    )
    old.create("26-27", 12, "Incompleto", {"picks": [""] * 14})
    old.close()
    systems, warnings = read_legacy_systems(path, [round_])
    assert systems[0].cost(round_) == 75
    assert systems[1].bets == () and "borrador incompleto" in systems[1].name
    assert warnings
