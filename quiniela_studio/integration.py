"""Adaptadores compartidos con Quiniela Local; preparación sin tocar SQLite ni Qt."""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import tempfile
import unicodedata
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

import data_updater
from live_results import LiveMatch, fetch_live_results

from .domain import Bet, ProbabilitySnapshot, Round, SystemVersion, round_dict, utcnow
from .engine import Cancelled, union_base
from .files import read_bytes
from .providers import load_win1x2, scrutiny_record, text

# Variantes nominales documentadas, sin coincidencia difusa ni orden implícito.
TEAM_ALIASES = {
    "ANDORRAFC": "ANDORRA",
    "ATHCLUBBILBAO": "ATHCLUB",
    "ATHLETICCLUB": "ATHCLUB",
    "ATHLETICBILBAO": "ATHCLUB",
    "ATLETICOMADRID": "ATMADRID",
    "ATLETICODEMADRID": "ATMADRID",
    "RAYOVALLECANO": "RAYO",
    "REALSOCIEDAD": "RSOCIEDAD",
    "REALOVIEDO": "ROVIEDO",
    "REALMADRID": "RMADRID",
    "RACING": "RACINGS",
    "RACINGSANTANDER": "RACINGS",
    "DEPORTIVOCORUNA": "DEPORTIVO",
    "DEPORTIVOLACORUNA": "DEPORTIVO",
}


def team_key(name: str) -> str:
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    key = re.sub("[^A-Z0-9]", "", plain.upper())
    return TEAM_ALIASES.get(key, key)


def validate_teams(round_: Round, teams: list[tuple[str, str]]) -> None:
    if len(teams) != 15:
        raise ValueError("La fuente no contiene los 15 partidos.")
    for match, (home, away) in zip(round_.matches, teams):
        if (
            not home
            or not away
            or (team_key(home), team_key(away))
            != (team_key(match.home), team_key(match.away))
        ):
            raise ValueError(
                f"Los equipos de la fuente no coinciden en el partido {match.number}: {home} – {away}."
            )


def public_snapshot(
    round_: Round, payload: bytes, captured_at: str | None = None
) -> Round:
    """XML público validado por identidad completa; nunca produce deportiva/P15."""
    rows = data_updater._validated_percentages(payload, round_.season, round_.number)
    matches = ElementTree.fromstring(payload).findall(".//partido")
    validate_teams(
        round_, [(m.get("local", ""), m.get("visitante", "")) for m in matches]
    )
    snapshot = ProbabilitySnapshot(
        "public",
        "Quinielista · porcentajes jugados",
        captured_at or utcnow(),
        tuple(tuple(v / 100 for v in row) for row in rows),
    )
    return replace(
        round_,
        snapshots=tuple(s for s in round_.snapshots if s.kind != "public")
        + (snapshot,),
    )


@dataclass(frozen=True)
class PreparedImport:
    rounds: tuple[Round, ...]
    directory: Path
    warnings: tuple[str, ...] = ()

    @property
    def preferred(self) -> str:
        return next(
            (r.key for r in self.rounds if r.mode == "current"), self.rounds[-1].key
        )


def checkpoint(cancelled) -> None:
    if cancelled():
        raise Cancelled("Operación cancelada; los datos anteriores se conservan.")


def prepare_data(
    cache: Path,
    *,
    folder=None,
    zip_path=None,
    online=False,
    cancelled=lambda: False,
    progress=lambda message: None,
) -> PreparedImport:
    """Prepara una copia independiente; solo la UI puede aprobar su aplicación."""
    cache.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="datos-", dir=cache))
    try:
        checkpoint(cancelled)
        if online:
            progress("Descargando jornadas WIN1X2…")
            data_updater.update_win1x2_files(stage)
        elif zip_path:
            progress("Validando ZIP WIN1X2…")
            data_updater.unpack_win1x2(read_bytes(zip_path), stage)
        elif folder:
            directory = Path(folder)
            nested = next(
                (
                    p
                    for p in directory.iterdir()
                    if p.is_dir() and p.name.casefold() == "datosg"
                ),
                None,
            )
            if nested:
                directory = nested
            items = [p for p in directory.iterdir() if p.is_file()]
            if (
                len(items) > 5000
                or sum(p.stat().st_size for p in items) > data_updater.MAX_UNPACKED
            ):
                raise ValueError("La carpeta supera los límites de importación.")
            for path in items:
                checkpoint(cancelled)
                if path.is_symlink():
                    raise ValueError("La carpeta contiene enlaces simbólicos.")
                shutil.copy2(path, stage / path.name)
        else:
            raise ValueError("Selecciona una carpeta, ZIP o descarga.")
        checkpoint(cancelled)
        progress("Validando jornadas, calendario y equipos…")
        rounds = list(load_win1x2(stage))
        warnings = []
        current = next((r for r in rounds if r.mode == "current"), None)
        if online and current:
            try:
                progress(f"Descargando porcentajes jugados de {current.key}…")
                path = data_updater.fetch_percentages(
                    current.season, current.number, stage
                )
                updated = public_snapshot(current, path.read_bytes())
                rounds[rounds.index(current)] = updated
            except (OSError, ValueError, KeyError, ElementTree.ParseError) as exc:
                warnings.append(
                    f"Jornadas disponibles; porcentajes no incorporados: {exc}"
                )
        elif not online:
            for i, round_ in enumerate(rounds):
                path = stage / f"porcentajes_{round_.season}_J{round_.number:02d}.xml"
                if path.exists():
                    try:
                        captured = datetime.fromtimestamp(
                            path.stat().st_mtime, timezone.utc
                        ).isoformat()
                        rounds[i] = public_snapshot(round_, read_bytes(path), captured)
                    except (
                        OSError,
                        ValueError,
                        KeyError,
                        ElementTree.ParseError,
                    ) as exc:
                        warnings.append(
                            f"{round_.key}: porcentajes no incorporados: {exc}"
                        )
        checkpoint(cancelled)
        return PreparedImport(tuple(rounds), stage, tuple(warnings))
    except BaseException:
        shutil.rmtree(stage)
        raise


