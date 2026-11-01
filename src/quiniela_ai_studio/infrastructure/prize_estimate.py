"""Orientative prize estimates from Quinielista's published round data."""

from __future__ import annotations

import html
import json
import re
from decimal import Decimal, InvalidOperation
from urllib.request import Request, urlopen

from quiniela_ai_studio.domain.models import Round

SOURCE = "Quinielista · estimación orientativa"
BASE_URL = "https://www.eduardolosilla.es/quiniela/ayudas/estimacion"
MAX_RESPONSE_BYTES = 1_000_000


def _number(value: object, label: str) -> Decimal:
    text = str(value or "0").strip().replace("€", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{label} publicado no válido.") from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f"{label} publicado no válido.")
    return number


def _cents(value: object, label: str) -> int:
    return int((_number(value, label) * 100).quantize(Decimal("1")))


def _shares(rows: object, *, plenary: bool = False) -> tuple[tuple[float, ...], ...]:
    if not isinstance(rows, list) or len(rows) != (1 if plenary else 15):
        raise ValueError("La fuente no contiene los porcentajes completos de la jornada.")
    result = []
    if plenary:
        row = rows[0]
        sides = []
        for side in ("L", "V"):
            values = [float(row.get(f"porc_15{side}_{goal}_dec", row.get(f"porc_15{side}_{goal}", 0))) for goal in "012M"]
            total = sum(values)
            if any(value < 0 for value in values) or not 90 <= total <= 110:
                raise ValueError("Los porcentajes del Pleno no son válidos.")
            sides.append(tuple(value / total for value in values))
        return tuple(sides)
    for row in rows[:14]:
        values = [float(row.get(f"porc_{sign}_dec", row.get(f"porc_{sign}", 0))) for sign in ("1", "X", "2")]
        total = sum(values)
        if any(value < 0 for value in values) or not 90 <= total <= 110:
            raise ValueError("Los porcentajes de los partidos no son válidos.")
        result.append(tuple(value / total for value in values))
    return tuple(result)


def parse_prize_estimate(payload: str, round_: Round) -> dict:
    """Parse the page's embedded round data and validate its season/round."""
    match = re.search(
        r'<script\s+id="eduardo-losilla-state"\s+type="application/json">([\s\S]*?)</script>',
        payload,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError("La fuente no publicó los datos internos de la estimación.")
    transfer = json.loads(html.unescape(match.group(1).replace("&q;", '"')))
    try:
        season_year = 2000 + int(round_.season.split("-")[-1])
        general = transfer[f"jornada_{round_.number}_{season_year}"]
        probability = transfer[f"probabilidades_{round_.number}_{season_year}"]
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("Quinielista no ofrece una estimación para esta jornada.") from exc
    if int(general.get("temporada", 0)) != season_year or int(general.get("jornada", 0)) != round_.number:
        raise ValueError("La estimación publicada pertenece a otra jornada.")
    if int(probability.get("numTemporada", 0)) != season_year or int(probability.get("numJornada", 0)) != round_.number:
        raise ValueError("Los porcentajes publicados pertenecen a otra jornada.")

    match_data = probability.get("partidos", {})
    played = _shares(match_data.get("quinielista"))
    market_rows = match_data.get("real")
    try:
        market = _shares(market_rows) if isinstance(market_rows, list) and len(market_rows) == 15 else played
    except ValueError:
        market = played
    pleno = _shares([match_data["quinielista"][14]], plenary=True)
    revenue = _cents(general.get("recaudacion"), "La recaudación")
    jackpot = _cents(general.get("boteEstimacion") or general.get("textoBote"), "El bote")
    ticket = _cents(general.get("costeApuesta", "0.75"), "El precio por apuesta")
    if revenue <= 0 or ticket <= 0:
        raise ValueError("Aún no hay recaudación suficiente para estimar los premios.")
    return {
        "season": round_.season,
        "round": round_.number,
        "revenue_cents": revenue,
        "jackpot_cents": jackpot,
        "ticket_cents": ticket,
        "played": played,
        "market": market,
        "pleno_home": pleno[0],
        "pleno_away": pleno[1],
        "captured_at": general.get("fechaFinApuestas") or probability.get("fechaModificacion"),
        "source": SOURCE,
        "url": f"{BASE_URL}?jornada={round_.number}&temporada={season_year}",
    }


def fetch_prize_estimate(round_: Round) -> dict:
    """Fetch a bounded response; call from a worker thread."""
    if round_.season == "DEMO":
        raise ValueError("La jornada de demostración no admite previsión de premios.")
    season_year = 2000 + int(round_.season.split("-")[-1])
    url = f"{BASE_URL}?jornada={round_.number}&temporada={season_year}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 Quiniela-AI-Studio/2.0"})
    with urlopen(request, timeout=10) as response:
        payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("La respuesta de estimación excede el tamaño admitido.")
    return parse_prize_estimate(payload.decode("utf-8", "replace"), round_)
