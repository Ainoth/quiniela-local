"""Reference for a published round and the adapter's identity checks."""

from dataclasses import replace

import pytest

from quiniela_ai_studio.domain.models import Match, Round, utcnow
from quiniela_ai_studio.infrastructure.published_scrutiny import (
    parse_published_scrutiny,
)

TEAMS = (
    ("Espanyol", "At. Madrid"), ("Villarreal", "Elche"),
    ("Betis", "Barcelona"), ("Valencia", "Ath.Club Bilbao"),
    ("Celta", "Alavés"), ("Málaga", "R.Sociedad"),
    ("R.Madrid", "Sevilla"), ("Eibar", "Mallorca"),
    ("Las Palmas", "Castellón"), ("Burgos", "Sabadell"),
    ("Ath.Club (F)", "Valencia (F)"), ("R.Madrid (F)", "Espanyol (F)"),
    ("Eibar (F)", "Deportivo (F)"), ("At. Madrid (F)", "Madrid CCF (F)"),
    ("Getafe", "Rayo"),
)
SCORES = ((0, 1), (0, 0), (2, 5), (0, 0), (2, 1), (2, 5), (4, 1),
          (1, 1), (0, 3), (1, 0), (1, 0), (3, 1), (2, 3), (4, 0), (1, 1))
AMOUNTS = ("80.778,13 €", "11.162,13 €", "165,26 €", "12,76 €",
           "2,22 €", "Sin premio a cobrar")


def reference_round():
    matches = tuple(Match(i, home, away, home_id=f"home:{i}", away_id=f"away:{i}")
                    for i, (home, away) in enumerate(TEAMS, 1))
    return Round("26-27", 14, matches, "past", "Referencia", utcnow(),
                 nominal_date="2026-10-18")


def reference_page():
    rows = []
    for i, ((home, away), (a, b)) in enumerate(zip(TEAMS, SCORES), 1):
        source_home = home.replace("Ath.Club", "Athletic Club").replace("R.Madrid", "Real Madrid")
        source_away = away.replace("Ath.Club", "Athletic Club").replace("Athletic Club Bilbao", "Athletic Club").replace("R.Sociedad", "Real Sociedad").replace("Madrid CCF", "Madrid Cff").replace("Rayo", "Rayo Vallecano")
        source_home += " (m)" if "(F)" not in home else ""
        source_away += " (m)" if "(F)" not in away else ""
        source_home = source_home.replace("(F)", "(f)")
        source_away = source_away.replace("(F)", "(f)")
        sign = ("1" if a > b else "2" if a < b else "X") if i < 15 else f"{a}-{b}"
        rows.append(f'<li class="match-row"><span class="match-pos">{i}</span>'
                    f'<div class="match-teams">{source_home} <span>—</span> {source_away}'
                    f'<div class="match-score">{a} - {b}</div></div>'
                    f'<span class="result-sign">{sign}</span></li>')
    categories = ("Pleno al 15", "1ª (14 Aciertos)", "2ª (13 Aciertos)",
                  "3ª (12 Aciertos)", "4ª (11 Aciertos)", "5ª (10 Aciertos)")
    prizes = "".join(f'<th scope="row">{label}</th><td class="count">1</td>'
                     f'<td class="amount">{amount}</td>'
                     for label, amount in zip(categories, AMOUNTS))
    return ('<h1>La Quiniela</h1><p>Jornada 14</p><time datetime="2026-10-18">18/10</time>'
            + "".join(rows) + prizes)


def test_published_scrutiny_reference_j14_and_all_payouts():
    record = parse_published_scrutiny(reference_page(), reference_round())
    assert record["result"] == "2X2X121X211121"
    assert record["pleno"] == "11"
    assert record["prizes"] == {15: 8077813, 14: 1116213, 13: 16526,
                                 12: 1276, 11: 222, 10: 0}


@pytest.mark.parametrize("change", (
    lambda page: page.replace("Jornada 14", "Jornada 13"),
    lambda page: page.replace("Espanyol (m)", "Otro (m)"),
    lambda page: page.replace("0 - 1", "1 - 0", 1),
    lambda page: page.replace("2,22 €", "pendiente"),
))
def test_published_scrutiny_rejects_wrong_round_fixture_score_or_amount(change):
    with pytest.raises(ValueError):
        parse_published_scrutiny(change(reference_page()), reference_round())


def test_published_scrutiny_rejects_wrong_frozen_date():
    with pytest.raises(ValueError):
        parse_published_scrutiny(reference_page(), replace(reference_round(), nominal_date="2026-10-19"))
