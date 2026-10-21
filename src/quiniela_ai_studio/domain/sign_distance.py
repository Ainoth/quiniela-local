"""Exact maximum spacing between equal signs in the first 14 matches."""

from __future__ import annotations

from collections.abc import Sequence
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
