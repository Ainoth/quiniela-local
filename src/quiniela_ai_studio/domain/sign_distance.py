"""Exact maximum spacing between equal signs in the first 14 matches."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from functools import lru_cache
from itertools import pairwise


def maximum_sign_distance(column: str, sign: str) -> int:
    """Return the largest index difference between consecutive occurrences.

    ``V`` treats X and 2 as one family. A family appearing fewer than twice
    has distance zero. Positions refer only to the fourteen standard matches.
    """
    if len(column) != 14 or set(column) - set("1X2"):
        raise ValueError("La columna debe tener 14 signos 1/X/2.")
    if sign not in ("1", "X", "2", "V"):
        raise ValueError("La distancia requiere 1, X, 2 o V.")
    positions = [index for index, value in enumerate(column)
                 if (value != "1" if sign == "V" else value == sign)]
    return max((right - left for left, right in pairwise(positions)), default=0)


def possible_sign_distances(base: Sequence[str], sign: str) -> tuple[int, ...]:
    """Find all achievable maxima with a small exact dynamic program."""
    return _possible_sign_distances(tuple(base), sign)


def historical_sign_distance_recommendation(
    columns: Sequence[str], base: Sequence[str], coverage: float
) -> tuple[dict[str, set[int]], int, int, int]:
    """Recommend compatible distance values from joint historical profiles.

    The target is applied to complete 1/X/2/V distance tuples, rather than
    independently to each sign. This avoids compounding four marginal filters
    into a much narrower condition than the selected risk suggests. Returned
    ``matched`` is measured again after projecting the chosen tuples back into
    the four independently editable sign filters.
    """
    if not 0 < coverage <= 1:
        raise ValueError("La cobertura histórica debe estar entre 0 y 1.")
    signs = ("1", "X", "2", "V")
    reachable = {sign: set(possible_sign_distances(base, sign)) for sign in signs}
    profiles: Counter[tuple[int, int, int, int]] = Counter()
    eligible_columns: list[tuple[int, int, int, int]] = []
    for column in columns:
        profile = tuple(maximum_sign_distance(column, sign) for sign in signs)
        if all(value in reachable[sign] for sign, value in zip(signs, profile)):
            profiles[profile] += 1
            eligible_columns.append(profile)
    sample_size = sum(profiles.values())
    if not sample_size:
        raise ValueError("El histórico seleccionado no contiene distancias compatibles con la base actual.")

    target = max(1, int(sample_size * coverage + 0.999999))
    chosen_profiles: set[tuple[int, int, int, int]] = set()
    accumulated = 0
    for profile, amount in sorted(profiles.items(), key=lambda item: (-item[1], item[0])):
        chosen_profiles.add(profile)
        accumulated += amount
        if accumulated >= target:
            break

    recommendations = {
        sign: {profile[index] for profile in chosen_profiles}
        for index, sign in enumerate(signs)
    }
    matched = sum(
        all(profile[index] in recommendations[sign] for index, sign in enumerate(signs))
        for profile in eligible_columns
    )
    return recommendations, sample_size, matched, target


@lru_cache(maxsize=64)
def _possible_sign_distances(base: tuple[str, ...], sign: str) -> tuple[int, ...]:
    if len(base) != 14 or any(not item or set(item) - set("1X2") for item in base):
        raise ValueError("La base debe contener 14 selecciones válidas.")
    if sign not in ("1", "X", "2", "V"):
        raise ValueError("La distancia requiere 1, X, 2 o V.")
    states = {(-1, 0)}
    for index, picks in enumerate(base):
        following = set()
        for last, maximum in states:
            for value in picks:
                matches = value != "1" if sign == "V" else value == sign
                if matches:
                    following.add((index, max(maximum, index - last) if last >= 0 else maximum))
                else:
                    following.add((last, maximum))
        states = following
    return tuple(sorted({maximum for _last, maximum in states}))
