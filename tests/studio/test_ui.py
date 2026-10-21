import os

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from dataclasses import replace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QBoxLayout, QFileDialog

from quiniela_studio.demo import demo_round
from quiniela_studio.storage import Repository
from quiniela_studio.ui import STYLE, MainWindow


@pytest.fixture(scope='session')
def application():
    app=QApplication.instance() or QApplication([])
    app.setStyle('Fusion');app.setStyleSheet(STYLE)
    yield app


@pytest.fixture
def window(application,tmp_path,monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    unexpected=[]
    monkeypatch.setattr(QMessageBox,'warning',lambda parent,title,message:(unexpected.append(str(message)),QMessageBox.StandardButton.Ok)[1])
    repo=Repository(tmp_path/'studio.sqlite3');repo.save_round(demo_round())
    window=MainWindow(repo);window.resize(1024,768);window.show();application.processEvents()
    yield window
    window.close();application.processEvents()
    assert not unexpected, 'Avisos inesperados: '+repr(unexpected)


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
    window.budget.setValue(1.5);window.optimize();wait_for_data(window)
    assert window.system.quantity==6  # Propuesta aún no aplicada.
    window.optimization_dialog.apply_button.click()
    assert window.system.quantity==2 and window.system.revision==4
    window.result_input.setText('1'*14);window.evaluate()
    assert window.eval_model.rowCount()==2
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a:(str(tmp_path/'bets.txt'),''))
    monkeypatch.setattr(window,'show_export_result',lambda *a:None)
    window.export_txt();assert len((tmp_path/'bets.txt').read_text().splitlines())==2
    # Tablas virtualizadas: un refresco idéntico mantiene índice y selección.
    window.system_view.selectRow(0);index=window.system_view.currentIndex()
    window.refresh();assert window.system_view.currentIndex()==index
    window.navigation.setCurrentRow(1);QTest.qWait(10)
    assert window.generate_button.isVisible()
    assert window.generate_button.mapTo(window,window.generate_button.rect().topLeft()).y()<window.height()


def test_open_saved_coverage_reduction_from_mis_sistemas(window):
    """A saved Hermes report has its verifier nested under ``coverage``."""
    from quiniela_ai_studio.domain.coverage_reducer import (
        CoverageReductionConfig,
        reduce_coverage,
    )
    from quiniela_ai_studio.domain.models import Bet

    bets=(Bet('1'*14,'M0'),Bet('X'+'1'*13,'M0'))
    source=window.service.imported(window.round,'Origen',bets)
    result=reduce_coverage(
        bets,source.base,CoverageReductionConfig(14,150,75,'hermes',scenario_limit=20)
    )
    saved=window.service.coverage_copy(source,result.bets,result.report)
    window.navigation.setCurrentRow(5)
    window.update_system_list()
    row=next(i for i,system in enumerate(window.listed_systems)
             if system.system_id==saved.system_id)
    window.system_view.selectRow(row)
    window.open_selected()
    assert window.system.system_id==saved.system_id
    assert 'cobertura exacta, mínimo 14' in window.footer.text()


def test_coverage_footer_handles_previous_and_incomplete_schemas():
    from quiniela_ai_studio.ui.window import coverage_footer

    assert 'cobertura exacta, mínimo 13' in coverage_footer(
        {'status':'exacta','minimum_hits':13}
    )
    assert 'cobertura estimada por muestreo, mínimo NO VERIFICADO' in coverage_footer(
        {'coverage':{'status':'estimada por muestreo','minimum_hits':None}}
    )
    assert coverage_footer({'method':'Hermes'})==' · cobertura aún no verificada'


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
    window.normal_generator.triples.setValue(4);window.normal_generator.doubles.setValue(6);window.apply_template()
    assert window.system.base[0]==original and window.system.locks[0]


def test_seven_pages_and_geometry(window):
    for index in range(7):
        window.navigation.setCurrentRow(index);QTest.qWait(5)
        assert window.pages.currentIndex()==index
        assert window.pages.widget(index).isVisible()
    assert window.footer.isVisible()


def wait_for_data(window):
    for _ in range(2000):
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
    assert row[2:]==(3,1,1,12,13,'Pendiente')
    assert 'sin premios' in window.eval_summary.text()
    assert not window.prize_card.isVisible()
    window.load_rounds('DEMO/J01')
    assert window.live_matches is None and window.live_model.rowCount()==15
    assert all(row[5]!='Esperando marcador' for row in window.live_model.rows)


