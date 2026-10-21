"""Oráculos exactos para el generador Normal y sus archivos abiertos."""

import itertools
import json
import math

import pytest

from quiniela_ai_studio.domain.normal_generation import (
    ProbabilitySource,
    best_base,
    best_base_under_limit,
    combine_action_columns,
    generate_base_action,
    import_probability_source,
    iter_ranked_columns,
    normalize_percentages,
    parse_columns_file,
    select_ranked_action,
    theoretical_count,
    validate_percentages,
    weighted_probabilities,
)
from quiniela_studio.demo import demo_round


def test_exact_top_k_matches_exhaustive_enumeration_and_ties_are_lexical():
    values = [(0.5, 0.3, 0.2)] * 12 + [(0.7, 0.2, 0.1), (0.4, 0.35, 0.25)]
    base = ("1",) * 12 + ("1X2", "1X2")
    got = list(iter_ranked_columns(values, base=base, limit=9))
    exhaustive = []
    for last_two in itertools.product("1X2", repeat=2):
        column = "1" * 12 + "".join(last_two)
        probability = math.prod(values[i]["1X2".index(sign)] for i, sign in enumerate(column))
        exhaustive.append((column, probability))
    expected = sorted(exhaustive, key=lambda pair: (-pair[1], pair[0]))
    assert [column for _, column, _ in got] == [column for column, _ in expected]
    assert [p for _, _, p in got] == pytest.approx([p for _, p in expected])
    assert [position for position, *_ in got] == list(range(1, 10))


def test_equal_probability_ties_use_documented_sign_order_1_x_2():
    values = [(1 / 3, 1 / 3, 1 / 3)] * 14
    base = ("1X2", "1X2") + ("1",) * 12
    got = [column[:2] for _position, column, _probability in iter_ranked_columns(values, base=base, limit=9)]
    assert got == ["11", "1X", "12", "X1", "XX", "X2", "21", "2X", "22"]


def test_endings_are_one_based_and_keep_exact_positions():
    values = [(1 / 3, 1 / 3, 1 / 3)] * 14
    result = select_ranked_action(values, count=100_000, endings=(5, 7))
    assert result.ranked_count == 100_000
    assert result.rejected_terminations == 80_000
    assert len(result.columns) == 20_000
    assert result.first_position == 5
    assert result.last_position == 99_997
    # In a tie the lexical order begins at the all-1 column and advances by the final position.
    ranked = dict((position, column) for position, column, _ in iter_ranked_columns(values, limit=100_000))
    assert result.columns[:2] == (ranked[5], ranked[7])
    assert result.columns[-1] == ranked[99_997]


def test_triples_doubles_and_base_counts_are_exact():
    values = [(0.62, 0.25, 0.13)] * 14
    base, report = best_base(values, 6, 6)
    assert (len(base), report["triples"], report["doubles"], report["fixed"]) == (14, 6, 6, 2)
    assert theoretical_count(7, 7) == 279_936
    assert len(generate_base_action(values, base).columns) == theoretical_count(6, 6)
    with pytest.raises(ValueError, match="no supere"):
        best_base(values, 8, 7)


def test_base_uses_exact_probability_mass_and_preserves_locks():
    rows = [(0.9, 0.08, 0.02)] * 14
    rows[5] = (0.34, 0.33, 0.33)
    base, report = best_base(rows, 1, 1, locks=(True,) + (False,) * 13, locked_base=("X",) + ("1",) * 13)
    assert base[0] == "X"
    assert sum(len(value) == 3 for value in base) == 1
    assert sum(len(value) == 2 for value in base) == 1
    assert report["decisions"][0]["locked"]
    assert report["decisions"][0]["excluded_mass"] == pytest.approx(0.92)


def test_automatic_base_selects_quantities_exactly_under_column_limit():
    rows = [(0.6, 0.25, 0.15)] * 14
    base, report = best_base_under_limit(rows, 6)
    assert report["criteria"] == "maximizar_probabilidad_conjunta_bajo_limite_columnas_v1"
    assert (report["triples"], report["doubles"], report["fixed"]) == (1, 1, 12)
    assert report["columns"] == theoretical_count(1, 1) == 6
    assert report["retained_probability"] == pytest.approx((0.6 ** 12) * 0.85)
    assert sum(len(signs) == 3 for signs in base) == report["triples"]
    assert sum(len(signs) == 2 for signs in base) == report["doubles"]


def test_automatic_base_respects_locked_width_and_impossible_limit():
    rows = [(0.6, 0.25, 0.15)] * 14
    locks = (True,) + (False,) * 13
    base, report = best_base_under_limit(rows, 6, locks, ("1X",) + ("1",) * 13)
    assert base[0] == "1X"
    assert report["doubles"] >= 1
    with pytest.raises(ValueError, match="bloqueados"):
        best_base_under_limit(rows, 1, locks, ("1X",) + ("1",) * 13)


