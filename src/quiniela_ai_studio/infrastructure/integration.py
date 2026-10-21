"""Adaptadores compartidos con Quiniela Local; preparación sin tocar SQLite ni Qt."""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import tempfile
import unicodedata
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

import data_updater
from live_results import LiveMatch, fetch_live_results
from quiniela_ai_studio.domain.engine import Cancelled, union_base
from quiniela_ai_studio.domain.models import (
    Bet,
    ProbabilitySnapshot,
    Round,
    SystemVersion,
    round_dict,
    utcnow,
)
from quiniela_ai_studio.infrastructure.files import read_bytes
from quiniela_ai_studio.infrastructure.providers import (
    load_win1x2,
    scrutiny_record,
    text,
)

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
    "MANCHUNITED": "MANUNITED",
    "MANCHESTERUNITED": "MANUNITED",
    "BAYERNMUNICH": "BMUNICH",
    "BORDORTMUND": "BDORTMUND",
    "BORUSSIADORTMUND": "BDORTMUND",
    "MANCHESTCITY": "MANCITY",
    "MANCHESTERCITY": "MANCITY",
    "CSUCRAIOVA": "UCRAIOVA",
    # En algunos PRE de WIN1X2 aparece «Madrid CCF» para el mismo equipo
    # que Quinielista publica como «Madrid CFF».
    "MADRIDCCFF": "MADRIDCFFF",
    # Variantes observadas en el XML de porcentajes de Quinielista frente al
    # fichero de jornada WIN1X2 (incluye una errata histórica en PSV Eindhoven).
    "PSV": "PSVEINDHOVEN",
    "PSVEIDHOVEN": "PSVEINDHOVEN",
    "SHAKTARDONETSK": "SHAKHTARDONETSK",
    "RBLEIPZIG": "LEIPZIG",
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
        pleno_values=pleno_percentages(matches[-1], "p_jugados_"),
    )
    return replace(
        round_,
        snapshots=tuple(s for s in round_.snapshots if s.kind != "public")
        + (snapshot,),
    )


def pleno_percentages(match, prefix: str, suffix: str = "") -> tuple:
    """Lee marginales 0/1/2/M por equipo; no supone una distribución conjunta."""
    import math
    fields = tuple(tuple(f"{prefix}{goal}{side}{suffix}" for goal in "012M") for side in "LV")
    if not any(field in match.attrib for row in fields for field in row):
        return ()
    rows = []
    for fields_side in fields:
        try:
            values = tuple(float(match.attrib[field]) for field in fields_side)
        except (ValueError, KeyError) as exc:
            raise ValueError("Porcentajes del Pleno incompletos o inválidos.") from exc
        if any(not math.isfinite(v) or not 0 <= v <= 100 for v in values) or not 99 <= sum(values) <= 101:
            raise ValueError("Los porcentajes del Pleno deben sumar 100 por equipo.")
        rows.append(tuple(v / sum(values) for v in values))
    return tuple(rows)


def probability_snapshots(round_: Round, payload: bytes, captured_at: str | None = None) -> Round:
    """Lee público y mercado del XML publicado; no inventa probabilidades ausentes."""
    updated = public_snapshot(round_, payload, captured_at)
    matches = ElementTree.fromstring(payload).findall(".//partido")[:14]
    fields = tuple(f"p_bf_{sign}desc" for sign in "1X2")
    if not any(any(field in match.attrib for field in fields) for match in matches):
        fields = tuple(f"p_bf_{sign}" for sign in "1X2")
    if not any(any(field in match.attrib for field in fields) for match in matches):
        return updated
    import math

    rows = []
    for match in matches:
        try:
            values = tuple(float(match.attrib[field]) for field in fields)
        except (ValueError, KeyError) as exc:
            raise ValueError("La fuente de mercado está incompleta o contiene valores inválidos.") from exc
        if any(not math.isfinite(v) or not 0 <= v <= 100 for v in values) or not 99 <= sum(values) <= 101:
            raise ValueError("Los porcentajes de mercado no son válidos o no suman 100.")
        rows.append(tuple(v / sum(values) for v in values))
    snapshot = ProbabilitySnapshot(
        "sport", "Quinielista / Eduardo Losilla · mercado (Betfair/casas de apuestas)",
        captured_at or utcnow(), tuple(rows), "porcentajes publicados; sin calibración propia",
        pleno_values=pleno_percentages(ElementTree.fromstring(payload).findall(".//partido")[-1], "p_bf_", "desc") or pleno_percentages(ElementTree.fromstring(payload).findall(".//partido")[-1], "p_bf_"),
    )
    return replace(updated, snapshots=tuple(s for s in updated.snapshots if s.kind != "sport") + (snapshot,))