def test_cached_scrutiny_shows_prize_breakdown_and_clears_on_round_change(window,tmp_path,application):
    from quiniela_ai_studio.domain.models import Bet
    from quiniela_ai_studio.infrastructure.providers import load_win1x2
    from tests.studio.test_integration import data_folder

    folder=data_folder(tmp_path/'premios')
    historical=load_win1x2(folder)[0]
    window.repository.save_round(historical)
    window.load_rounds(historical.key)
    window.repository.set_setting('data_directory',str(folder))
    bets=(Bet('1'*14,'00',2),Bet('2'+'1'*13,'00',3))
    winning_system=window.service.imported(historical,'Premiada',bets)
    window.set_system(winning_system)
    window.auto_live.setChecked(False)
    window.navigation.setCurrentRow(4)
    application.processEvents()

    assert window.prize_card.isVisible()
    assert window.prize_layout.direction()==QBoxLayout.Direction.TopToBottom
    assert window.prize_total.text()=='14,00 €'
    assert window.prize_category_rows[15][1].text()=='2'
    assert window.prize_category_rows[14][3].text()=='4,00 €'
    assert window.prize_category_rows[13][3].text()=='6,00 €'
    assert window.prize_detail_card.isVisible()
    assert window.prize_detail_rows[15][1].text()=='1'
    assert window.prize_detail_rows[14][2].text()=='2,00 €'
    assert window.prize_detail_rows[14][3].text()=='2'
    assert window.prize_detail_total.text()=='14,00 €'
    assert window.live_model.rows[0][5]=='Escrutinio publicado'
    assert 'boleto validado' in window.prize_fine_print.text()

    from live_results import LiveMatch
    incomplete=[LiveMatch(m.number,m.home,m.away,'—','','','Pendiente',False,0) for m in historical.matches]
    window.display_live(incomplete,'2026-10-20T12:00:00+00:00',cached=False)
    assert window.prize_card.isVisible()
    assert window.live_model.rows[0][5]=='Escrutinio publicado'

    window.set_system(window.service.imported(historical,'Sin aciertos',(Bet('2'*14,'00'),)))
    assert not window.prize_card.isVisible()
    window.set_system(winning_system)
    assert window.prize_card.isVisible()

    window.repository.set_setting('data_directory',None)
    window.evaluate_live()
    assert not window.prize_card.isVisible()
    window.repository.set_setting('data_directory',str(folder))
    assert window.show_cached_scrutiny()
    assert window.prize_card.isVisible()
    window.read_cached_scrutiny()
    assert window.manual_mode.isChecked()
    assert window.prize_total.text()=='14,00 €'
    window.manual_mode.setChecked(False)
    assert window.prize_card.isVisible()

    window.load_rounds('DEMO/J01')
    assert not window.prize_card.isVisible()
    assert not window.prize_detail_card.isVisible()


def test_switching_system_in_mis_sistemas_clears_previous_prize_before_aciertos(window,tmp_path,application):
    from quiniela_ai_studio.domain.models import Bet
    from quiniela_ai_studio.infrastructure.providers import load_win1x2
    from tests.studio.test_integration import data_folder

    folder=data_folder(tmp_path/'cambio_sistema_premios')
    round_=load_win1x2(folder)[0]
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    window.repository.set_setting('data_directory',str(folder))
    assert window.tabs.tabText(4)=='Escrutinio'
    assert window.navigation.item(4).text()=='Escrutinio'
    winner=window.service.imported(round_,'Premiada',(Bet('1'*14,'00'),))
    loser=window.service.imported(round_,'Sin aciertos',(Bet('2'*14,'00'),))
    window.set_system(winner)
    window.auto_live.setChecked(False)
    window.navigation.setCurrentRow(4);application.processEvents()
    assert window.prize_card.isVisible()
    assert window.prize_detail_card.isVisible()

    window.navigation.setCurrentRow(5)
    window.set_system(loser)
    assert not window.prize_card.isVisible()
    assert not window.prize_detail_card.isVisible()
    window.navigation.setCurrentRow(4);application.processEvents()
    assert not window.prize_card.isVisible()
    assert window.prize_detail_card.isVisible()
    assert window.prize_detail_total.text()=='0,00 €'


