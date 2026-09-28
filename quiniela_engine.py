"""Motor combinatorio independiente de la interfaz de Quiniela Local."""

from __future__ import annotations

import itertools
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Mapping, Sequence

SIGNS = ("1", "X", "2")
Column = tuple[str, ...]


def normalize_base(base: Sequence[Iterable[str]]) -> tuple[frozenset[str], ...]:
    result = tuple(frozenset(item) for item in base)
    if not result or any(not item or not item <= set(SIGNS) for item in result):
        raise ValueError("Cada partido debe admitir al menos un signo válido: 1, X o 2")
    return result


def generate_columns(base: Sequence[Iterable[str]]) -> Iterator[Column]:
    normalized = normalize_base(base)
    ordered = [tuple(sign for sign in SIGNS if sign in allowed) for allowed in normalized]
    yield from itertools.product(*ordered)


def development_size(base: Sequence[Iterable[str]]) -> int:
    return math.prod(len(item) for item in normalize_base(base))


@dataclass(frozen=True)
class ProbabilitySource:
    name: str
    probabilities: tuple[tuple[float, float, float], ...]


def compose_probabilities(
    sources: Mapping[str, ProbabilitySource], weights: Mapping[str, float]
) -> tuple[tuple[float, float, float], ...]:
    active = [(sources[name], float(weight)) for name, weight in weights.items() if weight > 0]
    if not active:
        raise ValueError("La fuente compuesta necesita al menos una ponderación positiva")
    length = len(active[0][0].probabilities)
    if any(len(source.probabilities) != length for source, _ in active):
        raise ValueError("Todas las fuentes deben contener los mismos partidos")
    total_weight = sum(weight for _, weight in active)
    rows = []
    for index in range(length):
        row = tuple(sum(source.probabilities[index][i] * weight for source, weight in active) / total_weight for i in range(3))
        total = sum(row)
        rows.append(tuple(value / total for value in row))
    return tuple(rows)


def counts(column: Sequence[str]) -> dict[str, int]:
    value = Counter(column)
    return {"1": value["1"], "X": value["X"], "2": value["2"], "V": value["X"] + value["2"]}


def max_run(column: Sequence[str], sign: str) -> int:
    best = current = 0
    for item in column:
        current = current + 1 if item == sign else 0
        best = max(best, current)
    return best


def interruptions(column: Sequence[str]) -> int:
    return sum(left != right for left, right in zip(column, column[1:]))


def positions(column: Sequence[str], sign: str) -> tuple[int, ...]:
    return tuple(index + 1 for index, item in enumerate(column) if item == sign)


def distances(column: Sequence[str], sign: str) -> tuple[int, ...]:
    found = positions(column, sign)
    return tuple(right - left for left, right in zip(found, found[1:]))


def coincidences(left: Sequence[str], right: Sequence[str]) -> int:
    return sum(a == b for a, b in zip(left, right))


def figure(column: Sequence[str], groups: Sequence[Sequence[int]], signs: frozenset[str] = frozenset(("X", "2"))) -> tuple[int, ...]:
    return tuple(sum(column[index - 1] in signs for index in group) for group in groups)


def log_probability(column: Sequence[str], probabilities: Sequence[Sequence[float]]) -> float:
    return sum(math.log(max(float(probabilities[i][SIGNS.index(sign)]), 1e-300)) for i, sign in enumerate(column))


@dataclass
class GroupRule:
    name: str
    positions: tuple[int, ...]
    minimum: int
    maximum: int
    signs: frozenset[str] = frozenset(("X", "2"))

    def value(self, column: Sequence[str]) -> int:
        return sum(column[index - 1] in self.signs for index in self.positions)


@dataclass
class PatternGroup:
    name: str
    pattern: tuple[frozenset[str], ...]
    minimum: int
    maximum: int

    def hits(self, column: Sequence[str]) -> int:
        return sum(sign in admitted for sign, admitted in zip(column, self.pattern))


