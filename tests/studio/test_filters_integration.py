from itertools import pairwise, product

import pytest

from quiniela_studio.demo import demo_round
from quiniela_studio.domain import Bet
from quiniela_studio.filters import BasicFilters
from quiniela_studio.services import SystemService
from quiniela_studio.storage import Repository


def test_shared_filters_against_exhaustive_reference():
    bets = tuple(Bet("".join(p) + "1" * 8, "M0", 2) for p in product("1X2", repeat=6))
    spec = BasicFilters(
        variants=(2, 4),
        x_count=(1, 2),
        two_count=(1, 2),
        max_x_run=1,
        x_distance=(2, 4),
        reference="1" * 14,
        coincidences=(10, 12),
    )
    expected = []
    for b in bets:
        c = b.column
        positions = [i for i, s in enumerate(c) if s == "X"]
        gaps = [j - i for i, j in pairwise(positions)]
        if (
            2 <= c.count("X") + c.count("2") <= 4
            and 1 <= c.count("X") <= 2
            and 1 <= c.count("2") <= 2
            and "XX" not in c
            and all(2 <= d <= 4 for d in gaps)
            and 10 <= c.count("1") <= 12
        ):
            expected.append(b)
    assert spec.apply(bets) == tuple(expected)
    assert all(b.quantity == 2 and b.pleno == "M0" for b in expected)


def test_filter_versions_restore_initial_origin_and_reject_empty(tmp_path):
    repo = Repository(tmp_path / "studio.sqlite3")
    round_ = demo_round()
    repo.save_round(round_)
    service = SystemService(repo)
    bets = (
        Bet("1" * 14, "00", 3),
        Bet("X" + "1" * 13, "M2", 2),
        Bet("2" + "1" * 13, "M0"),
    )
    system = service.imported(round_, "Prueba", bets)
    filtered = service.filtered(system, BasicFilters(x_count=(1, 14)))
    assert filtered.quantity == 2 and filtered.bets == (bets[1],)
    with pytest.raises(ValueError):
        service.filtered(filtered, BasicFilters(x_count=(2, 14)))
    assert repo.load(system.system_id) == filtered
    optimized = service.optimized(filtered, 75)
    restored = service.restore_origin(optimized)
    assert restored.bets == bets and restored.cost(round_) == 450
    assert repo.load(system.system_id, 1).bets == bets
    repo.close()


@pytest.mark.parametrize(
    "params",
    [
        {"variants": (3, 2)},
        {"x_distance": (0, 13)},
        {"reference": "1X"},
        {"max_x_run": 0},
    ],
)
def test_invalid_filters_rejected(params):
    with pytest.raises(ValueError):
        BasicFilters(**params)