def test_published_scrutiny_with_no_award_stays_neutral(window,tmp_path,application):
    from quiniela_ai_studio.domain.models import Bet
    from quiniela_ai_studio.infrastructure.providers import load_win1x2
    from tests.studio.test_integration import data_folder

    folder=data_folder(tmp_path/'sin_premio')
    historical=load_win1x2(folder)[0]
    window.repository.save_round(historical)
    window.load_rounds(historical.key)
    window.repository.set_setting('data_directory',str(folder))
    window.set_system(window.service.imported(historical,'Sin premio',(Bet('2'*14,'00'),)))
    window.auto_live.setChecked(False)
    window.navigation.setCurrentRow(4)
    application.processEvents()

    assert not window.prize_card.isVisible()
    assert 'sin premios' in window.prize_notice.text()
    assert window.eval_model.rowCount()==1


def test_published_page_cache_displays_real_j14_prize_when_pre_is_provisional(window, application):
    from quiniela_ai_studio.domain.models import Bet
    from quiniela_ai_studio.infrastructure.published_scrutiny import (
        parse_published_scrutiny,
    )
    from tests.studio.test_published_scrutiny import reference_page, reference_round

    round_ = reference_round()
    scrutiny = parse_published_scrutiny(reference_page(), round_)
    window.repository.save_round(round_)
    window.load_rounds(round_.key)
    window.repository.set_setting('published_scrutiny:'+round_.key, {
        'fixture':[[match.home_id,match.away_id] for match in round_.matches],
        'nominal_date':round_.nominal_date,'scrutiny':scrutiny})
    bet = Bet('111'+scrutiny['result'][3:], '11')
    window.set_system(window.service.imported(round_,'Premio de J14',(bet,)))
    window.auto_live.setChecked(False)
    window.navigation.setCurrentRow(4)
    application.processEvents()

    assert window.prize_card.isVisible()
    assert window.prize_total.text() == '2,22 €'
    assert window.prize_detail_card.isVisible()
    assert window.prize_category_rows[11][1].text() == '1'
    assert window.prize_detail_rows[11][2].text() == '2,22 €'
    assert window.prize_detail_rows[11][3].text() == '1'
    assert window.prize_detail_rows[11][4].text() == '2,22 €'
    assert window.prize_detail_rows[10][2].text() == '0,00 €'
    assert window.prize_detail_total.text() == '2,22 €'
    assert 'Comprobar Lotería' in window.prize_fine_print.text()
    assert window.eval_model.rows[0][3] == 11


def test_cached_scrutiny_with_wrong_teams_never_announces_a_prize(window,tmp_path,application):
    from quiniela_ai_studio.domain.models import Bet
    from quiniela_ai_studio.infrastructure.providers import load_win1x2
    from tests.studio.test_integration import data_folder

    folder=data_folder(tmp_path/'equipos_distintos')
    historical=load_win1x2(folder)[0]
    wrong=replace(historical,matches=(replace(historical.matches[0],home_id='otro:ZZZ'),)+historical.matches[1:])
    window.repository.save_round(wrong)
    window.load_rounds(wrong.key)
    window.repository.set_setting('data_directory',str(folder))
    window.set_system(window.service.imported(wrong,'PRE no coincidente',(Bet('1'*14,'00'),)))
    window.auto_live.setChecked(False)
    window.navigation.setCurrentRow(4)
    application.processEvents()

    assert not window.prize_card.isVisible()
    assert 'equipos' in window.prize_notice.text()


def test_waiting_marker_uses_schedule_without_claiming_unknown_result(window):
    from datetime import UTC, datetime

    now=datetime(2026,10,17,18,30,tzinfo=UTC)
    assert window.waiting_marker_status('2026-10-17T16:00:00+00:00',now).startswith('Sin resultado · horario 17/10 ')
    assert window.waiting_marker_status('2026-10-18T16:00:00+00:00',now).startswith('Por comenzar · 18/10 ')
    assert window.waiting_marker_status('',now)=='Sin datos del marcador'


def test_live_error_does_not_describe_all_fixtures_as_pending(window):
    window.live_error(window.frozen_round(),'No se pudo conectar con el marcador público: sin conexión')
    assert 'No se ha recibido ningún resultado' in window.live_status.text()
    assert 'pendiente' not in window.live_status.text().casefold()


