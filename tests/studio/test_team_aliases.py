from datetime import UTC, datetime

import pytest

from quiniela_ai_studio.domain.models import Match, Round
from quiniela_ai_studio.domain.team_identity import (
    same_fixtures,
    same_team_name,
    same_team_pair,
    uniquely_matches_team,
)
from quiniela_ai_studio.infrastructure.integration import team_key, validate_teams


def test_win1x2_madrid_ccf_typo_matches_quinielista_madrid_cff_name():
    assert team_key('Madrid CCF (F)') == team_key('Madrid CFF (F)')

    matches = tuple(
        Match(index, f'Local {index}', f'Visitante {index}')
        for index in range(1, 14)
    ) + (Match(14, 'At. Madrid (F)', 'Madrid CCF (F)'), Match(15, 'Local 15', 'Visitante 15'))
    round_ = Round(
        '26-27', 14, matches, 'current', 'WIN1X2',
        datetime.now(UTC).isoformat(),
    )
    teams = [(match.home, match.away) for match in matches]
    teams[13] = ('AT.MADRID (F)', 'MADRID CFF (F)')

    validate_teams(round_, teams)

    teams[13] = ('AT.MADRID (F)', 'Otro equipo')
    with pytest.raises(ValueError, match='partido 14'):
        validate_teams(round_, teams)


def test_quinielista_market_names_match_win1x2_aliases_for_champions_round():
    aliases = (
        ('Oporto', 'PSV Eidhoven', 'OPORTO', 'PSV'),
        ('Inter', 'Shaktar Donetsk', 'INTER', 'SHAKHTAR DONETSK'),
        ('R.Madrid', 'Leipzig', 'R.MADRID', 'RB LEIPZIG'),
    )
    for home, away, source_home, source_away in aliases:
        assert team_key(home) == team_key(source_home)
        assert team_key(away) == team_key(source_away)

    matches = tuple(
        Match(index, f'Local {index}', f'Visitante {index}')
        for index in range(1, 16)
    )
    matches = list(matches)
    for number, (home, away, _source_home, _source_away) in zip((1, 9, 11), aliases):
        matches[number - 1] = Match(number, home, away)
    round_ = Round(
        '26-27', 15, tuple(matches), 'current', 'WIN1X2',
        datetime.now(UTC).isoformat(),
    )
    source_teams = [(match.home, match.away) for match in matches]
    for number, (_home, _away, source_home, source_away) in zip((1, 9, 11), aliases):
        source_teams[number - 1] = (source_home, source_away)

    validate_teams(round_, source_teams)


def test_quinielista_ol_lyon_alias_matches_win1x2_lyon():
    assert team_key('OL. LYON') == team_key('Lyon')
    matches = tuple(
        Match(index, f'Local {index}', f'Visitante {index}')
        for index in range(1, 16)
    )
    matches = list(matches)
    matches[11] = Match(12, 'R.Sociedad', 'Lyon')
    round_ = Round(
        '26-27', 19, tuple(matches), 'current', 'WIN1X2', datetime.now(UTC).isoformat(),
    )
    teams = [(match.home, match.away) for match in matches]
    teams[11] = ('R.SOCIEDAD', 'OL. LYON')
    validate_teams(round_, teams)


def test_quinielista_w_marker_matches_feminine_win1x2_team():
    matches = tuple(
        Match(index, f'Local {index}', f'Visitante {index}')
        for index in range(1, 11)
    ) + (
        Match(11, 'Logroño (F)', 'Badalona (F)'),
        Match(12, 'Deportivo (F)', 'Alavés (F)'),
        Match(13, 'Eibar (F)', 'Madrid CCF (F)'),
        Match(14, 'R.Madrid (F)', 'Tenerife (F)'),
        Match(15, 'Local 15', 'Visitante 15'),
    )
    round_ = Round(
        '26-27', 16, matches, 'current', 'WIN1X2', datetime.now(UTC).isoformat(),
    )
    source_teams = [(match.home, match.away) for match in matches]
    source_teams[10] = ('LOGROÑO (F)', 'BADALONA W.(F)')

    validate_teams(round_, source_teams)

    source_teams[10] = ('LOGROÑO (F)', 'BADALONA B (F)')
    with pytest.raises(ValueError, match='partido 11'):
        validate_teams(round_, source_teams)


def test_win1x2_sevilla_typo_does_not_reject_valid_live_round():
    assert team_key('Sevila (F)') == team_key('Sevilla (F)')
    matches = tuple(
        Match(index, f'Local {index}', f'Visitante {index}')
        for index in range(1, 13)
    ) + (
        Match(13, 'Sevila (F)', 'R.Madrid (F)'),
        Match(14, 'Tenerife (F)', 'Ath.Club (F)'),
        Match(15, 'Ath.Club Bilbao', 'R.Sociedad'),
    )
    round_ = Round(
        '26-27', 18, matches, 'current', 'WIN1X2', datetime.now(UTC).isoformat(),
    )
    source_teams = [(match.home, match.away) for match in matches]
    source_teams[12] = ('SEVILLA (F)', 'R.MADRID (F)')

    validate_teams(round_, source_teams)

    source_teams[12] = ('OTRO EQUIPO (F)', 'R.MADRID (F)')
    with pytest.raises(ValueError, match='partido 13'):
        validate_teams(round_, source_teams)


@pytest.mark.parametrize(('left', 'right'), [
    ('Sevila (F)', 'Sevilla (F)'),
    ('PSV Eidhoven', 'PSV Eindhoven'),
    ('R. Madrid', 'Real Madrid'),
    ('Atletico Madrid', 'At. Madrid'),
    ('Athletic Club Bilbao', 'Ath.Club'),
    ('Racing Santander', 'Racing S.'),
    ('Shaktar Donetsk', 'Shakhtar Donetsk'),
    ('Alaves', 'Alavés'),
    ('Badalona W.(F)', 'FC Badalona (F)'),
])
def test_team_identity_accepts_known_spelling_and_format_variants(left, right):
    assert same_team_name(left, right, allow_missing_gender=True)


@pytest.mark.parametrize(('left', 'right'), [
    ('Barcelona', 'Barcelona B'),
    ('Manchester City', 'Manchester United'),
    ('U Craiova', 'FC U Craiova'),
    ('Rayo Vallecano', 'Real Valladolid'),
    ('Athletic Club (F)', 'Athletic Club (M)'),
])
def test_team_identity_keeps_distinct_clubs_and_competitions_separate(left, right):
    assert not same_team_name(left, right, allow_missing_gender=True)


def test_team_identity_preserves_home_away_order():
    assert not same_team_pair(('Sevilla', 'Rayo'), ('Rayo', 'Sevilla'))
    assert same_fixtures([('Sevilla', 'Rayo')], [('Sevila', 'Rayo')])
    assert not same_fixtures([('Sevilla', 'Rayo')], [('Rayo', 'Sevilla')])


def test_typo_must_resolve_to_one_team_in_the_round():
    assert uniquely_matches_team('Malaga', 'Malag', ['Malaga', 'Rayo'])
    assert not uniquely_matches_team('Malaga', 'Malag', ['Malaga', 'Malage'])
