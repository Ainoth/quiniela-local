"""Adaptador de marcador alternativo para competiciones españolas cubiertas por ESPN.

El marcador de Quinielista/Dataradar sigue siendo la fuente primaria. Este
adaptador sirve de respaldo si falla, no puede interpretarse o deja sin
marcador partidos cuyo horario ya pasó.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request

from live_results import LiveMatch
from quiniela_ai_studio.domain.models import Match

ESPN_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={day}"
)
LEAGUES_MEN = ("esp.1", "esp.2")
LEAGUE_WOMEN = ("esp.w.1",)
SOURCE_NAME = "ESPN (alternativa)"
REQUEST_TIMEOUT_SECONDS = 4
MAX_RESPONSE_BYTES = 2 * 1024 * 1024

# Diferencias de nombres entre los horarios PRE locales y el marcador ESPN.
TEAM_ALIASES = {
    "ATHCLUBBILBAO": "ATHCLUB",
    "ATHLETICCLUB": "ATHCLUB",
    "ATHLETICBILBAO": "ATHCLUB",
    "ATLETICOMADRID": "ATMADRID",
    "ATLETICODEMADRID": "ATMADRID",
    "RAYOVALLECANO": "RAYO",
    "REALSOCIEDAD": "RSOCIEDAD",
    "REALMADRID": "RMADRID",
    "DEPORTIVOCORUNA": "DEPORTIVO",
    "DEPORTIVOLACORUNA": "DEPORTIVO",
    "MADRIDCCF": "MADRIDCFF",
    "REALBETIS": "BETIS",
    "REALBETISBALOMPIE": "BETIS",
    "CELTAVIGO": "CELTA",
    "RCCELTADEVIGO": "CELTA",
    "CDCASTELLON": "CASTELLON",
    "CDSABADELL": "SABADELL",
    "RCDMALLORCA": "MALLORCA",
    "CDTENERIFE": "TENERIFE",
}


def _scheduled_date(match: Match) -> str | None:
    """Return the local fixture date as ESPN's YYYYMMDD query value."""
    value = match.kickoff
    if not value:
        return None
    for pattern in ("%d/%m/%Y%H:%M", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(value, pattern).strftime("%Y%m%d")
        except ValueError:
            continue
    return None


def _is_women_match(match: Match) -> bool:
    return any(re.search(r"\((?:F|FEMENINO)\)\s*$", name, re.IGNORECASE)
               for name in (match.home, match.away))


def _team_key(name: str) -> str:
    # Los equipos de Liga F se identifican por la competición. El sufijo (F)
    # solo aclara la etiqueta local y no forma parte del nombre ESPN.
    clean = re.sub(r"\s*\((?:F|FEMENINO)\)\s*$", "", name, flags=re.IGNORECASE)
    plain = unicodedata.normalize("NFKD", clean).encode("ascii", "ignore").decode()
    key = re.sub(r"[^A-Z0-9]", "", plain.upper())
    return TEAM_ALIASES.get(key, key)


def _score_value(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and re.fullmatch(r"\d{1,2}", value.strip()):
        return int(value)
    return None


def parse_espn_scoreboard(payload: bytes, league: str, day: str) -> list[dict]:
    """Parse one ESPN scoreboard response, discarding scheduled placeholder 0–0s."""
    try:
        body = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("ESPN devolvió un JSON de marcador no válido.") from exc
    events = body.get("events") if isinstance(body, dict) else None
    if not isinstance(events, list):
        raise ValueError("ESPN devolvió una estructura de marcador no reconocida.")

    parsed = []
    for event in events:
        if not isinstance(event, dict):
            continue
        event_date = event.get("date")
        try:
            scheduled = datetime.fromisoformat(str(event_date).replace("Z", "+00:00"))
        except ValueError:
            continue
        if scheduled.tzinfo is None or scheduled.astimezone().strftime("%Y%m%d") != day:
            continue
        competitions = event.get("competitions")
        if not isinstance(competitions, list) or not competitions:
            continue
        competition = competitions[0]
        competitors = competition.get("competitors")
        if not isinstance(competitors, list):
            continue
        sides = {
            row.get("homeAway"): row
            for row in competitors
            if isinstance(row, dict) and row.get("homeAway") in ("home", "away")
        }
        home, away = sides.get("home"), sides.get("away")
        if not home or not away:
            continue
        home_name = str(home.get("team", {}).get("displayName", "")).strip()
        away_name = str(away.get("team", {}).get("displayName", "")).strip()
        if not home_name or not away_name:
            continue

        status = competition.get("status") or event.get("status") or {}
        status_type = status.get("type") or {}
        state = str(status_type.get("state", "")).casefold()
        status_name = str(status_type.get("name", "")).upper()
        cancelled = any(token in status_name for token in ("CANCEL", "POSTPON", "SUSPEND", "ABANDON"))
        home_goals = _score_value(home.get("score"))
        away_goals = _score_value(away.get("score"))
        has_playing_score = state in {"in", "post"} and not cancelled
        if has_playing_score and home_goals is not None and away_goals is not None:
            score = f"{home_goals} - {away_goals}"
            sign = "1" if home_goals > away_goals else "2" if home_goals < away_goals else "X"
            pleno = "".join(str(goals) if goals < 3 else "M" for goals in (home_goals, away_goals))
        else:
            score, sign, pleno = "—", "", ""

        completed = bool(status_type.get("completed")) or state == "post"
        final = bool(completed and sign)
        if cancelled:
            status_text = str(status_type.get("description") or "Aplazado")
        elif state == "in":
            detail = str(status.get("displayClock") or status_type.get("shortDetail") or "")
            status_text = f"En juego · {detail}" if detail else "En juego"
        elif final:
            status_text = "Finalizado"
        elif state == "pre":
            status_text = "Sin comenzar"
        else:
            status_text = str(status_type.get("description") or "Estado sin confirmar")

        parsed.append({
            "day": day,
            "scheduled": scheduled,
            "league": league,
            "home": home_name,
            "away": away_name,
            "home_key": _team_key(home_name),
            "away_key": _team_key(away_name),
            "score": score,
            "sign": sign,
            "pleno": pleno,
            "status": status_text,
            "final": final,
            "updated": int(time.time()),
        })
    return parsed


def _fetch_scoreboard(day: str, league: str) -> list[dict]:
    url = ESPN_SCOREBOARD_URL.format(league=league, day=day)
    request = urllib.request.Request(url, headers={
        "User-Agent": "Quiniela AI Studio/1.0 (scoreboard fallback)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ConnectionError(f"ESPN {league} {day}: {exc}") from exc
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError(f"La respuesta ESPN {league} {day} supera el tamaño permitido.")
    return parse_espn_scoreboard(payload, league, day)


def fetch_espn_live_scores(fixtures: tuple[Match, ...] | list[Match]) -> tuple[LiveMatch, ...]:
    """Fetch and align Spanish Primera, Segunda and Liga F games to a quiniela.

    Missing coverage is returned as an explicit blank row; it never becomes a
    made-up 0–0. Team order and schedule date must match before accepting a score.
    """
    fixtures = tuple(fixtures)
    queries = set()
    dates_by_match = {}
    for match in fixtures:
        day = _scheduled_date(match)
        dates_by_match[match.number] = day
        if day:
            leagues = LEAGUE_WOMEN if _is_women_match(match) else LEAGUES_MEN
            queries.update((day, league) for league in leagues)
    if not queries:
        raise ValueError("La jornada no tiene fechas utilizables para consultar ESPN.")

    events: list[dict] = []
    failures = []
    successful_responses = 0
    with ThreadPoolExecutor(max_workers=min(9, len(queries))) as executor:
        futures = {executor.submit(_fetch_scoreboard, day, league): (day, league)
                   for day, league in sorted(queries)}
        for future in as_completed(futures):
            day, league = futures[future]
            try:
                events.extend(future.result())
                successful_responses += 1
            except (ConnectionError, ValueError) as exc:
                failures.append(str(exc))
    if not successful_responses:
        detail = "; ".join(failures[:3]) or "sin respuestas válidas"
        raise ConnectionError(f"ESPN no está disponible: {detail}")

    by_fixture = {}
    for match in fixtures:
        day = dates_by_match[match.number]
        if not day:
            by_fixture[match.number] = None
            continue
        league_set = LEAGUE_WOMEN if _is_women_match(match) else LEAGUES_MEN
        expected_pair = (_team_key(match.home), _team_key(match.away))
        by_fixture[match.number] = next((event for event in events
            if event["day"] == day and event["league"] in league_set
            and (event["home_key"], event["away_key"]) == expected_pair), None)

    now = int(time.time())
    result = []
    for match in fixtures:
        event = by_fixture.get(match.number)
        if event is None:
            result.append(LiveMatch(match.number, match.home, match.away, "—", "", "",
                                    "Sin cobertura de ESPN", False, 0, SOURCE_NAME))
        else:
            result.append(LiveMatch(match.number, match.home, match.away, event["score"],
                                    event["sign"], event["pleno"], event["status"],
                                    event["final"], event["updated"] or now, SOURCE_NAME))
    return tuple(result)
