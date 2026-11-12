"""Comparación descriptiva entre probabilidad de mercado y popularidad."""

from __future__ import annotations

from dataclasses import dataclass

from .models import ProbabilitySnapshot


@dataclass(frozen=True)
class ValueSignal:
    """Ratio mercado/público para un signo; no expresa ROI ni premio esperado."""

    match_number: int
    sign: str
    market_probability: float
    public_probability: float
    ratio: float | None
    label: str


def value_signals(
    market: ProbabilitySnapshot, public: ProbabilitySnapshot
) -> tuple[ValueSignal, ...]:
    """Calcula CR = P(mercado) / Q(jugado), sin mezclar jornadas ni fuentes."""
    if market.kind != "sport" or public.kind != "public":
        raise ValueError("Se requieren instantáneas de mercado y porcentajes jugados.")
    if len(market.values) != len(public.values):
        raise ValueError("Las fuentes no contienen el mismo número de partidos.")
    output = []
    for index, (market_row, public_row) in enumerate(
        zip(market.values, public.values), 1
    ):
        if market_row is None or public_row is None:
            continue
        for sign, probability, crowd in zip("1X2", market_row, public_row):
            ratio = probability / crowd if crowd > 0 else None
            label = (
                "sin porcentaje jugado"
                if ratio is None
                else "infra-apostado" if ratio > 1.15
                else "sobreapostado" if ratio < 0.85
                else "sin diferencia marcada"
            )
            output.append(ValueSignal(index, sign, probability, crowd, ratio, label))
    return tuple(output)
