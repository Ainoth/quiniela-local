import pytest

from quiniela_ai_studio.domain.models import ProbabilitySnapshot
from quiniela_ai_studio.domain.value_signals import value_signals
from quiniela_studio.demo import demo_round


def test_value_signals_apply_market_to_public_ratio_thresholds():
    round_ = demo_round()
    signals = value_signals(
        round_.snapshot("sport"), round_.snapshot("public")
    )

    assert len(signals) == 42
    assert signals[0].ratio == pytest.approx(5 / 6)
    assert signals[0].label == "sobreapostado"
    assert signals[1].ratio == pytest.approx(1.2)
    assert signals[1].label == "infra-apostado"
    assert signals[2].ratio == pytest.approx(4 / 3)
    assert signals[2].label == "infra-apostado"


def test_value_signals_skip_rows_without_both_sources():
    round_ = demo_round()
    market = round_.snapshot("sport")
    public = round_.snapshot("public")
    market_rows = (None, *market.values[1:])
    market_partial = ProbabilitySnapshot(
        "sport", market.source, market.captured_at, market_rows
    )

    signals = value_signals(market_partial, public)

    assert len(signals) == 39
    assert all(signal.match_number != 1 for signal in signals)