@dataclass
class FilterConfig:
    variants: tuple[int, int] | None = None
    x_count: tuple[int, int] | None = None
    two_count: tuple[int, int] | None = None
    max_runs: dict[str, int] = field(default_factory=dict)
    interruption_range: tuple[int, int] | None = None
    distance_ranges: dict[str, tuple[int, int]] = field(default_factory=dict)
    reference: Column | None = None
    repetition_range: tuple[int, int] | None = None
    allowed_figures: set[tuple[int, ...]] | None = None
    figure_groups: tuple[tuple[int, ...], ...] = ()
    group_rules: list[GroupRule] = field(default_factory=list)
    pattern_groups: list[PatternGroup] = field(default_factory=list)
    allowed_group_failures: int = 0
    group_hit_sum: tuple[int, int] | None = None
    values: tuple[Mapping[str, float], ...] | None = None
    value_range: tuple[float, float] | None = None
    log_probability_range: tuple[float, float] | None = None

    def accepts(self, column: Column, probabilities: Sequence[Sequence[float]] | None = None) -> bool:
        totals = counts(column)
        for value, limits in ((totals["V"], self.variants), (totals["X"], self.x_count), (totals["2"], self.two_count)):
            if limits and not limits[0] <= value <= limits[1]:
                return False
        if any(max_run(column, sign) > maximum for sign, maximum in self.max_runs.items()):
            return False
        if self.interruption_range and not self.interruption_range[0] <= interruptions(column) <= self.interruption_range[1]:
            return False
        for sign, limits in self.distance_ranges.items():
            if any(not limits[0] <= distance <= limits[1] for distance in distances(column, sign)):
                return False
        if self.reference and self.repetition_range:
            if not self.repetition_range[0] <= coincidences(column, self.reference) <= self.repetition_range[1]:
                return False
        if self.allowed_figures is not None and figure(column, self.figure_groups) not in self.allowed_figures:
            return False
        if any(not rule.minimum <= rule.value(column) <= rule.maximum for rule in self.group_rules):
            return False
        hits = [group.hits(column) for group in self.pattern_groups]
        failures = sum(not group.minimum <= hit <= group.maximum for group, hit in zip(self.pattern_groups, hits))
        if failures > self.allowed_group_failures:
            return False
        if self.group_hit_sum and not self.group_hit_sum[0] <= sum(hits) <= self.group_hit_sum[1]:
            return False
        if self.values and self.value_range:
            value = sum(self.values[i][sign] for i, sign in enumerate(column))
            if not self.value_range[0] <= value <= self.value_range[1]:
                return False
        if self.log_probability_range:
            if probabilities is None:
                raise ValueError("El filtro de probabilidad necesita porcentajes")
            value = log_probability(column, probabilities)
            if not self.log_probability_range[0] <= value <= self.log_probability_range[1]:
                return False
        return True


def filter_columns(columns: Iterable[Column], config: FilterConfig, probabilities=None) -> Iterator[Column]:
    for column in columns:
        if config.accepts(column, probabilities):
            yield column


def rank_columns(columns: Iterable[Column], probabilities: Sequence[Sequence[float]]) -> list[tuple[Column, float]]:
    ranked = [(column, log_probability(column, probabilities)) for column in columns]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked


def reduce_columns(columns: Sequence[Column], target: int, probabilities=None) -> list[Column]:
    """Reducción práctica: conserva probabilidad y maximiza diversidad Hamming."""
    if target <= 0:
        return []
    remaining = list(dict.fromkeys(columns))
    if len(remaining) <= target:
        return remaining
    if probabilities:
        remaining.sort(key=lambda item: log_probability(item, probabilities), reverse=True)
    selected = [remaining.pop(0)]
    while remaining and len(selected) < target:
        best = max(
            remaining,
            key=lambda candidate: (
                min(len(candidate) - coincidences(candidate, chosen) for chosen in selected),
                log_probability(candidate, probabilities) if probabilities else 0,
            ),
        )
        selected.append(best)
        remaining.remove(best)
    return selected


def analyze(columns: Sequence[Column], probabilities=None) -> dict[str, object]:
    if not columns:
        return {"columns": 0}
    result: dict[str, object] = {
        "columns": len(columns),
        "average_variants": sum(counts(column)["V"] for column in columns) / len(columns),
        "average_x": sum(counts(column)["X"] for column in columns) / len(columns),
        "average_2": sum(counts(column)["2"] for column in columns) / len(columns),
    }
    if probabilities:
        logs = [log_probability(column, probabilities) for column in columns]
        result["probability_mass"] = sum(math.exp(value) for value in logs)
        result["best_probability"] = math.exp(max(logs))
    return result
