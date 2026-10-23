"""Fuentes verificables y descarga explícita sin confundir mercado y público."""
import json
from dataclasses import replace

import pytest
from test_integration import data_folder, load_win1x2, xml

import data_updater
from quiniela_ai_studio.infrastructure.integration import (
    fetch_round_sources,
    probability_snapshots,
    team_key,
)

pytest_plugins = ('test_ui',)


def market_xml():
    return xml().replace(b'p_jugados_1="50"', b'p_bf_1desc="20" p_bf_Xdesc="30" p_bf_2desc="50" p_jugados_1="50"')


def test_market_and_popularity_are_distinct(tmp_path):
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    updated = probability_snapshots(round_, market_xml())
    assert updated.snapshot('sport').values[0] == (.2, .3, .5)
    assert updated.snapshot('public').values[0] == (.5, .3, .2)
    assert 'mercado' in updated.snapshot('sport').source
    assert round_.snapshot('sport') is None


@pytest.mark.parametrize('payload', [
    market_xml().replace(b'p_bf_1desc="20"', b'p_bf_1desc="nan"'),
    market_xml().replace(b'p_bf_1desc="20"', b'p_bf_1desc="-20"'),
    market_xml().replace(b'p_bf_1desc="20"', b'p_bf_1desc="80"'),
    market_xml().replace(b'p_bf_Xdesc="30"', b'', 1),
    market_xml().replace(b'jornada="12"', b'jornada="13"'),
    market_xml().replace(b'Equipo A', b'Otro equipo', 1),
])
def test_invalid_market_or_identity_rejected(tmp_path, payload):
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    with pytest.raises(ValueError):
        probability_snapshots(round_, payload)


def test_no_market_is_not_invented(tmp_path):
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    assert probability_snapshots(round_, xml()).snapshot('sport') is None


def test_explicit_aliases_do_not_match_other_clubs():
    for local, remote in [('Manch. United', 'MAN.UNITED'), ('Bayern Munich', 'B.MUNICH'),
                          ('Bor. Dortmund', 'B.DORTMUND'), ('Manchest. City', 'MAN.CITY'),
                          ('CSU Craiova', 'U. CRAIOVA')]:
        assert team_key(local) == team_key(remote)
    assert team_key('FC U Craiova') != team_key('U. Craiova')
    assert team_key('Manchester United') != team_key('Manchester City')


def test_missing_source_cannot_apply_template(window, tmp_path):
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    window.new_system()
    original = window.system
    with pytest.raises(ValueError, match='no tiene porcentajes'):
        window.apply_template()
    assert window.system == original
    assert 'Sin porcentajes' in window.source_status.text()


def test_network_failure_preserves_system(window, tmp_path, monkeypatch):
    from test_ui import wait_for_data

    from quiniela_ai_studio.ui import window as ui
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    window.new_system()
    original = window.system
    def fail(*args, **kwargs):
        raise OSError('Fuente temporalmente no disponible')
    monkeypatch.setattr(ui, 'fetch_round_sources', fail)
    monkeypatch.setattr(ui.QMessageBox, 'warning', lambda *args: None)
    window.refresh_system_sources()
    wait_for_data(window)
    assert window.system == original
    assert 'no disponible' in window.data_message.text()


def test_exact_round_download_and_cache_preservation(tmp_path, monkeypatch):
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    urls = []
    def download(url):
        urls.append(url)
        return market_xml()
    monkeypatch.setattr(data_updater, '_download', download)
    cache = tmp_path / 'cache'
    updated = fetch_round_sources(round_, cache)
    assert urls == [data_updater.QUINIELISTA_PERCENTAGES.format(round_no=12)]
    assert updated.snapshot('sport')
    path = cache / 'porcentajes_26-27_J12.xml'
    before = path.read_bytes()
    monkeypatch.setattr(data_updater, '_download', lambda url: market_xml().replace(b'jornada="12"', b'jornada="11"'))
    with pytest.raises(ValueError):
        fetch_round_sources(round_, cache)
    assert path.read_bytes() == before


def test_historical_round_does_not_download_current_season_percentages(tmp_path, monkeypatch):
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    historical = replace(round_, mode='past')
    monkeypatch.setattr(
        data_updater, '_download',
        lambda _url: pytest.fail('No debe pedir porcentajes sin filtro de temporada.'),
    )

    with pytest.raises(ValueError, match='solo publica porcentajes para la jornada en curso'):
        fetch_round_sources(historical, tmp_path / 'cache')


def test_download_adopts_sources_without_changing_bets(window, tmp_path, monkeypatch):
    from test_ui import wait_for_data

    from quiniela_ai_studio.domain.models import Bet
    from quiniela_ai_studio.ui import window as ui
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    original = window.service.imported(round_, 'Real', (Bet('X' * 14, 'M2', 2),))
    window.set_system(original)
    monkeypatch.setattr(ui, 'fetch_round_sources', lambda *args, **kwargs: probability_snapshots(round_, market_xml()))
    window.refresh_system_sources()
    wait_for_data(window)
    assert window.system.bets == original.bets
    assert window.system.cost(round_) == original.cost(round_)
    assert window.repository.load(original.system_id, 1) == original
    assert json.loads(window.system.round_snapshot)['snapshots'][1]['kind'] == 'sport'
    assert 'mercado' in window.source_status.text()


def test_changed_system_does_not_adopt_download(window, tmp_path, monkeypatch):
    from quiniela_ai_studio.domain.models import Bet
    from quiniela_ai_studio.infrastructure.integration import probability_snapshots
    round_ = load_win1x2(data_folder(tmp_path / 'source'))[-1]
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    source = window.service.imported(round_, 'Real', (Bet('1' * 14, '00'),))
    window.set_system(source)
    window.data_kind = 'sources'
    window.data_context = source
    from types import SimpleNamespace
    window.data_worker = SimpleNamespace(cancel_event=SimpleNamespace(is_set=lambda: False), isRunning=lambda: False)
    window.set_system(window.service.duplicate(source))
    window.background_done(probability_snapshots(round_, market_xml()))
    assert window.frozen_round().snapshot('sport') is None
    window.data_worker = None
