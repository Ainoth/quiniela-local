import json

from quiniela_ai_studio.domain.models import Match
from quiniela_ai_studio.infrastructure.espn_live import (
    SOURCE_NAME,
    fetch_espn_live_scores,
    parse_espn_scoreboard,
)


def event(home, away, home_score, away_score, state, status_name, *, completed=False,
          date="2026-10-17T12:00:00Z"):
    status = {
        "type": {
            "state": state,
            "name": status_name,
            "completed": completed,
            "description": status_name,
            "shortDetail": "FT" if completed else "",
        }
    }
    return {
        "date": date,
        "competitions": [{
            "status": status,
            "competitors": [
                {"homeAway": "home", "score": str(home_score), "team": {"displayName": home}},
                {"homeAway": "away", "score": str(away_score), "team": {"displayName": away}},
            ],
        }],
    }


def payload(*events):
    return json.dumps({"events": list(events)}).encode()


def test_espn_parser_does_not_treat_scheduled_zero_scores_as_results():
    rows = parse_espn_scoreboard(
        payload(event("Getafe", "Rayo Vallecano", 0, 0, "pre", "STATUS_SCHEDULED",
                      date="2026-10-19T19:00:00Z")),
        "esp.1", "20261019",
    )
    assert len(rows) == 1
    assert (rows[0]["score"], rows[0]["sign"], rows[0]["pleno"], rows[0]["final"]) == (
        "—", "", "", False,
    )
    assert rows[0]["status"] == "Sin comenzar"


def test_espn_parser_calculates_sign_and_pleno_only_from_reported_scores():
    rows = parse_espn_scoreboard(
        payload(event("Espanyol", "Atlético Madrid", 0, 4, "post", "STATUS_FULL_TIME", completed=True)),
        "esp.1", "20261017",
    )
    assert (rows[0]["score"], rows[0]["sign"], rows[0]["pleno"], rows[0]["final"]) == (
        "0 - 4", "2", "0M", True,
    )


def test_espn_fallback_matches_fixture_order_gender_and_team_aliases(monkeypatch):
    fixtures = (
        Match(1, "Espanyol", "At. Madrid", "17/10/202614:00"),
        Match(2, "Ath.Club (F)", "Valencia (F)", "17/10/202616:30"),
        Match(3, "Getafe", "Rayo", "19/10/202621:00"),
    )

    def fake_scoreboard(day, league):
        if league == "esp.1":
            return parse_espn_scoreboard(payload(
                event("Espanyol", "Atlético Madrid", 0, 1, "post", "STATUS_FULL_TIME", completed=True),
                event("Getafe", "Rayo Vallecano", 0, 0, "pre", "STATUS_SCHEDULED",
                      date="2026-10-19T19:00:00Z"),
            ), league, day)
        if league == "esp.w.1":
            return parse_espn_scoreboard(payload(
                event("Athletic Club", "Valencia", 1, 0, "post", "STATUS_FULL_TIME", completed=True),
            ), league, day)
        return []

    monkeypatch.setattr("quiniela_ai_studio.infrastructure.espn_live._fetch_scoreboard", fake_scoreboard)
    matches = fetch_espn_live_scores(fixtures)
    assert len(matches) == 3
    assert [(m.number, m.sign, m.final) for m in matches] == [(1, "2", True), (2, "1", True), (3, "", False)]
    assert matches[0].source == SOURCE_NAME
    assert matches[2].score == "—" and matches[2].status == "Sin comenzar"


def test_espn_fallback_marks_uncovered_fixtures_without_fabricating_scores(monkeypatch):
    fixture = Match(1, "Equipo desconocido", "Otro equipo", "17/10/202614:00")
    monkeypatch.setattr("quiniela_ai_studio.infrastructure.espn_live._fetch_scoreboard", lambda *_: [])
    match = fetch_espn_live_scores((fixture,))[0]
    assert (match.score, match.sign, match.status, match.source) == (
        "—", "", "Sin cobertura de ESPN", SOURCE_NAME,
    )


def test_round_adapter_uses_espn_when_primary_marker_is_unreachable(monkeypatch):
    from dataclasses import replace

    import quiniela_ai_studio.infrastructure.integration as integration
    import quiniela_ai_studio.infrastructure.espn_live as espn_live
    from quiniela_studio.demo import demo_round
    from live_results import LiveMatch

    round_ = replace(demo_round(), season="26-27", number=14, mode="current")
    monkeypatch.setattr(integration, "fetch_live_results", lambda *_: (_ for _ in ()).throw(ConnectionError("offline")))
    monkeypatch.setattr(espn_live, "fetch_espn_live_scores", lambda fixtures: tuple(
        LiveMatch(match.number, match.home, match.away, "—", "", "", "Sin cobertura de ESPN", False, 0, SOURCE_NAME)
        for match in fixtures
    ))

    matches = integration.live_for_round(round_)
    assert len(matches) == 15
    assert all(match.source == SOURCE_NAME for match in matches)


def test_round_adapter_enriches_stale_primary_rows_after_kickoff(monkeypatch):
    from dataclasses import replace

    import quiniela_ai_studio.infrastructure.integration as integration
    import quiniela_ai_studio.infrastructure.espn_live as espn_live
    from quiniela_studio.demo import demo_round
    from live_results import LiveMatch

    base = demo_round()
    fixtures = tuple(replace(match, kickoff="01/01/2000 12:00") for match in base.matches)
    round_ = replace(base, season="26-27", number=14, mode="current", matches=fixtures)
    primary = tuple(
        LiveMatch(match.number, match.home, match.away, "—", "", "", "Sin resultado", False, 0)
        for match in fixtures
    )
    alternate = tuple(
        LiveMatch(
            match.number, match.home, match.away,
            "1 - 0" if match.number == 1 else "—",
            "1" if match.number == 1 else "",
            "10" if match.number == 1 else "",
            "Finalizado" if match.number == 1 else "Sin cobertura de ESPN",
            match.number == 1, 1, SOURCE_NAME,
        )
        for match in fixtures
    )
    monkeypatch.setattr(integration, "fetch_live_results", lambda *_: primary)
    monkeypatch.setattr(espn_live, "fetch_espn_live_scores", lambda _: alternate)

    matches = integration.live_for_round(round_)

    assert matches[0].score == "1 - 0"
    assert matches[0].source == SOURCE_NAME
    assert matches[1] == primary[1]