def test_bundled_historical_results_load_and_include_verified_scores():
    from quiniela_ai_studio.infrastructure.historical_results import bundled_results

    rows = bundled_results()
    assert len(rows) >= 2_500
    assert all(len(row["results14"]) == 14 for row in rows)
    enriched = [row for row in rows if row.get("score_01")]
    assert len(enriched) >= 800
    assert all(row.get("score_15") for row in enriched)
    for row in enriched:
        signs = "".join("1" if int(row[f"score_{i:02}"].split("-")[0]) > int(row[f"score_{i:02}"].split("-")[1]) else "2" if int(row[f"score_{i:02}"].split("-")[0]) < int(row[f"score_{i:02}"].split("-")[1]) else "X" for i in range(1, 15))
        assert signs == row["results14"]


def test_percentages_validation_and_explicit_normalization():
    with pytest.raises(ValueError, match="sumar 100"):
        validate_percentages([(.4, .3, .2)] * 14)
    normalized = normalize_percentages([(40, 30, 20)] * 14)
    assert normalized[0] == pytest.approx((0.4445, 0.3333, 0.2222))
    assert sum(normalized[0]) == pytest.approx(1)


def test_weighted_sources_and_round_isolation():
    round_ = demo_round()
    a = ProbabilitySource(round_.key, "Clasificación importada", "2026-10-15T10:00:00+02:00", ((.6, .3, .1),) * 14, "classification")
    b = ProbabilitySource(round_.key, "Forma CSV", "2026-10-15T10:00:00+02:00", ((.2, .3, .5),) * 14, "form5")
    assert weighted_probabilities(((a, 50), (b, 50)))[0] == pytest.approx((.4, .3, .3))
    with pytest.raises(ValueError, match="jornadas"):
        other = ProbabilitySource("other", "otra", "2026-10-15T10:00:00+02:00", ((.2, .3, .5),) * 14)
        weighted_probabilities(((a, 50), (other, 50)))


def test_csv_probability_import_checks_order_teams_sums_and_identity():
    round_ = demo_round()
    header = "number,home,away,p1,px,p2,source,captured_at,kind\n"
    body = "".join(f'{i},{m.home},{m.away},50,30,20,Test fixture,2026-10-15T10:00:00+02:00,form5\n' for i, m in enumerate(round_.matches[:14], 1))
    source = import_probability_source((header + body).encode(), round_key=round_.key, matches=round_.matches, filename="form.csv")
    assert source.kind == "form5" and source.values[0] == pytest.approx((.5, .3, .2))
    with pytest.raises(ValueError, match="no coinciden"):
        import_probability_source((header + body.replace(round_.matches[0].home, "Otro", 1)).encode(), round_key=round_.key, matches=round_.matches)


def test_json_probability_import_and_invalid_round():
    round_ = demo_round()
    payload = dict(schema="quiniela_ai_studio.probabilities", version=1, round_key=round_.key,
                   source="CSV convertido", captured_at="2026-10-15T10:00:00+02:00", kind="history",
                   matches=[dict(number=i, home=m.home, away=m.away, p1=50, px=30, p2=20) for i, m in enumerate(round_.matches[:14], 1)])
    source = import_probability_source(json.dumps(payload).encode(), round_key=round_.key, matches=round_.matches)
    assert source.kind == "history"
    payload["round_key"] = "otra"
    with pytest.raises(ValueError, match="no coincide"):
        import_probability_source(json.dumps(payload).encode(), round_key=round_.key, matches=round_.matches)


def test_concatenation_union_and_intersection_are_exact():
    a = "1" * 14
    b = "X" * 14
    c = "2" * 14
    assert combine_action_columns(((a, b), (b, c)), keep_duplicates=True, intersection=False) == ((a, b, b, c), 1)
    assert combine_action_columns(((a, b), (b, c)), keep_duplicates=False, intersection=False) == ((a, b, c), 1)
    assert combine_action_columns(((a, b), (b, c), (a, b, c)), keep_duplicates=False, intersection=True) == ((b,), 6)


def test_cp_minimum_is_product_probability_and_range_is_inclusive():
    rows = [(1.0, 0.0, 0.0)] * 14
    result = select_ranked_action(rows, count=10, start=2, end=5, minimum_probability=.5)
    assert result.ranked_count == 4
    assert result.rejected_coefficient == 4
    assert result.columns == ()
    skewed = [(0.9, 0.1, 0.0)] * 14
    assert select_ranked_action(skewed, count=1, maximum_probability=0.2).rejected_coefficient == 1
    assert select_ranked_action(skewed, count=1, maximum_probability=0.23).columns == ("1" * 14,)
    with pytest.raises(ValueError, match="rango C.P."):
        select_ranked_action(skewed, count=1, minimum_probability=0.3, maximum_probability=0.2)


def test_column_import_accepts_txt_and_open_json_only():
    assert parse_columns_file(("1" * 14 + "\n" + "X" * 14 + "\n").encode()) == ("1" * 14, "X" * 14)
    payload = json.dumps(dict(schema="quiniela_ai_studio.columns", version=1, columns=[dict(signs14="2" * 14)])).encode()
    assert parse_columns_file(payload) == ("2" * 14,)
    with pytest.raises(ValueError, match="no compatible"):
        parse_columns_file(b'{"columns":["11111111111111"]}')
