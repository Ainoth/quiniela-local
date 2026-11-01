"""Scenario-based, indicative awards; never interchangeable with published payouts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from quiniela_ai_studio.domain.models import Bet

# Shares of the total round revenue. The Pleno pool also includes the reported jackpot.
POOL_SHARES = {10: 0.09, 11: 0.075, 12: 0.075, 13: 0.075, 14: 0.16, 15: 0.075}


def _hit_distribution(probabilities: Sequence[Sequence[float]], signs: str) -> tuple[float, ...]:
    distribution = [1.0] + [0.0] * 14
    for index, sign in enumerate(signs):
        hit = probabilities[index]["1X2".index(sign)]
        for count in range(index + 1, -1, -1):
            missed = distribution[count] * (1.0 - hit)
            gained = distribution[count - 1] * hit if count else 0.0
            distribution[count] = missed + gained
    return tuple(distribution)


def estimate_prizes(
    bets: Sequence[Bet],
    model: Mapping,
    result_signs: Mapping[int, str] | None = None,
    pleno_result: str = "",
) -> dict:
    """Estimate own category payouts for current results + favorites for pending games."""
    if not bets:
        raise ValueError("Abre o importa apuestas para calcular la previsión.")
    played = model.get("played")
    market = model.get("market") or played
    if not isinstance(played, (tuple, list)) or len(played) != 14 or len(market) != 14:
        raise ValueError("Faltan porcentajes publicados para la previsión.")
    signs = []
    actual = result_signs or {}
    for index in range(14):
        value = actual.get(index + 1, "")
        if value not in ("1", "X", "2"):
            row = market[index]
            value = "1X2"[max(range(3), key=lambda pos: row[pos])]
        signs.append(value)
    scenario = "".join(signs)

    home = model.get("pleno_home", ())
    away = model.get("pleno_away", ())
    if pleno_result and len(pleno_result) == 2 and set(pleno_result) <= set("012M"):
        pair = pleno_result
    elif len(home) == 4 and len(away) == 4:
        pair = max(
            ("".join(("012M"[a], "012M"[b])) for a in range(4) for b in range(4)),
            key=lambda value: home["012M".index(value[0])] * away["012M".index(value[1])],
        )
    else:
        pair = "00"

    distribution = _hit_distribution(played, scenario)
    pleno_probability = home["012M".index(pair[0])] * away["012M".index(pair[1])] if len(home) == len(away) == 4 else 0.0
    revenue = int(model.get("revenue_cents", 0))
    ticket = int(model.get("ticket_cents", 0))
    jackpot = int(model.get("jackpot_cents", 0))
    if revenue <= 0 or ticket <= 0:
        raise ValueError("La fuente no ha publicado recaudación o precio válidos.")
    public_entries = revenue / ticket
    expected = {category: public_entries * distribution[category] for category in range(10, 15)}
    expected[15] = expected[14] * pleno_probability
    pools = {category: revenue * share for category, share in POOL_SHARES.items()}
    pools[15] += jackpot
    unit = {
        category: min(pools[category] / expected[category], pools[category]) if expected[category] > 0 else 0.0
        for category in range(10, 15)
    }
    # The 14 pool is shared by every 14-hit bet, including the subset that also wins 15.
    unit[15] = unit[14] + (min(pools[15] / expected[15], pools[15]) if expected[15] > 0 else 0.0)

    own = {category: 0 for category in range(10, 16)}
    for bet in bets:
        hits = sum(left == right for left, right in zip(bet.column, scenario))
        if hits == 14 and bet.pleno == pair:
            own[15] += bet.quantity
        elif 10 <= hits <= 14:
            own[hits] += bet.quantity
    rows = []
    total = 0
    for category in (15, 14, 13, 12, 11, 10):
        amount = max(0, round(unit[category]))
        subtotal = amount * own[category]
        total += subtotal
        rows.append({
            "category": category,
            "own_bets": own[category],
            "expected_public_winners": expected[category],
            "unit_cents": amount,
            "subtotal_cents": subtotal,
        })
    return {
        "scenario": scenario,
        "pleno": pair,
        "total_cents": total,
        "revenue_cents": revenue,
        "jackpot_cents": jackpot,
        "public_entries": round(public_entries),
        "rows": tuple(rows),
        "source": model.get("source", "Quinielista · estimación orientativa"),
        "url": model.get("url", ""),
        "captured_at": model.get("captured_at"),
    }
