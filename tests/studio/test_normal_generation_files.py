
import pytest

from quiniela_ai_studio.domain.normal_generation import parse_columns_file
from quiniela_ai_studio.infrastructure.normal_generation import generate_actions_file


def _small_space():
    probabilities = ((.6, .3, .1), (.2, .5, .3)) + ((1, 0, 0),) * 12
    base = ("1X2", "1X2") + ("1",) * 12
    return probabilities, base


def test_action_file_uses_exact_rank_terminations_union_and_audit(tmp_path):
    probabilities, base = _small_space()
    target = tmp_path / "columns.txt"
    report = generate_actions_file(target, [
        dict(label="A", probabilities=probabilities, base=base, rank_start=1, rank_end=5, endings=(1, 2)),
        dict(label="B", probabilities=probabilities, base=base, rank_start=1, rank_end=5, endings=(2, 3)),
    ])
    lines = target.read_text().splitlines()
    assert len(lines) == report["count_final"]
    assert len(lines) == len(set(lines))
    assert report["count_before_combination"] == 4
    assert report["duplicates_removed"] == 1
    assert report["columns_removed_by_intersection"] == 0
    assert report["actions"][0]["rejected_endings"] == 3
    assert report["actions"][0]["ranking_method"].startswith("exact best-first")
    assert parse_columns_file(target.read_bytes()) == tuple(lines)


def test_action_file_intersection_and_terminations_keep_original_positions(tmp_path):
    probabilities, base = _small_space()
    target = tmp_path / "intersection.json"
    report = generate_actions_file(target, [
        dict(label="all", probabilities=probabilities, base=base, rank_start=1, rank_end=9, endings=()),
        dict(label="odd rank", probabilities=probabilities, base=base, rank_start=1, rank_end=9, endings=(1, 3, 5, 7, 9)),
    ], intersection=True, keep_duplicates=True)
    columns = parse_columns_file(target.read_bytes())
    assert len(columns) == 5
    assert report["intersection"] is True
    assert report["keep_duplicates"] is True
    assert report["duplicates_removed"] == 0
    assert report["columns_removed_by_intersection"] == 9
    assert report["combination"] == "intersección"


def test_each_action_ranks_with_its_own_probability_source(tmp_path):
    source_a = [(0.8, 0.1, 0.1)] * 14
    source_b = [(0.1, 0.8, 0.1)] * 14
    actions = [
        dict(label="Mercado", probabilities=source_a, source={"source": "Mercado"}, rank_start=1, rank_end=1),
        dict(label="Popularidad", probabilities=source_b, source={"source": "Popularidad"}, rank_start=1, rank_end=1),
    ]
    path = tmp_path / "sources.txt"
    report = generate_actions_file(path, actions, keep_duplicates=True)
    assert path.read_text().splitlines() == ["1" * 14, "X" * 14]
    assert [item["source"]["source"] for item in report["actions"]] == ["Mercado", "Popularidad"]


def test_imported_columns_audit_keeps_filename_and_content_hash(tmp_path):
    path = tmp_path / "imported.txt"
    report = generate_actions_file(path, [dict(label="Local", imported_columns=("1" * 14,),
        rank_start=1, rank_end=1, source_audit={"file_name": "mias.txt", "columns_sha256": "abc"})])
    assert parse_columns_file(path.read_bytes()) == ("1" * 14,)
    assert report["actions"][0]["source"] == {"file_name": "mias.txt", "columns_sha256": "abc"}


def test_cancel_keeps_existing_destination_unchanged(tmp_path):
    probabilities, base = _small_space()
    target = tmp_path / "existing.txt"; target.write_text("previous\n")
    with pytest.raises(InterruptedError, match="se conserva"):
        generate_actions_file(target, [dict(label="A", probabilities=probabilities, base=base,
            rank_start=1, rank_end=9, endings=())], cancelled=lambda: True)
    assert target.read_text() == "previous\n"
    assert list(tmp_path.glob("*.tmp")) == []