def test_filters_and_restore_origin_ui(window):
    window.example_system();wait_for_generation(window)
    window.navigation.setCurrentRow(8);QTest.qWait(10)
    original=window.system.bets
    window.reduction_activation_buttons[0].setChecked(True)
    window.count_apply['X'].setChecked(True)
    for value in range(1,15):window.count_squares[('X',value)].setChecked(True)
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
    from PySide6.QtWidgets import QMessageBox

    from pc_store import SystemStore
    from quiniela_studio.providers import load_win1x2
    from tests.studio.test_integration import data_folder
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
    for index in range(len(window.TAB_ORDER)):
        window.tabs.setCurrentIndex(index);QTest.qWait(5)
        assert window.sign_buttons[0]['1'].isVisible()
        assert window.goal_buttons[0]['M'].isVisible()
        expected=window.SECTIONS.index(window.TAB_ORDER[index])
        assert window.pages.currentIndex()==expected
    window.tabs.setCurrentIndex(1)
    QTest.mouseClick(window.goal_buttons[0]['M'],Qt.MouseButton.LeftButton)
    QTest.mouseClick(window.goal_buttons[1]['0'],Qt.MouseButton.LeftButton)
    assert window.system.pleno=='M0'
    assert 'fijos' in window.builder_info.text() and '6,75' in window.builder_info.text()


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
    window.navigation.setCurrentRow(8);QTest.qWait(10)
    original=window.system.bets
    window.reduction_activation_buttons[0].setChecked(True)
    # The graphical square applies the exact count; the outer square can
    # suspend the whole set while preserving its values.
    window.count_apply['2'].setChecked(True)
    window.count_squares[('2',0)].setChecked(True)
    window.filter_reference.set_column('')
    window.apply_filters()
    assert window.system.bets==tuple(b for b in original if '2' not in b.column)
    assert window.system.quantity>0
    active=window.reduction_activation_buttons[0]
    active.setChecked(False)
    assert not active.text() and not active.isChecked()
    window.apply_filters()
    assert window.system.bets==original
    assert window.count_squares[('2',0)].isChecked()
    active.setChecked(True);window.apply_filters()
    assert window.system.bets==tuple(b for b in original if '2' not in b.column)
    assert 'garantía combinatoria' in window.methods_status.text()
    assert 'pendiente' in window.ai_status.text()


def test_hidden_reference_filter_is_not_applied_while_its_tab_is_unpublished(window):
    window.example_system();wait_for_generation(window)
    revision=window.system.revision
    window.filter_checks['coincidences'].setChecked(True)
    assert window.filter_reference.isEnabled()
    # Coincidencias sigue reservada para una futura pestaña, no se aplica oculta.
    assert 8 not in window.filter_spec().reduction_tabs_enabled
    bets=window.system.bets
    window.apply_filters()
    assert window.system.bets==bets
    window.filter_checks['coincidences'].setChecked(False)
    window.apply_filters()
    assert window.system.revision==revision


