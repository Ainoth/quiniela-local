import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from dataclasses import replace
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog
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


def wait_for_data(window):
    for _ in range(400):
        QTest.qWait(10)
        if not window.data_worker.isRunning():
            QTest.qWait(30)
            return
    raise AssertionError('La tarea de datos no finalizó.')


def test_import_real_folder_preview_and_restart_offline(window,tmp_path,monkeypatch):
    from tests.studio.test_integration import data_folder
    folder=data_folder(tmp_path/'Datosg')
    monkeypatch.setattr(window,'confirm_data',lambda prepared:True)
    monkeypatch.setattr(QFileDialog,'getExistingDirectory',lambda *a:str(folder))
    window.import_win1x2();wait_for_data(window)
    assert window.round.key=='26-27/J12' and window.round.editable
    assert window.system is None
    window.new_system()
    assert window.system.round_key=='26-27/J12'
    assert 'Equipo A' in window.match_labels[0].text()
    selected=window.round.key
    # Reabrir con la selección guardada, sin tocar la fuente ni usar Internet.
    db=window.repository.path
    window.close()
    repo=Repository(db);reopened=MainWindow(repo)
    assert reopened.round.key==selected and reopened.system is not None
    reopened.close()


def test_background_import_discard_preserves_demo(window,tmp_path,monkeypatch):
    from tests.studio.test_integration import data_folder
    folder=data_folder(tmp_path/'Datosg')
    monkeypatch.setattr(window,'confirm_data',lambda prepared:False)
    window.start_data_import(folder=folder);wait_for_data(window)
    assert window.round.key=='DEMO/J01'
    assert window.repository.setting('data_directory') is None
    assert list((tmp_path/'data-cache').iterdir())==[]


def test_live_partial_and_cached_result_respects_quantities(window,monkeypatch):
    from live_results import LiveMatch
    from quiniela_studio.domain import Bet
    round_=replace(window.round,season='26-27',number=12)
    window.repository.save_round(round_);window.load_rounds(round_.key)
    system=window.service.imported(round_,'Directo',(Bet('1'*14,'M0',3),));window.set_system(system)
    matches=[LiveMatch(m.number,m.home,m.away,'—','','','Pendiente',False,0) for m in round_.matches]
    matches[0]=replace(matches[0],score='0 - 1',sign='2',final=True,status='Finalizado')
    matches[1]=replace(matches[1],score='1 - 0',sign='1',status='En juego')
    window.display_live(matches,'2026-10-10T12:00:00+00:00',cached=False)
    window.evaluate_live()
    row=window.eval_model.rows[0]
    assert row[2:]==(3,1,0,13)
    assert 'sin premios' in window.eval_summary.text()
    window.load_rounds('DEMO/J01')
    assert window.live_matches is None and window.live_model.rowCount()==0


def test_filters_and_restore_origin_ui(window):
    window.example_system();wait_for_generation(window)
    original=window.system.bets
    window.filter_group.setChecked(True)
    window.filter_ranges['x_count'][0].setValue(1)
    window.apply_filters()
    assert 0<window.system.quantity<6
    assert all(b.column.count('X')>=1 for b in window.system.bets)
    window.restore_origin()
    assert window.system.bets==original


def test_close_during_background_operation_cancels_without_import(window,tmp_path):
    import threading
    from quiniela_studio.integration import prepare_data
    from tests.studio.test_integration import data_folder
    folder=data_folder(tmp_path/'Datosg')
    prepared=prepare_data(tmp_path/'data-cache',folder=folder)
    release=threading.Event()
    def blocked(cancel,status):
        release.wait(2)
        return prepared
    window.start_background('import',None,blocked)
    window.close()
    assert window.close_pending and window.data_worker.cancel_event.is_set()
    release.set();wait_for_data(window)
    assert not prepared.directory.exists()
    import sqlite3
    with sqlite3.connect(window.repository.path) as db:
        assert db.execute('SELECT COUNT(*) FROM rounds').fetchone()[0]==1


def test_sqlite_pc_copies_in_qt(window,tmp_path,monkeypatch):
    from tests.studio.test_integration import data_folder
    from quiniela_studio.providers import load_win1x2
    from pc_store import SystemStore
    from PySide6.QtWidgets import QMessageBox
    round_=load_win1x2(data_folder(tmp_path/'Datosg'))[-1]
    window.repository.save_round(round_);window.load_rounds(round_.key)
    path=tmp_path/'old.sqlite3';store=SystemStore(path)
    store.create('26-27',12,'Mi anterior',{'picks':['1']*14,'columns':['1'*14,'1'*14],'pleno':'M-0'});store.close()
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**kw:(str(path),''))
    monkeypatch.setattr(QMessageBox,'question',lambda *a:QMessageBox.StandardButton.Yes)
    window.import_pc_systems();wait_for_data(window)
    assert window.system_model.rowCount()==1
    window.system_view.selectRow(0);window.open_selected()
    assert window.system.quantity==2 and window.system.pleno=='M0'
    assert window.system.cost(window.round)==150
