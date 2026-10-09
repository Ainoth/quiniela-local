import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from dataclasses import replace
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QFileDialog
from quiniela_studio.demo import demo_round
from quiniela_studio.storage import Repository
from quiniela_studio.ui import MainWindow, STYLE


@pytest.fixture(scope='session')
def application():
    app=QApplication.instance() or QApplication([])
    app.setStyle('Fusion');app.setStyleSheet(STYLE)
    yield app


@pytest.fixture
def window(application,tmp_path):
    repo=Repository(tmp_path/'studio.sqlite3');repo.save_round(demo_round())
    window=MainWindow(repo);window.resize(1024,768);window.show();application.processEvents()
    yield window
    window.close();application.processEvents()


def wait_for_generation(window):
    for _ in range(300):
        QTest.qWait(10)
        if not window.worker.isRunning():
            QTest.qWait(20)
            return
    raise AssertionError('La generación no finalizó.')


def test_T15_six_columns_real_gui_flow(window,tmp_path,monkeypatch):
    window.example_system();wait_for_generation(window)
    assert window.system.quantity==6
    assert window.system.cost(window.round)==450
    window.budget.setValue(1.5);window.optimize()
    assert window.system.quantity==2 and window.system.revision==4
    window.result_input.setText('1'*14);window.evaluate()
    assert window.eval_model.rowCount()==2
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a:(str(tmp_path/'bets.txt'),''))
    window.export_txt();assert len((tmp_path/'bets.txt').read_text().splitlines())==2
    # Tablas virtualizadas: un refresco idéntico mantiene índice y selección.
    window.system_view.selectRow(0);index=window.system_view.currentIndex()
    window.refresh();assert window.system_view.currentIndex()==index
    window.navigation.setCurrentRow(1);QTest.qWait(10)
    assert window.generate_button.isVisible()
    assert window.generate_button.mapTo(window,window.generate_button.rect().topLeft()).y()<window.height()


def test_round_switch_clears_active_and_results(window):
    window.example_system();wait_for_generation(window)
    other=replace(window.round,number=2,mode='past');window.repository.save_round(other)
    window.result_input.setText('1'*14)
    window.load_rounds(other.key)
    assert window.system is None and window.result_input.text()=='-'*14
    assert not window.generate_button.isEnabled()
    window.load_rounds('DEMO/J01')
    assert window.system.quantity==6


def test_locks_and_template_ui(window):
    window.new_system()
    QTest.mouseClick(window.lock_buttons[0],Qt.MouseButton.LeftButton)
    assert window.system.locks[0] and not window.sign_buttons[0]['1'].isEnabled()
    original=window.system.base[0]
    window.coverage.setValue(10);window.apply_template()
    assert window.system.base[0]==original and window.system.locks[0]


def test_seven_pages_and_geometry(window):
    for index in range(7):
        window.navigation.setCurrentRow(index);QTest.qWait(5)
        assert window.pages.currentIndex()==index
        assert window.pages.widget(index).isVisible()
    assert window.footer.isVisible()
