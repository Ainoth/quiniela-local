"""Reference checks for the independent Distancias reduction."""

from __future__ import annotations

import itertools

import pytest

from quiniela_ai_studio.domain.reduction_rules import (
    ReductionRule,
    rules_from_parameters,
)
from quiniela_ai_studio.domain.sign_distance import (
    historical_sign_distance_recommendation,
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


def test_historical_recommendation_uses_joint_profiles_and_risk_changes_values():
    columns = [
        "1" * 14, "X" * 14, "2" * 14, "1X" * 7, "12" * 7, "X2" * 7,
        "1" * 7 + "X" * 7, "X" * 7 + "2" * 7, "2" * 7 + "1" * 7,
    ] * 3
    base = ("1X2",) * 14
    broad = historical_sign_distance_recommendation(columns, base, .90)
    medium = historical_sign_distance_recommendation(columns, base, .70)
    selective = historical_sign_distance_recommendation(columns, base, .30)

    assert broad[1] == medium[1] == selective[1] == len(columns)
    assert broad[0] != medium[0]
    assert selective[0] != medium[0]
    assert broad[2] >= medium[2] >= selective[2]
    assert broad[3] >= medium[3] >= selective[3]


def test_historical_distance_recommendation_rejects_no_compatible_sample():
    with pytest.raises(ValueError, match="no contiene distancias compatibles"):
        historical_sign_distance_recommendation([], ("1X2",) * 14, .7)
