from datetime import UTC, datetime

import pytest

from quiniela_ai_studio.domain.models import Match, Round
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
