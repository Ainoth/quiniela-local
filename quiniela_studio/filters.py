"""Filtros básicos compartidos: semántica del motor histórico, límites explícitos."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from quiniela_engine import FilterConfig

from .domain import validate_column


@dataclass(frozen=True)
class BasicFilters:
    variants: tuple[int, int] = (0, 14)
    x_count: tuple[int, int] = (0, 14)
    two_count: tuple[int, int] = (0, 14)
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
        ):
            if (
                len(limits) != 2
                or any(type(n) is not int for n in limits)
                or not lower <= limits[0] <= limits[1] <= upper
            ):
                raise ValueError("Los mínimos y máximos de filtros no son válidos.")
        if any(
            type(n) is not int or not 1 <= n <= 14
            for n in (self.max_x_run, self.max_two_run)
        ):
            raise ValueError("La racha máxima debe estar entre 1 y 14.")
        if self.reference:
            validate_column(self.reference)

    def apply(self, bets):
        """Subconjunto de apuestas exactas; conserva Plenos y cantidades sin expansión."""
        config = FilterConfig(
            variants=self.variants,
            x_count=self.x_count,
            two_count=self.two_count,
            max_runs={"X": self.max_x_run, "2": self.max_two_run},
            distance_ranges={"X": self.x_distance},
            reference=tuple(self.reference) if self.reference else None,
            repetition_range=self.coincidences if self.reference else None,
        )
        return tuple(bet for bet in bets if config.accepts(tuple(bet.column)))

    def parameters(self):
        return dict(id="basic-local-v1", version=1, **asdict(self))
