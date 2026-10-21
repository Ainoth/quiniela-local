"""Filtros básicos compartidos: semántica del motor histórico, límites explícitos."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from quiniela_ai_studio.domain.models import validate_column
from quiniela_engine import FilterConfig

from .advanced_conditions import AdvancedConditions, advanced_from_parameters
from .engine import Cancelled
from .reduction_rules import ReductionRule, rules_from_parameters


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
    advanced: AdvancedConditions = field(default_factory=AdvancedConditions)
    reduction_rules: tuple[ReductionRule, ...] = ()
    reduction_tabs_enabled: tuple[int, ...] = tuple(range(17))
    quick_conditions_active: bool = False

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
        if (len(set(self.reduction_tabs_enabled)) != len(self.reduction_tabs_enabled)
                or any(type(index) is not int or not 0 <= index < 19 for index in self.reduction_tabs_enabled)):
            raise ValueError('La activación de pestañas de reducción no es válida.')

    def apply(self, bets, cancelled: Callable[[], bool] = lambda: False):
        """Subconjunto de apuestas exactas; conserva Plenos y cantidades sin expansión."""
        enabled_tabs=set(self.reduction_tabs_enabled)
        variants=self.variants if 0 in enabled_tabs or self.quick_conditions_active else (0,14)
        x_count=self.x_count if 0 in enabled_tabs or self.quick_conditions_active else (0,14)
        two_count=self.two_count if 0 in enabled_tabs or self.quick_conditions_active else (0,14)
        max_runs={sign:(value if 1 in enabled_tabs or self.quick_conditions_active else 14) for sign,value in
                  (('1',self.max_one_run),('X',self.max_x_run),('2',self.max_two_run))}
        changes=self.changes if 2 in enabled_tabs or self.quick_conditions_active else (0,13)
        # Cuenta exposes this existing filter next to its count matrix while
        # Cambio remains an independent owner for the same single condition.
        distance=self.x_distance if (0 in enabled_tabs or 2 in enabled_tabs or self.quick_conditions_active) else (1,13)
        reference=self.reference if 8 in enabled_tabs else ''
        config = FilterConfig(
            variants=variants,
            x_count=x_count,
            two_count=two_count,
            max_runs=max_runs,
            interruption_range=changes,
            distance_ranges={"X": distance},
            reference=tuple(reference) if reference else None,
            repetition_range=self.coincidences if reference else None,
        )
        result = []
        for index, bet in enumerate(bets):
            if index % 256 == 0 and cancelled():
                raise Cancelled("Cálculo de condiciones cancelado.")
            if (config.accepts(tuple(bet.column)) and self.advanced.accepts(bet.column)
                    and all(not rule.active or (rule.tab_index>=0 and rule.tab_index not in enabled_tabs) or rule.accepts(bet.column)
                            for rule in self.reduction_rules)):
                result.append(bet)
        if cancelled():
            raise Cancelled("Cálculo de condiciones cancelado.")
        return tuple(result)

    def parameters(self):
        parameters = asdict(self)
        parameters["advanced"] = self.advanced.parameters()
        parameters["reduction_rules"] = [rule.parameters() for rule in self.reduction_rules]
        return dict(id="basic-local-v5", version=5, **parameters)


def filters_from_parameters(parameters: dict) -> BasicFilters:
    """Read old filter versions and the current optional advanced conditions."""
    values = dict(parameters)
    values.pop("id", None)
    values.pop("version", None)
    values['reduction_tabs_enabled'] = tuple(values.get('reduction_tabs_enabled', range(17)))
    values["advanced"] = advanced_from_parameters(values.get("advanced"))
    values["reduction_rules"] = rules_from_parameters(values.get("reduction_rules"))
    return BasicFilters(**values)


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
