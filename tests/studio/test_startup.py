"""Elección de sesión: continuar, nueva actual y fallos offline sin perder apuestas."""
from dataclasses import replace
from datetime import date, timedelta

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from test_integration import data_folder
from test_ui import wait_for_data, wait_for_generation

from quiniela_ai_studio.domain.models import Bet
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.integration import prepare_data
from quiniela_ai_studio.infrastructure.storage import Repository
from quiniela_ai_studio.ui.window import MainWindow

pytest_plugins = ('test_ui',)


def real_round(number, mode):
    today = date.today().isoformat()
    return replace(demo_round(), season='26-27', number=number, mode=mode,
                   nominal_date=today, editable_until=(date.today()+timedelta(days=1)).isoformat())


def previous_system(window):
    old = real_round(11, 'past')
    window.repository.save_round(old)
    system = window.service.imported(old, 'La anterior', (Bet('X'*14, 'M1', 2),))
    window.load_rounds(old.key)
    window.set_system(system)
    return system


def test_yes_in_real_spanish_dialog_restores_once_without_new_versions(window):
    window.example_system();wait_for_generation(window)
    original = window.system
    seen = []
    def accept():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QMessageBox)
        assert original.name in dialog.text()
        assert original.round_key in dialog.text()
        assert dialog.button(QMessageBox.StandardButton.Yes).text() == 'Sí, continuar'
        seen.append(dialog.text())
        dialog.button(QMessageBox.StandardButton.Yes).click()
    QTimer.singleShot(0, accept)
    window.start_session()
    window.start_session()
    assert len(seen) == 1
    assert window.system == original
    assert len(window.repository.systems()) == 1
    assert window.repository.load(original.system_id).hash == original.hash


def test_no_creates_new_current_without_overwriting_saved_systems(window):
    old = previous_system(window)
    current = real_round(12, 'current')
    window.repository.save_round(current)
    existing = window.service.new(current, 'Actual ya guardada')
    def decline():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QMessageBox)
        assert dialog.button(QMessageBox.StandardButton.No).text() == 'No, empezar una nueva'
        dialog.button(QMessageBox.StandardButton.No).click()
    QTimer.singleShot(0, decline)
    window.start_session()
    assert window.round.key == current.key
    assert window.system.system_id not in (old.system_id, existing.system_id)
    assert window.system.quantity == 0 and not window.system.plenos
    assert window.system_mode(window.system) == 'normal'
    assert window.navigation.currentRow() == 1
    assert window.repository.load(old.system_id).hash == old.hash
    assert window.repository.load(existing.system_id).hash == existing.hash
    assert window.repository.setting('last_open_system') == window.system.system_id


def test_restart_resumes_actual_last_reduced_even_when_normal_exists(window, monkeypatch, application):
    window.example_system();wait_for_generation(window)
    normal = window.system
    reduced = window.service.new(window.round, 'La reducida que dejé abierta', mode='reduced')
    window.set_system(reduced)
    path = window.repository.path
    window.close()
    reopened = MainWindow(Repository(path))
    try:
        # Construir la pantalla no debe sustituir la referencia de sesión guardada.
        assert reopened.repository.setting('last_open_system') == reduced.system_id
        asked = []
        def accept(previous):
            asked.append(previous)
            return True
        monkeypatch.setattr(reopened, 'ask_resume', accept)
        reopened.start_session()
        assert asked == [reduced]
        assert reopened.system == reduced
        assert reopened.navigation.currentRow() == 7
        assert len(reopened.repository.systems()) == 2
        assert reopened.repository.load(normal.system_id).hash == normal.hash
    finally:
        reopened.close();application.processEvents()


def test_no_downloads_missing_current_then_creates_fresh_ballot(window, monkeypatch, tmp_path):
    old = previous_system(window)
    folder = data_folder(tmp_path/'Datosg')
    monkeypatch.setattr(window, 'ask_resume', lambda previous: False)
    monkeypatch.setattr('quiniela_ai_studio.ui.window.prepare_data',
                        lambda cache, cancelled, progress, **options: prepare_data(cache, folder=folder, cancelled=cancelled, progress=progress))
    monkeypatch.setattr(window, 'confirm_data', lambda prepared: (_ for _ in ()).throw(AssertionError('La sesión nueva ya está elegida.')))
    window.start_session()
    wait_for_data(window)
    assert window.round.key == '26-27/J12' and window.round.editable
    assert window.system.round_key == window.round.key
    assert window.system.system_id != old.system_id and window.system.quantity == 0
    assert window.repository.load(old.system_id).hash == old.hash
    assert not window._startup_new_pending


def test_download_failure_keeps_old_saved_without_opening_or_inventing_current(window, monkeypatch):
    old = previous_system(window)
    before = len(window.repository.systems())
    monkeypatch.setattr(window, 'ask_resume', lambda previous: False)
    def offline(*args, **kwargs):
        raise OSError('No hay conexión para descargar la jornada actual.')
    monkeypatch.setattr('quiniela_ai_studio.ui.window.prepare_data', offline)
    errors = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda parent, title, message: errors.append(message))
    window.start_session();wait_for_data(window)
    assert window.system is None
    assert len(window.repository.systems()) == before
    assert window.repository.load(old.system_id).hash == old.hash
    assert not window._startup_new_pending
    assert errors and 'conexión' in errors[0]


def test_first_offline_demo_profile_has_no_resume_question(window, monkeypatch):
    def unexpected(previous):
        raise AssertionError('No hay una quiniela anterior que continuar.')
    monkeypatch.setattr(window, 'ask_resume', unexpected)
    window.start_session()
    assert window.round.mode == 'simulation'
    assert window.system.quantity == 0
    assert window.navigation.currentRow() == 1
