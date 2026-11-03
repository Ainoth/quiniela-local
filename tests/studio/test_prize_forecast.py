import json

import pytest

from live_results import LiveMatch
from quiniela_ai_studio.domain import engine
from quiniela_ai_studio.domain.models import Bet
from quiniela_ai_studio.domain.prize_forecast import estimate_prizes
from quiniela_ai_studio.infrastructure.prize_estimate import parse_prize_estimate
from tests.studio.test_published_scrutiny import reference_round

pytest_plugins = ("test_ui",)

def transfer(round_no=14):
    general = {
        "temporada": 2027, "jornada": round_no, "recaudacion": "1.000.000,00",
        "boteEstimacion": "50.000,00", "costeApuesta": 0.75,
    }
    matches = [
        {"porc_1_dec": 100, "porc_X_dec": 0, "porc_2_dec": 0}
        for _ in range(14)
    ]
    pleno = {f"porc_15{side}_{goal}_dec": (100 if goal == "0" else 0)
             for side in ("L", "V") for goal in "012M"}
    played = matches + [pleno]
    probabilities = {
        "numTemporada": "2027", "numJornada": str(round_no),
        "partidos": {"quinielista": played, "real": played},
    }
    return {
        f"jornada_{round_no}_2027": general,
        f"probabilidades_{round_no}_2027": probabilities,
    }


def test_parse_estimate_extracts_season_revenue_market_and_pleno():
    round_ = reference_round()
    payload = '<script id="eduardo-losilla-state" type="application/json">' + json.dumps(
        transfer(), ensure_ascii=False
    ).replace('"', '&q;') + '</script>'
    model = parse_prize_estimate(payload, round_)
    assert model["season"] == round_.season and model["round"] == round_.number
    assert model["revenue_cents"] == 100_000_000
    assert model["jackpot_cents"] == 5_000_000
    assert model["played"] == ((1.0, 0.0, 0.0),) * 14
    assert model["pleno_home"] == model["pleno_away"] == (1.0, 0.0, 0.0, 0.0)


def test_parse_estimate_rejects_a_different_round():
    round_ = reference_round()
    payload = '<script id="eduardo-losilla-state" type="application/json">' + json.dumps(
        transfer(round_no=13)
    ).replace('"', '&q;') + '</script>'
    with pytest.raises(ValueError, match="no ofrece una estimación"):
        parse_prize_estimate(payload, round_)


def test_estimate_applies_current_scenario_and_separates_15_from_14():
    bets = (Bet("1" * 14, "00"), Bet("1" * 14, "11"))
    model = {
        "played": ((1.0, 0.0, 0.0),) * 14,
        "market": ((1.0, 0.0, 0.0),) * 14,
        "pleno_home": (1.0, 0.0, 0.0, 0.0),
        "pleno_away": (1.0, 0.0, 0.0, 0.0),
        "revenue_cents": 100_000_000,
        "jackpot_cents": 5_000_000,
        "ticket_cents": 75,
    }
    estimate = estimate_prizes(bets, model)
    rows = {row["category"]: row for row in estimate["rows"]}
    assert estimate["scenario"] == "1" * 14 and estimate["pleno"] == "00"
    assert rows[15]["own_bets"] == rows[14]["own_bets"] == 1
    assert rows[15]["unit_cents"] > rows[14]["unit_cents"]
    assert estimate["total_cents"] == sum(row["subtotal_cents"] for row in estimate["rows"])


def test_forecast_card_remains_visible_without_open_or_imported_bets(window):
    window.system = None
    window.external_scrutiny_bets = None
    window.refresh_scrutiny_page()

    assert not window.estimate_prize_card.isHidden()
    assert "Importa apuestas" in window.estimate_scenario_label.text()


def test_live_refresh_keeps_forecast_card_visible_without_bets(window):
    window.system = None
    window.external_scrutiny_bets = None
    window.live_matches = tuple(
        LiveMatch(i + 1, match.home, match.away, "", "", "", "Pendiente", False, 0)
        for i, match in enumerate(window.round.matches)
    )

    window.evaluate_live()

    assert not window.estimate_prize_card.isHidden()
    assert "Importa apuestas" in window.estimate_scenario_label.text()


def test_desktop_shows_live_progress_and_golden_forecast_card(window):
    assert window.prize_cards_layout.itemAt(0).widget() is window.estimate_prize_card
    assert window.prize_cards_layout.itemAt(1).widget() is window.official_prize_column
    bets = (Bet("1" * 14, "00"), Bet("1" * 14, "11"))
    window.system = window.service.imported(window.round, "Previsión", bets)
    window.estimate_model = {
        "played": ((1.0, 0.0, 0.0),) * 14,
        "market": ((1.0, 0.0, 0.0),) * 14,
        "pleno_home": (1.0, 0.0, 0.0, 0.0),
        "pleno_away": (1.0, 0.0, 0.0, 0.0),
        "revenue_cents": 100_000_000,
        "jackpot_cents": 5_000_000,
        "ticket_cents": 75,
        "source": "Fuente de prueba",
    }
    window.estimate_round_key = window.round.key
    window.live_matches = tuple(
        LiveMatch(i + 1, match.home, match.away, "1-0", "1" if i == 0 else "X" if i == 1 else "",
                  "", "Finalizado" if i < 2 else "Pendiente", i < 2, 1)
        for i, match in enumerate(window.round.matches)
    )
    outcome = engine.evaluate(bets, "1X" + "-" * 12, finalized=(True, True) + (False,) * 12)
    window.render_scrutiny(outcome, "", False)
    assert window.scrutiny_summary_hits.text() == "1"
    assert window.scrutiny_summary_misses.text() == "1"
    assert window.scrutiny_summary_pending.text() == "12"
    assert not window.estimate_prize_card.isHidden()
    assert window.estimate_total.text() != "—"
    assert "aproximación no oficial" in window.estimate_source_label.text()
    assert window.estimate_prize_card.minimumHeight() == 0
    assert len(window.estimate_category_rows) == 6
    assert window.estimate_rows_layout.count() == 6
    assert all(" apuestas · " in label.text() and not label.wordWrap() for label in window.estimate_category_rows.values())
    assert not window.estimate_prize_card.isHidden()
    assert not window.prize_notice.isHidden()
    assert window.prize_notice.minimumHeight() == 0
    assert window.scrutiny_lower_reserve() >= (
        max(window.estimate_prize_card.minimumHeight(), window.prize_notice.minimumHeight())
        + window.eval_summary.minimumHeight()
    )
    assert all('No publicado' in line for line in window.prize_notice.text().splitlines()[1:])
    assert all(label.font().pointSize() <= 11 for label in window.estimate_category_rows.values())
