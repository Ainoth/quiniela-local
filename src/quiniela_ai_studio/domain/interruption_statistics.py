"""Exact transition and interruption-figure calculations for 14-sign columns."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Iterable, Sequence
from itertools import pairwise


def interruption_profile(column: str) -> tuple[int, int, str]:
    """Return (change count, longest consecutive changes, exact run figure).

    There are thirteen transitions in a 14-sign column. A transition is an
    interruption iff the adjacent signs differ. Consecutive interruptions are
    grouped as maximal runs and the displayed figure is sorted descending.
    The Pleno al 15 is never part of this calculation.
    """
    _validate_column(column)
    runs: list[int] = []
    current = 0
    for left, right in pairwise(column):
        if left != right:
            current += 1
        elif current:
            runs.append(current)
            current = 0
    if current:
        runs.append(current)
    ordered = tuple(sorted(runs, reverse=True))
    return sum(ordered), max(ordered, default=0), "-".join(map(str, ordered))


def possible_interruption_profiles(
    base: Sequence[str],
) -> tuple[tuple[int, int, str], ...]:
    """Enumerate exact reachable transition profiles without expanding columns.

    Dynamic-programming states retain the final sign, the current change run,
    and the completed run partition. With fourteen positions this stays small
    even when the quiniela base represents millions of possible columns.
    """
    _validate_base(base)
    states = {(sign, 0, ()) for sign in dict.fromkeys(base[0])}
    for pick in base[1:]:
        following = set()
        for previous, current, closed in states:
            for sign in dict.fromkeys(pick):
                if sign != previous:
                    following.add((sign, current + 1, closed))
                else:
                    next_closed = (
                        tuple(sorted((*closed, current), reverse=True))
                        if current
                        else closed
                    )
                    following.add((sign, 0, next_closed))
        states = following
    profiles = set()
    for _last, current, closed in states:
        parts = tuple(sorted((*closed, current), reverse=True)) if current else closed
        total = sum(parts)
        profiles.add((total, max(parts, default=0), "-".join(map(str, parts))))
    return tuple(sorted(profiles))


def random_interruption_recommendation(
    base: Sequence[str],
    seed: int,
    coverage: float,
) -> tuple[set[tuple[int, int]], set[tuple[int, str]]]:
    """Choose a reproducible subset of reachable joint profiles.

    This is an original, provisional sampling policy. ``coverage`` controls
    the fraction of distinct reachable profiles retained; it is not a success
    probability or an estimate of lottery winnings.
    """
    profiles = possible_interruption_profiles(base)
    if type(seed) is not int or seed < 0 or not 0 < coverage <= 1:
        raise ValueError("Semilla o cobertura de interrupciones no válida.")
    count = max(1, min(len(profiles), round(len(profiles) * coverage)))
    selected = random.Random(seed).sample(profiles, count)
    return (
        {(total, maximum) for total, maximum, _figure in selected},
        {(total, figure) for total, _maximum, figure in selected},
    )


def historical_interruption_recommendation(
    columns: Iterable[str],
    base: Sequence[str],
    coverage: float,
) -> tuple[set[tuple[int, int]], set[tuple[int, str]], int, int]:
    """Recommend reachable joint profiles by their observed historical count.

    Returns selected matrix pairs, selected (total, figure) pairs, number of
    final results examined, and number matched by the recommendation. This is
    descriptive of the chosen historical sample, not a forecast.
    """
    if not 0 < coverage <= 1:
        raise ValueError("La cobertura histórica debe estar entre 0 y 1.")
    reachable = set(possible_interruption_profiles(base))
    counts = Counter(
        profile
        for column in columns
        if (profile := interruption_profile(column)) in reachable
    )
    if not counts:
        raise ValueError("No hay resultados históricos compatibles con la base actual.")
    ordered = sorted(counts, key=lambda profile: (-counts[profile], profile))
    target = max(1, int(sum(counts.values()) * coverage + 0.999999))
    selected = []
    matched = 0
    for profile in ordered:
        selected.append(profile)
        matched += counts[profile]
        if matched >= target:
            break
    return (
        {(total, maximum) for total, maximum, _figure in selected},
        {(total, figure) for total, _maximum, figure in selected},
        sum(counts.values()),
        matched,
    )


def _validate_column(column: str) -> None:
    if (
        not isinstance(column, str)
        or len(column) != 14
        or any(sign not in "1X2" for sign in column)
    ):
        raise ValueError("Cada columna debe contener exactamente 14 signos 1/X/2.")


def _validate_base(base: Sequence[str]) -> None:
    if len(base) != 14 or any(
        not isinstance(pick, str) or not pick or set(pick) - set("1X2") for pick in base
    ):
        raise ValueError("La base debe contener 14 selecciones válidas 1/X/2.")
