from datetime import datetime, timezone

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
        datetime.now(timezone.utc).isoformat(),
    )
    teams = [(match.home, match.away) for match in matches]
    teams[13] = ('AT.MADRID (F)', 'MADRID CFF (F)')

    validate_teams(round_, teams)

    teams[13] = ('AT.MADRID (F)', 'Otro equipo')
    with pytest.raises(ValueError, match='partido 14'):
        validate_teams(round_, teams)
