"""Filtros básicos compartidos: semántica del motor histórico, límites explícitos."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass

from quiniela_ai_studio.domain.models import validate_column
from quiniela_engine import FilterConfig

from .engine import Cancelled


@dataclass(frozen=True)
class BasicFilters:
    variants: tuple[int, int] = (0, 14)
    x_count: tuple[int, int] = (0, 14)
    two_count: tuple[int, int] = (0, 14)
    changes: tuple[int, int] = (0, 13)
    max_one_run: int = 14
    max_x_run: int = 14
    max_two_run: int = 14
    x_distance: tuple[int, int] = (1, 13)
    reference: str = ""
    coincidences: tuple[int, int] = (0, 14)

    def __post_init__(self):
        for limits, lower, upper in (
            (self.variants, 0, 14),
            (self.x_count, 0, 14),
            (self.two_count, 0, 14),
            (self.x_distance, 1, 13),
            (self.coincidences, 0, 14),
            (self.changes, 0, 13),
        ):
            if (
                len(limits) != 2
                or any(type(n) is not int for n in limits)
                or not lower <= limits[0] <= limits[1] <= upper
            ):
                raise ValueError("Los mínimos y máximos de filtros no son válidos.")
        if any(
            type(n) is not int or not 1 <= n <= 14
            for n in (self.max_one_run, self.max_x_run, self.max_two_run)
        ):
            raise ValueError("La racha máxima debe estar entre 1 y 14.")
        if self.reference:
            validate_column(self.reference)

    def apply(self, bets, cancelled: Callable[[], bool] = lambda: False):
        """Subconjunto de apuestas exactas; conserva Plenos y cantidades sin expansión."""
        config = FilterConfig(
            variants=self.variants,
            x_count=self.x_count,
            two_count=self.two_count,
            max_runs={"1": self.max_one_run, "X": self.max_x_run, "2": self.max_two_run},
            interruption_range=self.changes,
            distance_ranges={"X": self.x_distance},
            reference=tuple(self.reference) if self.reference else None,
            repetition_range=self.coincidences if self.reference else None,
        )
        result = []
        for index, bet in enumerate(bets):
            if index % 256 == 0 and cancelled():
                raise Cancelled("Cálculo de condiciones cancelado.")
            if config.accepts(tuple(bet.column)):
                result.append(bet)
        if cancelled():
            raise Cancelled("Cálculo de condiciones cancelado.")
        return tuple(result)

    def parameters(self):
        return dict(id="basic-local-v2", version=2, **asdict(self))


def quick_conditions(level: int) -> BasicFilters:
    """Original local presets, reversed per user request: 0 strict, 10 neutral.

    Uses the historical ties-to-even rounding; this only proposes conditions,
    never a forecast, reduction guarantee or target number of columns.
    """
    if type(level) is not int or not 0 <= level <= 10:
        raise ValueError("El nivel debe estar entre 0 y 10.")
    if level == 10:
        return BasicFilters()
    strength = 10 - level
    return BasicFilters(
        variants=(round(strength * 0.5), round(14 - strength * 0.6)),
        x_count=(round(strength * 0.2), round(14 - strength * 0.8)),
        two_count=(round(strength * 0.1), round(14 - strength * 0.9)),
        changes=(round(strength * 0.5), round(13 - strength * 0.3)),
        max_one_run=max(4, 14 - strength),
        max_x_run=max(2, 12 - strength),
        max_two_run=max(2, 12 - strength),
    )
