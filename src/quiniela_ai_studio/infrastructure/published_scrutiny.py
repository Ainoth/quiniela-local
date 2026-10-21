"""Read published Quiniela payouts from a public mirror, independently of Qt.

The adapter accepts a page only after checking date, round, every fixture,
the 14 signs and Pleno score. It does not treat live scores as prize amounts.
"""

from __future__ import annotations

import html
import re
from datetime import date
from decimal import Decimal
from urllib.request import Request, urlopen

from quiniela_ai_studio.domain.models import Round
from quiniela_ai_studio.infrastructure.integration import team_key

SOURCE = "Comprobar Lotería · escrutinio SELAE reproducido"
BASE_URL = "https://comprobarloteria.com/quiniela/{date}/"


def _plain(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", fragment)).split())


def _money(value: str) -> int:
    if "Sin premio" in value:
        return 0
    match = re.fullmatch(r"\s*([\d.]+,\d{2})\s*€\s*", value)
    if not match:
        raise ValueError("El reparto publicado tiene un importe inválido.")
    return int(Decimal(match[1].replace(".", "").replace(",", ".")) * 100)


def _team(value: str, *, stored: bool = False) -> tuple[str, str]:
    def identity(name: str) -> str:
        key = team_key(name)
        return "MADRIDCFF" if key == "MADRIDCCF" else key

    match = re.fullmatch(r"\s*(.*?)\s*\(([mf])\)\s*", value, re.IGNORECASE)
    if not match:
        if stored:
            return identity(value), "M"
        raise ValueError("El escrutinio no identifica el equipo y su competición.")
    return identity(match[1]), match[2].upper()


def parse_published_scrutiny(payload: str, round_: Round) -> dict:
    """Validate a complete page against a frozen round before returning cents."""
    date_match = re.search(r'<time\s+datetime="(\d{4}-\d{2}-\d{2})"', payload)
    number_match = re.search(r"Jornada\s+(\d+)", _plain(payload), re.IGNORECASE)
    if not date_match or not number_match:
        raise ValueError("La página no identifica fecha y jornada.")
    published_date = date.fromisoformat(date_match[1])
    if published_date.isoformat() != round_.nominal_date or int(number_match[1]) != round_.number:
        raise ValueError("La fecha o jornada del escrutinio no coincide con el sistema.")
    season = f"{(published_date.year - (published_date.month < 7)) % 100:02d}-{(published_date.year + (published_date.month >= 7)) % 100:02d}"
    if season != round_.season:
        raise ValueError("La temporada del escrutinio no coincide con el sistema.")

    row_pattern = re.compile(
        r'<li\s+class="match-row"[^>]*>\s*<span\s+class="match-pos"[^>]*>(\d+)</span>'
        r'.*?<div\s+class="match-teams"[^>]*>(.*?)<div\s+class="match-score"[^>]*>(.*?)</div>'
        r'.*?</div>\s*<span\s+class="result-sign"[^>]*>(.*?)</span>\s*</li>',
        re.DOTALL,
    )
    rows = row_pattern.findall(payload)
    if len(rows) != 15:
        raise ValueError("El escrutinio no contiene los 15 partidos completos.")
    signs = []
    pleno = ""
    for expected, (number, teams_html, score_html, sign_html) in zip(round_.matches, rows):
        if int(number) != expected.number:
            raise ValueError("El orden de partidos del escrutinio no coincide.")
        teams_text = _plain(re.sub(r"<span[^>]*>—</span>", "|", teams_html))
        pair = teams_text.split("|", 1)
        if len(pair) != 2 or (_team(pair[0]), _team(pair[1])) != (_team(expected.home, stored=True), _team(expected.away, stored=True)):
            raise ValueError(f"Los equipos del escrutinio no coinciden en el partido {number}.")
        score = re.fullmatch(r"(\d+)\s*-\s*(\d+)", _plain(score_html))
        sign = _plain(sign_html).upper()
        if not score:
            raise ValueError("El escrutinio no tiene todos los marcadores finales.")
        if expected.number < 15:
            calculated = "1" if int(score[1]) > int(score[2]) else "2" if int(score[1]) < int(score[2]) else "X"
            if sign != calculated:
                raise ValueError("El signo publicado contradice el marcador.")
            signs.append(sign)
        else:
            goal = lambda value: str(value) if value < 3 else "M"
            pleno = goal(int(score[1])) + goal(int(score[2]))
            if sign.replace(" ", "") != f"{score[1]}-{score[2]}":
                raise ValueError("El Pleno publicado contradice el marcador.")

    prize_rows = re.findall(
        r'<th\s+scope="row"[^>]*>(.*?)</th>\s*<td\s+class="count"[^>]*>(.*?)</td>'
        r'\s*<td\s+class="amount"[^>]*>(.*?)</td>', payload, re.DOTALL
    )
    categories = {}
    winners = {}
    for title, count, amount in prize_rows:
        label = _plain(title)
        category = 15 if label == "Pleno al 15" else next(
            (n for n in (14, 13, 12, 11, 10) if re.search(rf"\b{n}\s+Aciertos\b", label, re.IGNORECASE)), None
        )
        if category is None or category in categories:
            continue
        winners[category] = int(_plain(count).replace(".", ""))
        categories[category] = _money(_plain(amount))
    if set(categories) != {10, 11, 12, 13, 14, 15}:
        raise ValueError("El reparto publicado no contiene todas las categorías.")
    return {
        "round_no": round_.number, "result": "".join(signs), "pleno": pleno,
        "prizes": categories, "winners": winners, "source": SOURCE,
        "url": BASE_URL.format(date=published_date.isoformat()),
    }


def fetch_published_scrutiny(round_: Round) -> dict:
    """Fetch a matching published page with a short timeout for worker use."""
    if not round_.nominal_date or round_.season == "DEMO":
        raise ValueError("La jornada no tiene fecha real para consultar premios.")
    url = BASE_URL.format(date=round_.nominal_date)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 Quiniela-AI-Studio/1.0"})
    with urlopen(request, timeout=9) as response:
        payload = response.read(400_001)
    if len(payload) > 400_000:
        raise ValueError("La respuesta del escrutinio excede el tamaño admitido.")
    return parse_published_scrutiny(payload.decode("utf-8"), round_)
