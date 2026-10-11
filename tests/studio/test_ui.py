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
    window.navigation.setCurrentRow(2);QTest.qWait(10)
    original=window.system.bets
    QTest.mouseClick(window.filter_checks['x_count'],Qt.MouseButton.LeftButton)
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


def test_local_ballot_remains_visible_in_all_sections(window):
    window.new_system()
    for index in range(7):
        window.tabs.setCurrentIndex(index);QTest.qWait(5)
        assert window.sign_buttons[0]['1'].isVisible()
        assert window.goal_buttons[0]['M'].isVisible()
        assert window.pages.currentIndex()==index
    window.tabs.setCurrentIndex(1)
    QTest.mouseClick(window.goal_buttons[0]['M'],Qt.MouseButton.LeftButton)
    QTest.mouseClick(window.goal_buttons[1]['0'],Qt.MouseButton.LeftButton)
    assert window.system.pleno=='M0'
    assert 'fijos' in window.builder_info.text() and '0,75' in window.builder_info.text()


def test_partial_pleno_survives_restart(window,application):
    window.new_system()
    QTest.mouseClick(window.goal_buttons[0]['M'],Qt.MouseButton.LeftButton)
    assert window.pleno_combos[0].currentText()=='M'
    path=window.repository.path;window.close()
    repo=Repository(path);reopened=MainWindow(repo)
    assert reopened.pleno_combos[0].currentText()=='M' and reopened.system.pleno==''
    reopened.pleno_combos[1].setCurrentText('2')
    assert reopened.system.pleno=='M2'
    reopened.close()


def test_direct_export_qt_preserves_system_and_records_audit(window,tmp_path,monkeypatch):
    from quiniela_ai_studio.infrastructure.files import read_system
    window.example_system();wait_for_generation(window)
    original=window.system;path=tmp_path/'direct.json'
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a:(str(path),'JSON (*.json)'))
    window.export_development();wait_for_data(window)
    _,loaded=read_system(path)
    assert loaded.bets==original.bets and window.system==original
    assert any(row[1]=='export_development' for row in window.repository.audit())


def test_filter_activation_is_independent_and_inactive_values_are_ignored(window):
    window.example_system();wait_for_generation(window)
    window.navigation.setCurrentRow(2);QTest.qWait(10)
    original=window.system.bets
    assert not window.filter_ranges['x_count'][0].isEnabled()
    # Click the visible checkbox exactly as a user would.
    QTest.mouseClick(window.filter_checks['x_count'],Qt.MouseButton.LeftButton)
    assert window.filter_checks['x_count'].text().startswith('✓')
    assert window.filter_ranges['x_count'][0].isEnabled()
    window.filter_ranges['x_count'][0].setValue(14)
    QTest.mouseClick(window.filter_checks['x_count'],Qt.MouseButton.LeftButton)
    QTest.mouseClick(window.filter_checks['two_count'],Qt.MouseButton.LeftButton)
    window.filter_ranges['two_count'][1].setValue(0)
    window.filter_reference.setText('INVALIDA')
    window.apply_filters()
    assert window.system.bets==tuple(b for b in original if '2' not in b.column)
    assert window.system.quantity>0
    assert not window.filter_ranges['x_count'][0].isEnabled()
    assert 'pendientes' in window.methods_status.text()
    assert 'pendiente' in window.ai_status.text()


def test_reference_filter_requires_reference_without_creating_revision(window):
    window.example_system();wait_for_generation(window)
    revision=window.system.revision
    window.filter_checks['coincidences'].setChecked(True)
    assert window.filter_reference.isEnabled()
    with pytest.raises(ValueError,match='otra quiniela con 14 signos'):
        window.apply_filters()
    assert window.system.revision==revision
    window.filter_checks['coincidences'].setChecked(False)
    window.apply_filters()
    assert window.system.revision==revision


