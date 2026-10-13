"""Exports preserve the chosen system rather than rebuilding its base ballot."""
import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from dataclasses import replace

import pytest
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog

from quiniela_ai_studio.domain.models import Bet
from quiniela_ai_studio.domain.reductions import plan_reduction, reduced_bets
from quiniela_ai_studio.infrastructure.demo import demo_round
from quiniela_ai_studio.infrastructure.files import read_system, read_txt
from quiniela_ai_studio.infrastructure.storage import Repository
from quiniela_ai_studio.ui.window import MainWindow


@pytest.fixture
def window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    repository = Repository(tmp_path / 'studio.sqlite3')
    repository.save_round(demo_round())
    window = MainWindow(repository)
    monkeypatch.setattr(window, 'show_export_result', lambda *args: None)
    window.show()
    app.processEvents()
    yield window
    window.close()
    app.processEvents()


def select_system(window, system):
    row = next(i for i, saved in enumerate(window.listed_systems)
               if saved.system_id == system.system_id)
    window.system_view.selectRow(row)


def test_mis_sistemas_exports_selected_row_without_opening_it(window, tmp_path, monkeypatch):
    selected = window.service.imported(window.round, 'Fila elegida',
                                       (Bet('1' * 14, '01', 3), Bet('X' * 14, 'M2')))
    opened = window.service.imported(window.round, 'Otra abierta', (Bet('2' * 14, '00'),))
    window.set_system(opened)
    window.navigation.setCurrentRow(5)
    select_system(window, selected)
    path = tmp_path / 'fila.txt'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (str(path), ''))
    window.selected_txt_button.click()
    assert read_txt(path) == selected.bets
    assert len(path.read_text().splitlines()) == 4
    assert window.system == opened
    assert any(row[1] == 'export_txt' for row in window.repository.audit())
    path = tmp_path / 'fila.json'
    window.selected_json_button.click()
    assert read_system(path)[1] == selected
    assert window.system == opened


def test_visible_global_save_keeps_reduced_bets_and_frozen_price(window, tmp_path, monkeypatch):
    source = window.service.new(window.round)
    source = window.service.edit(source, ('1X2',) * 4 + ('1',) * 10,
                                 (False,) * 14, '', pleno_choices=('01', '2'))
    plan = plan_reduction(source.base, source.plenos, 1, (0, 1, 2, 3))
    reduced = window.service.reduced_copy(source, plan, reduced_bets(plan))
    window.set_system(reduced)
    window.repository.change_rules(replace(window.round, price_cents=100))
    window.refresh()
    result = []
    monkeypatch.setattr(window, 'show_export_result', lambda *args: result.append(args))
    path = tmp_path / 'reducida'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (str(path), ''))
    for index in (2, 5, 7):
        window.navigation.setCurrentRow(index)
        assert window.export_button.isVisible() and window.export_button.isEnabled()
    window.navigation.setCurrentRow(1)
    assert window.system.system_id == source.system_id
    assert not window.export_button.isEnabled()  # Normal has its own ungenerated base.
    window.navigation.setCurrentRow(7)
    assert window.system == reduced and window.export_button.isEnabled()
    window.export_button.click()
    path = path.with_suffix('.txt')
    assert len(path.read_text().splitlines()) == 18
    assert read_txt(path) == reduced.bets
    assert result[0][2].price_cents == 75 and result[0][3] == 18
    assert window.repository.setting('export_directory') == str(tmp_path)
    assert window.system == reduced


def test_save_cancel_keeps_data_and_does_not_show_success(window, tmp_path, monkeypatch):
    system = window.service.imported(window.round, 'Mi quiniela', (Bet('1' * 14, 'M1'),))
    window.set_system(system)
    before = window.repository.audit()
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: ('', ''))
    monkeypatch.setattr(window, 'show_export_result', lambda *args: pytest.fail('Guardado cancelado'))
    window.export_button.click()
    assert window.repository.audit() == before and window.system == system
    assert not tuple(tmp_path.glob('*.txt'))


def test_direct_txt_export_reports_written_count_without_changing_draft(window, tmp_path, monkeypatch):
    draft = window.service.new(window.round)
    draft = window.service.edit(draft, ('1X', '1X2') + ('1',) * 12, (False,) * 14, 'M1')
    window.set_system(draft)
    path = tmp_path / 'combinaciones.txt'
    result = []
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (str(path), 'TXT (*.txt)'))
    monkeypatch.setattr(window, 'show_export_result', lambda *args: result.append(args))
    window.export_development()
    for _ in range(200):
        QTest.qWait(10)
        if not window.data_worker.isRunning():
            QTest.qWait(20)
            break
    assert len(path.read_text().splitlines()) == 6
    assert result[0][3] == 6 and result[0][1].bets == ()
    assert window.system == draft


def test_save_is_blocked_while_latest_filter_is_pending(window, tmp_path, monkeypatch):
    system = window.service.imported(window.round, 'Origen',
                                     (Bet('1' * 14, '01'), Bet('X' * 14, '01')))
    window.set_system(system)
    window.configure_quick_conditions(10)
    assert window.filter_timer.isActive() and not window.export_button.isEnabled()
    assert not window.full_export_button.isEnabled()
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: pytest.fail('Filtro pendiente'))
    with pytest.raises(ValueError, match='termine el cálculo'):
        window.export_txt()
    with pytest.raises(ValueError, match='termine el cálculo'):
        window.export_development()
    with pytest.raises(ValueError, match='termine el cálculo'):
        window.export_json()
    for _ in range(100):
        QTest.qWait(10)
        if not window.filter_timer.isActive() and window.filter_job is None:
            break
    assert window.export_button.isEnabled()