def test_filter_validation_does_not_block_unchecking(window,application):
    from PySide6.QtCore import QPoint
    window.example_system();wait_for_generation(window)
    window.navigation.setCurrentRow(8);QTest.qWait(10)
    window.reduction_activation_buttons[0].setChecked(True)
    original=window.system
    check=window.filter_checks['coincidences']
    QTest.mouseClick(check,Qt.MouseButton.LeftButton,pos=QPoint(9,check.height()//2))
    assert check.isChecked()
    wait_for_optimization(window);application.processEvents()
    assert QApplication.activeModalWidget() is None
    assert window.filter_feedback.text() in ('','No se ha aplicado ninguna condición.')
    assert window.system.bets==original.bets
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
    window.reduction_activation_buttons[0].setChecked(True)
    assert window.quick_conditions_slider.isVisible()
    window.quick_conditions_slider.setValue(0)
    assert window.system==original
    assert (window.normal_generator.triples.value(),window.normal_generator.doubles.value())==(0,0)
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
    window.reduction_activation_buttons[0].setChecked(True)
    normal_counts=(window.normal_generator.triples.value(),window.normal_generator.doubles.value())
    window.quick_conditions_slider.setValue(0);window.quick_conditions_slider.setValue(8);window.quick_conditions_slider.setValue(1)
    wait_for_optimization(window)
    from quiniela_ai_studio.domain.filters import quick_conditions
    assert window.system.bets==quick_conditions(1).apply(original.bets)
    assert (window.normal_generator.triples.value(),window.normal_generator.doubles.value())==normal_counts
    assert str(window.system.quantity) in window.optimize_info.text()
    assert window.budget_apply.isEnabled()
    assert window.budget_group.mapTo(window,window.budget_group.rect().topLeft()).y()>window.filter_group.mapTo(window,window.filter_group.rect().topLeft()).y()
    window.quick_conditions_slider.setValue(10);wait_for_optimization(window)
    window.count_apply['X'].setChecked(True)
    window.count_squares[('X',14)].setChecked(True)
    wait_for_optimization(window)
    assert window.system.quantity==0 and window.system.cost(window.round)==0
    assert not window.budget_apply.isEnabled()
    window.quick_conditions_slider.setValue(0);window.quick_conditions_slider.setValue(10)
    wait_for_optimization(window)
    assert window.system.bets==original.bets
    window.budget.setValue(3);window.budget_apply.click()
    wait_for_data(window);window.optimization_dialog.apply_button.click()
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

    from quiniela_ai_studio.domain.engine import Cancelled
    from quiniela_ai_studio.domain.filters import BasicFilters
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
    started.clear()
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
    assert window.system.bets==original
    application.processEvents()


def test_saved_optimization_controls_survive_restart(window):
    window.example_system();wait_for_generation(window)
    window.quick_conditions_slider.setValue(4);wait_for_optimization(window)
    saved=window.system;path=window.repository.path
    window.close()
    repo=Repository(path);reopened=MainWindow(repo)
    assert reopened.quick_conditions_slider.value()==4
    assert reopened.quick_level==4, (saved.parameters,reopened.system.parameters,reopened.quick_level)
    assert reopened.system.bets==saved.bets
    assert not reopened.filter_timer.isActive()
    reopened.close()


def test_empty_filtered_result_cannot_export_the_unfiltered_base(window,tmp_path):
    from quiniela_ai_studio.infrastructure.files import write_development
    window.example_system();wait_for_generation(window)
    window.reduction_activation_buttons[0].setChecked(True)
    window.count_apply['X'].setChecked(True)
    for value in range(15):window.count_squares[('X',value)].setChecked(value==14)
    wait_for_optimization(window)
    assert window.system.quantity==0
    path=tmp_path/'previous.txt';path.write_text('anterior')
    with pytest.raises(ValueError,match='No hay apuestas'):
        write_development(path,window.system,window.round)
    assert path.read_text()=='anterior'


def wait_for_live(window):
    for _ in range(300):
        QTest.qWait(10)
        if window.live_worker is None:return
    raise AssertionError('El marcador no terminó.')


def test_multiple_pleno_buttons_and_optional_reduction_copy(window):
    from quiniela_studio import engine
    window.new_system()
    window.set_system(window.service.edit(window.system,('1X2',)*4+('1',)*10,(False,)*14,''))
    for side,goals in ((0,'01'),(1,'2M')):
        for goal in goals:QTest.mouseClick(window.goal_buttons[side][goal],Qt.MouseButton.LeftButton)
    assert window.system.plenos==('02','0M','12','1M')
    window.start_generation();wait_for_generation(window)
    original=window.system
    assert original.quantity==324 and original.cost(window.round)==24300
    window.navigation.setCurrentRow(7)
    assert not window.reduction_apply.isEnabled()
    assert window.system.system_id!=original.system_id
    for side,goals in ((0,'01'),(1,'2M')):
        for goal in goals:QTest.mouseClick(window.goal_buttons[side][goal],Qt.MouseButton.LeftButton)
    assert window.reduction_apply.isEnabled()
    window.reduction_apply.click();wait_for_data(window)
    assert window.system.system_id!=original.system_id
    assert window.system.quantity==36 and window.system.cost(window.round)==2700
    assert window.repository.load(original.system_id).bets==original.bets
    assert set(window.system.plenos)==set(original.plenos)
    assert engine.size(window.system.base)==81


def test_automatic_marker_refresh_updates_hits_misses_and_pleno(window,monkeypatch):
    from live_results import LiveMatch
    from quiniela_studio import ui
    from quiniela_studio.domain import Bet
    round_=replace(window.round,season='26-27',number=12)
    window.repository.save_round(round_);window.load_rounds(round_.key)
    system=window.service.imported(round_,'Seguimiento',(Bet('1'*14,'01'),Bet('1'*13+'X','01')));window.set_system(system)
    counter=0
    preferred_sources=[]
    def provider(context, preferred_source=''):
        nonlocal counter
        counter+=1
        preferred_sources.append(preferred_source)
        matches=[LiveMatch(m.number,m.home,m.away,'1 - 0','1','10','Finalizado',True,0,'ESPN (alternativa)') for m in context.matches]
        matches[14]=replace(matches[14],score='0 - 1',sign='2',pleno='01',final=counter>=2,status='Finalizado' if counter>=2 else 'En juego')
        return tuple(matches)
    monkeypatch.setattr(ui,'live_for_round',provider)
    window.navigation.setCurrentRow(4);wait_for_live(window)
    assert counter==1
    assert window.live_model.rowCount()==15
    assert window.eval_model.rows[0][3:7]==(14,0,0,14)
    assert window.eval_model.rows[0][7]=='Goles coinciden (en juego)'
    window.live_timer.setInterval(30)
    for _ in range(100):
        QTest.qWait(10)
        if counter>=2 and window.live_worker is None:break
    window.live_timer.stop()
    assert counter>=2
    assert preferred_sources[:2]==['','ESPN (alternativa)']
    assert window.eval_model.rows[0][7]=='Pleno acertado'
    assert window.eval_model.rows[1][7]=='Goles sí; faltan 14'
    assert window.repository.setting('live:'+round_.key)['matches'][14]['pleno']=='01'
    cached=window.repository.setting('live:'+round_.key)
    monkeypatch.setattr(ui,'live_for_round',lambda context,preferred_source='':(_ for _ in ()).throw(OSError('Sin red')))
    window.fetch_live();wait_for_live(window)
    assert window.repository.setting('live:'+round_.key)==cached
    assert window.eval_model.rows[0][7]=='Pleno acertado'
    assert 'Se conserva el marcador guardado' in window.live_status.text()
    assert QApplication.activeModalWidget() is None
    window.navigation.setCurrentRow(0)
    assert not window.live_timer.isActive()


def test_manual_results_selector_updates_without_check_button(window):
    window.example_system();wait_for_generation(window)
    window.navigation.setCurrentRow(4);window.manual_mode.setChecked(True)
    for combo in window.manual_signs:combo.setCurrentText('1')
    window.manual_goals[0].setCurrentText('M');window.manual_goals[1].setCurrentText('1')
    window.final_check.setChecked(True)
    QTest.qWait(180)
    assert window.eval_model.rowCount()==6
    assert any(row[3]==14 and row[7]=='Pleno acertado' for row in window.eval_model.rows)
    assert not window.live_timer.isActive()


def test_live_bad_identity_and_close_do_not_corrupt_cache(window,monkeypatch,application):
    import threading

    from live_results import LiveMatch
    from quiniela_studio import ui
    round_=replace(window.round,season='26-27',number=12)
    window.repository.save_round(round_);window.load_rounds(round_.key)
    def matches(context):
        return tuple(LiveMatch(m.number,m.home,m.away,'—','','','Pendiente',False,0) for m in context.matches)
    monkeypatch.setattr(ui,'live_for_round',lambda context,preferred_source='':tuple(replace(m,home='Equipo incorrecto') for m in matches(context)))
    window.navigation.setCurrentRow(4);wait_for_live(window)
    assert window.repository.setting('live:'+round_.key) is None
    assert QApplication.activeModalWidget() is None
    started=threading.Event();release=threading.Event()
    def slow_provider(context,preferred_source=''):
        started.set();release.wait(2);return matches(context)
    monkeypatch.setattr(ui,'live_for_round',slow_provider)
    window.fetch_live()
    for _ in range(100):
        QTest.qWait(10)
        if started.is_set():break
    assert started.is_set()
    path=window.repository.path;window.close();release.set()
    for _ in range(100):
        QTest.qWait(10)
        if not window.isVisible():break
    assert not window.isVisible() and not window.live_timer.isActive()
    repo=Repository(path);assert repo.setting('live:'+round_.key) is None;repo.close()
    application.processEvents()


def test_live_refresh_keeps_selected_bet_and_shows_pleno_in_header(window):
    from live_results import LiveMatch
    from quiniela_studio.domain import Bet
    window.set_system(window.service.imported(window.round,'Comparación',(Bet('1'*14,'01'),Bet('X'*14,'02'))))
    matches=[LiveMatch(m.number,m.home,m.away,'1 - 0','1','10','Finalizado',True,0) for m in window.round.matches]
    matches[14]=replace(matches[14],score='0 - 2',sign='2',pleno='02')
    window.display_live(matches,'2026-10-12T10:00:00+00:00',False)
    window.eval_view.setCurrentIndex(window.eval_model.index(1,0))
    assert window.live_model.rows[0][3]=='X'
    matches=[replace(m,score='0 - 0',sign='X') if m.number<15 else m for m in matches]
    window.display_live(matches,'2026-10-12T10:01:00+00:00',False)
    selected=window.eval_view.currentIndex().row()
    assert window.eval_model.rows[selected][:2]==('X'*14,'02')
    assert window.live_model.rows[0][4]=='Acierto'
    assert '0 - 2' in window.live_pleno_summary.text()
