"""Repeated UI refreshes reuse immutable source revisions."""

import hashlib
import json
from dataclasses import asdict

from quiniela_ai_studio.application.services import SystemService
from quiniela_ai_studio.domain.models import Bet
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.storage import Repository


def test_optimized_bet_hash_keeps_the_existing_serialization():
    bets = (Bet("1" * 14, "M0", 3), Bet("X" * 14, "12"))
    from quiniela_ai_studio.domain.models import SystemVersion, utcnow

    system = SystemVersion(
        "hash-test", 1, "DEMO/J01", "Hash", ("1",) * 14, (False,) * 14,
        "M0", bets, utcnow(),
    )
    old_payload = json.dumps([asdict(bet) for bet in bets], sort_keys=True, separators=(",", ":"))
    assert system.hash == hashlib.sha256(old_payload.encode()).hexdigest()


def test_origin_bets_reuses_revision_chain_without_reloading_all_bets(tmp_path, monkeypatch):
    repository = Repository(tmp_path / "studio.sqlite3")
    try:
        round_ = demo_round()
        repository.save_round(round_)
        service = SystemService(repository)
        original_bets = (Bet("1" * 14, "M0"), Bet("X" * 14, "M1", 2))
        original = service.imported(round_, "Origen", original_bets)
        first = service.version(
            original,
            bets=original_bets,
            parameters=json.dumps({"input_revision": original.revision}),
        )
        latest = service.version(
            first,
            bets=(original_bets[0],),
            parameters=json.dumps({"input_revision": first.revision}),
        )

        loads = []
        load = repository.load

        def counted_load(*args, **kwargs):
            loads.append(args)
            return load(*args, **kwargs)

        monkeypatch.setattr(repository, "load", counted_load)
        source, bets = service.origin_bets(latest)
        assert source.revision == original.revision
        assert bets == original_bets
        first_call_count = len(loads)
        assert first_call_count == 2

        assert service.origin_bets(latest) == (source, bets)
        assert len(loads) == first_call_count
    finally:
        repository.close()