def reconcile_import(prepared: PreparedImport, existing: list[Round]) -> PreparedImport:
    """Conserva reglas y fuentes manuales; los sistemas ya congelados no cambian."""
    known = {r.key: r for r in existing}
    result, warnings = [], list(prepared.warnings)
    for incoming in prepared.rounds:
        previous = known.get(incoming.key)
        if previous:
            if not previous.source.startswith("WIN1X2"):
                warnings.append(
                    f"{incoming.key}: datos manuales conservados; no se reemplazan."
                )
                continue
            same = [(m.home_id, m.away_id) for m in incoming.matches] == [
                (m.home_id, m.away_id) for m in previous.matches
            ]
            snapshots = incoming.snapshots
            if same:
                snapshots += tuple(
                    s for s in previous.snapshots if not incoming.snapshot(s.kind)
                )
            incoming = replace(
                incoming,
                price_cents=previous.price_cents,
                rules_version=previous.rules_version,
                snapshots=snapshots,
            )
        result.append(incoming)
    if not result:
        raise ValueError(
            "Ninguna jornada se puede incorporar sin reemplazar datos manuales."
        )
    return replace(prepared, rounds=tuple(result), warnings=tuple(warnings))


def scrutiny_from_cache(directory: Path, round_: Round):
    path = next(
        (
            p
            for p in directory.iterdir()
            if p.name.casefold() == f"pre{round_.season}.txt".casefold()
        ),
        None,
    )
    if path is None:
        raise ValueError("No hay un PRE de esta temporada en los datos guardados.")
    line = next(
        (
            s
            for s in text(path).splitlines()
            if s[:2].strip().isdigit() and int(s[:2]) == round_.number
        ),
        "",
    )
    if len(line) >= 209:
        codes = [line[119 + i * 3 : 122 + i * 3].upper() for i in range(30)]
        expected = [
            code.rsplit(":", 1)[-1]
            for m in round_.matches
            for code in (m.home_id, m.away_id)
        ]
        if codes != expected:
            raise ValueError("Los equipos del PRE no coinciden con el sistema.")
    return scrutiny_record(line)


def live_for_round(round_: Round) -> tuple[LiveMatch, ...]:
    if round_.season == "DEMO":
        raise ValueError("La jornada de demostración no tiene marcador real.")
    matches = fetch_live_results(round_.season, round_.number)
    validate_teams(round_, [(m.home, m.away) for m in matches])
    return tuple(matches)


def read_legacy_systems(
    path: Path, rounds: list[Round], cancelled=lambda: False
) -> tuple[tuple[SystemVersion, ...], tuple[str, ...]]:
    """Lee todas las versiones Tkinter sin modificar la base original ni reconstruir apuestas."""
    import hashlib
    import uuid

    known = {r.key: r for r in rounds}
    prepared, warnings = [], []
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("La base antigua supera el máximo de importación de 128 MiB.")
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        if db.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise ValueError("Se esperaba una base SQLite de Quiniela Local versión 1.")
        rows = db.execute(
            "SELECT s.id,s.name,s.season,s.round_no,v.sequence,v.payload,v.hash "
            "FROM systems s JOIN versions v ON v.system_id=s.id ORDER BY s.id,v.sequence"
        )
        for ident, name, season, number, revision, raw, digest in rows:
            checkpoint(cancelled)
            if hashlib.sha256(raw.encode()).hexdigest() != digest:
                raise ValueError(
                    "La base antigua contiene una versión con hash incorrecto."
                )
            key = f"{season}/J{number:02d}"
            if key not in known:
                warnings.append(
                    f"{name} ({key}): importa primero los datos de esta jornada."
                )
                continue
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise TypeError(
                    "Una versión antigua no contiene un objeto JSON válido."
                )
            pleno = data.get("pleno", "").replace("-", "")
            columns = data.get("columns") or []
            bets = tuple(Bet(column, pleno) for column in columns)
            base = union_base(
                bets, tuple(p or "1" for p in data.get("picks", ["1"] * 14))
            )
            incomplete = not bets and any(not p for p in data.get("picks", [""] * 14))
            if incomplete:
                warnings.append(
                    f"{name} ({key}): borrador incompleto; posiciones vacías usan 1 provisional, revisar antes de generar."
                )
            # La app Tkinter de origen usa 75 céntimos fijos. No tomar un precio
            # distinto de la jornada actual para cambiar el gasto al copiar.
            frozen = replace(
                known[key],
                price_cents=75,
                rules_version="quiniela-local-legacy-75c; confirmar canal antes de jugar",
                snapshots=(),
            )
            # Determinista e idempotente por archivo/sistema/versión; cada copia conserva el origen.
            uid = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL, f"{path.resolve()}:{ident}:{revision}:{digest}"
                )
            )
            metadata = {
                "legacy_system": ident,
                "legacy_revision": revision,
                "legacy_hash": digest,
                "legacy_parameters": data,
            }
            prepared.append(
                SystemVersion(
                    uid,
                    1,
                    key,
                    f"{name} · PC v{revision}"
                    + (" · borrador incompleto" if incomplete else ""),
                    base,
                    (False,) * 14,
                    pleno,
                    bets,
                    utcnow(),
                    "copia de Quiniela Local",
                    json.dumps(metadata, ensure_ascii=False),
                    json.dumps(round_dict(frozen)),
                )
            )
    return tuple(prepared), tuple(warnings)
