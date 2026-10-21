"""Reference checks for the independent Distancias reduction."""

from __future__ import annotations

import itertools

import pytest

from quiniela_ai_studio.domain.reduction_rules import (
    ReductionRule,
    rules_from_parameters,
)
from quiniela_ai_studio.domain.sign_distance import (
    maximum_sign_distance,
    possible_sign_distances,
)


def test_distances_are_index_differences_and_variants_share_a_family():
    assert maximum_sign_distance("1XX1" + "1" * 10, "1") == 3
    assert maximum_sign_distance("X2" + "1" * 12, "V") == 1
    assert maximum_sign_distance("X" + "1" * 13, "X") == 0
    assert maximum_sign_distance("1" * 14, "V") == 0


def test_dynamic_program_matches_exhaustive_small_base():
    base = ("1X2", "12", "X2", "1X", "1", "2", "1", "X",
            "1", "1", "2", "1", "X", "1")
    for sign in ("1", "X", "2", "V"):
        expected = {maximum_sign_distance("".join(column), sign)
                    for column in itertools.product(*base)}
        assert set(possible_sign_distances(base, sign)) == expected


def test_distance_rule_accepts_discrete_values_and_round_trips():
    rule = ReductionRule("distance-1", "allowed_sign_distance", 0, 13,
                         sign="1", allowed_values=(3, 4), tab_index=18)
    assert rule.accepts("1XX1" + "1" * 10)
    assert not rule.accepts("11X1" + "1" * 10)
    assert rules_from_parameters((rule.parameters(),)) == (rule,)
    with pytest.raises(ValueError):
        ReductionRule("invalid", "allowed_sign_distance", 0, 14,
                      sign="V", allowed_values=(14,), tab_index=18)