def test_filter_validation_does_not_block_unchecking(window,application):
    from PySide6.QtCore import QPoint
    window.example_system();wait_for_generation(window)
    window.navigation.setCurrentRow(2);QTest.qWait(10)
    original=window.system
    check=window.filter_checks['coincidences']
    QTest.mouseClick(check,Qt.MouseButton.LeftButton,pos=QPoint(9,check.height()//2))
    assert check.isChecked()
    wait_for_optimization(window);application.processEvents()
    assert QApplication.activeModalWidget() is None
    assert 'otra quiniela con 14 signos' in window.filter_feedback.text()
    assert window.system==original
    QTest.mouseClick(check,Qt.MouseButton.LeftButton,pos=QPoint(9,check.height()//2))
    assert not check.isChecked()
    for control in window.filter_checks.values():control.setChecked(True)
    window.filter_reset.click()
    assert not any(control.isChecked() for control in window.filter_checks.values())
    wait_for_optimization(window)
    assert window.system.bets==original.bets


def test_edit_clears_stale_progress_and_explains_missing_development(window):
    window.example_system();wait_for_generation(window)
    assert window.system.bets and window.progress.value()==100
    QTest.mouseClick(window.sign_buttons[0]['2'],Qt.MouseButton.LeftButton)
    assert not window.system.bets
    assert window.progress.value()==0
    assert window.progress.format()=='Sin desarrollo generado'
    window.filter_checks['x_count'].setChecked(True)
    assert 'Generar' in window.filter_feedback.text()



def test_quick_condition_slider_populates_filters_and_recovers_original_bets(window):
    from quiniela_studio import engine
    window.new_system()
    base=('1X2',)*6+tuple('1X21X21X')
    window.set_system(window.service.edit(window.system,base,(False,)*14,'M1'))
    window.set_system(window.service.generated(window.system,engine.generate(base,'M1')))
    original=window.system
    window.navigation.setCurrentRow(2);QTest.qWait(10)
    assert window.quick_conditions_slider.isVisible()
    window.quick_conditions_slider.setValue(0)
    assert window.system==original
    assert window.coverage.value()==0  # The creation slider is independent.
    assert tuple(control.value() for control in window.filter_ranges['variants'])==(5,8)
    assert tuple(control.value() for control in window.filter_ranges['x_count'])==(2,6)
    assert tuple(control.value() for control in window.filter_ranges['changes'])==(5,10)
    assert window.filter_max_one.value()==4
    assert window.filter_checks['x_count'].isChecked()
    assert not window.filter_checks['coincidences'].isChecked()
    assert not window.filter_checks['x_distance'].isChecked()
    wait_for_optimization(window)
    assert 0<window.system.quantity<original.quantity
    window.quick_conditions_slider.setValue(10)
    assert tuple(control.value() for control in window.filter_ranges['variants'])==(0,14)
    wait_for_optimization(window)
    assert window.system.bets==original.bets
    assert window.system.pleno==original.pleno
    assert window.system.cost(window.round)==original.cost(window.round)


def wait_for_optimization(window):
    for _ in range(600):
        QTest.qWait(10)
        if not window.filter_timer.isActive() and window.filter_job is None:
            QTest.qWait(10)
            return
    raise AssertionError('La optimización no terminó.')


def test_live_optimization_latest_request_empty_recovery_and_budget_last(window):
    from quiniela_studio import engine
    window.new_system();base=('1X2',)*6+tuple('1X21X21X')
    window.set_system(window.service.edit(window.system,base,(False,)*14,'M1'))
    window.set_system(window.service.generated(window.system,engine.generate(base,'M1')))
    original=window.system
    window.navigation.setCurrentRow(2)
    window.coverage.setValue(7)
    window.quick_conditions_slider.setValue(0);window.quick_conditions_slider.setValue(8);window.quick_conditions_slider.setValue(1)
    wait_for_optimization(window)
    from quiniela_ai_studio.domain.filters import quick_conditions
    assert window.system.bets==quick_conditions(1).apply(original.bets)
    assert window.coverage.value()==7
    assert str(window.system.quantity) in window.optimize_info.text()
    assert window.budget_apply.isEnabled()
    assert window.budget_group.mapTo(window,window.budget_group.rect().topLeft()).y()>window.filter_group.mapTo(window,window.filter_group.rect().topLeft()).y()
    window.quick_conditions_slider.setValue(10);wait_for_optimization(window)
    window.filter_checks['x_count'].setChecked(True)
    window.filter_ranges['x_count'][0].setValue(14)
    wait_for_optimization(window)
    assert window.system.quantity==0 and window.system.cost(window.round)==0
    assert not window.budget_apply.isEnabled()
    window.quick_conditions_slider.setValue(0);window.quick_conditions_slider.setValue(10)
    wait_for_optimization(window)
    assert window.system.bets==original.bets
    window.budget.setValue(3);window.budget_apply.click()
    assert window.system.quantity==4 and window.system.cost(window.round)==300
    assert all(bet in original.bets for bet in window.system.bets)


def test_close_cancels_pending_live_optimization(window,application):
    window.example_system();wait_for_generation(window)
    window.quick_conditions_slider.setValue(0)
    window.close();application.processEvents()
    assert not window.filter_timer.isActive()
    assert not window.isVisible()


def test_live_worker_superseded_request_and_close_are_safe(window,monkeypatch,application):
    import threading
    from quiniela_ai_studio.domain.filters import BasicFilters
    from quiniela_ai_studio.domain.engine import Cancelled
    original_apply=BasicFilters.apply;started=threading.Event()
    def slow_apply(spec,bets,cancelled=lambda:False):
        if spec.variants==(5,8):
            started.set()
            while not cancelled():
                threading.Event().wait(0.005)
            raise Cancelled('Cancelado')
        return original_apply(spec,bets,cancelled)
    monkeypatch.setattr(BasicFilters,'apply',slow_apply)
    window.example_system();wait_for_generation(window)
    original=window.system.bets
    window.quick_conditions_slider.setValue(0)
    for _ in range(100):
        QTest.qWait(10)
        if started.is_set():break
    assert started.is_set() and window.filter_job.isRunning()
    window.quick_conditions_slider.setValue(10)
    wait_for_optimization(window)
    assert window.system.bets==original
    started.clear();revision=window.system.revision
    window.quick_conditions_slider.setValue(0)
    for _ in range(100):
        QTest.qWait(10)
        if started.is_set():break
    assert started.is_set()
    window.close()
    for _ in range(100):
        QTest.qWait(10)
        if not window.isVisible():break
    assert not window.isVisible()
    assert window.system.revision==revision
    application.processEvents()


def test_saved_optimization_controls_survive_restart(window):
    window.example_system();wait_for_generation(window)
    window.quick_conditions_slider.setValue(4);wait_for_optimization(window)
    saved=window.system;path=window.repository.path
    window.close()
    repo=Repository(path);reopened=MainWindow(repo)
    assert reopened.quick_conditions_slider.value()==4
    assert reopened.quick_level==4
    assert reopened.system.bets==saved.bets
    assert not reopened.filter_timer.isActive()
    reopened.close()


def test_empty_filtered_result_cannot_export_the_unfiltered_base(window,tmp_path):
    from quiniela_ai_studio.infrastructure.files import write_development
    window.example_system();wait_for_generation(window)
    window.filter_checks['x_count'].setChecked(True)
    window.filter_ranges['x_count'][0].setValue(14);wait_for_optimization(window)
    assert window.system.quantity==0
    path=tmp_path/'previous.txt';path.write_text('anterior')
    with pytest.raises(ValueError,match='No hay apuestas'):
        write_development(path,window.system,window.round)
    assert path.read_text()=='anterior'