def fetch_round_sources(round_: Round, cache: Path, *, cancelled=lambda: False) -> Round:
    """Descarga exclusivamente la jornada solicitada, validando también sus equipos."""
    if round_.season == "DEMO":
        raise ValueError("La demo es ficticia. Descarga partidos y selecciona una jornada real.")
    checkpoint(cancelled)
    payload = data_updater._download(data_updater.QUINIELISTA_PERCENTAGES.format(round_no=round_.number))
    updated = probability_snapshots(round_, payload)
    checkpoint(cancelled)
    data_updater._atomic_write(cache / f"porcentajes_{round_.season}_J{round_.number:02d}.xml", payload)
    return updated


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
                updated = probability_snapshots(current, path.read_bytes())
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
                            path.stat().st_mtime, UTC
                        ).isoformat()
                        rounds[i] = probability_snapshots(round_, read_bytes(path), captured)
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


def live_for_round(round_: Round, preferred_source: str = "") -> tuple[LiveMatch, ...]:
    if round_.season == "DEMO":
        raise ValueError("La jornada de demostración no tiene marcador real.")

    from quiniela_ai_studio.infrastructure.espn_live import fetch_espn_live_scores

    def fetch_espn():
        matches = fetch_espn_live_scores(round_.matches)
        validate_teams(round_, [(m.home, m.away) for m in matches])
        return matches

    # Una vez que ESPN resuelve una jornada, usarlo primero en sus refrescos para
    # no esperar cada vez a que falle la fuente primaria; si ESPN cae, se prueba Dataradar.
    if preferred_source == "ESPN (alternativa)":
        try:
            matches = fetch_espn()
            if any(match.status != "Sin cobertura de ESPN" for match in matches):
                return matches
        except (ConnectionError, ValueError):
            pass

    try:
        matches = fetch_live_results(round_.season, round_.number)
    except (ConnectionError, ValueError) as primary_error:
        # Dataradar es la fuente principal. Si falla la conexión o no puede
        # interpretarse la respuesta, se prueba ESPN. La identidad de equipos
        # se valida después, fuera de este bloque, sin ocultar cruces.
        try:
            return fetch_espn()
        except (ConnectionError, ValueError) as fallback_error:
            raise ConnectionError(
                "No se pudo conectar con el marcador público ni con ESPN: "
                f"{primary_error}; {fallback_error}"
            ) from fallback_error
    # Una respuesta estructurada con equipos distintos se rechaza directamente;
    # no se oculta como un simple fallo de red ni se cambia de jornada.
    validate_teams(round_, [(m.home, m.away) for m in matches])

    # Algunos proveedores contestan correctamente, pero aún dejan vacíos los
    # partidos cuyo horario ya pasó. En ese caso consultar ESPN evita mantener
    # esos encuentros como pendientes hasta la siguiente jornada. Solo se
    # sustituyen filas sin signo por resultados alternativos confirmados.
    now = datetime.now().astimezone()
    primary_by_number = {match.number: match for match in matches}
    has_missing_started_match = any(
        (fixture.number not in primary_by_number or not primary_by_number[fixture.number].sign)
        and _kickoff_has_passed(fixture.kickoff, now)
        for fixture in round_.matches[:14]
    )
    if has_missing_started_match:
        try:
            alternate = fetch_espn()
        except (ConnectionError, ValueError):
            return tuple(matches)
        alternate_by_number = {match.number: match for match in alternate}
        return tuple(
            alternate_by_number.get(match.number, match)
            if not match.sign and alternate_by_number.get(match.number, match).sign
            else match
            for match in matches
        )
    return tuple(matches)


def _kickoff_has_passed(value: str, now: datetime) -> bool:
    """Return whether a supported local fixture kickoff is earlier than now."""
    scheduled = None
    for pattern in ("%d/%m/%Y%H:%M", "%d/%m/%Y %H:%M"):
        try:
            scheduled = datetime.strptime(value, pattern).astimezone()
            break
        except ValueError:
            continue
    if scheduled is None:
        try:
            scheduled = datetime.fromisoformat(value)
        except ValueError:
            return False
        if scheduled.tzinfo is None:
            scheduled = scheduled.astimezone()
    return scheduled <= now


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
