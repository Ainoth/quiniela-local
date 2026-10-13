"""Integración Qt: propuesta, consentimiento de aplicación y preparación manual."""
import json
import threading
from collections import Counter

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog, QMessageBox
from test_pleno_probabilities import with_goals
from test_portfolio import BASE72
from test_ui import wait_for_data

from quiniela_ai_studio.domain.engine import generate
from quiniela_ai_studio.domain.models import Bet
from quiniela_ai_studio.infrastructure.ticket_files import read_ticket_file

pytest_plugins=('test_ui',)


def test_72_proposal_apply_and_audit(window):
    original=window.service.imported(window.round,'Sintético 72',generate(BASE72,'M0'))
    window.set_system(original);window.navigation.setCurrentRow(2)
    window.budget.setValue(5);window.optimize();wait_for_data(window)
    assert window.system==original and window.optimization_result.report['cost_cents']==450
    assert window.optimization_result.report['after']['universe_total']==72
    assert window.optimization_dialog.isVisible()
    window.optimization_dialog.apply_button.click()
    assert window.system.quantity==6 and window.system.cost(window.round)==450
    assert 'minimum_hits' in window.system.parameters
    assert window.repository.load(original.system_id,original.revision)==original
    assert any('optimization_run' in str(row) for row in window.repository.audit())
    assert not window.portfolio_objective.model().item(3).isEnabled()
    events=[(row[1],json.loads(row[3])) for row in window.repository.audit() if row[1] in ('optimization_started','optimization_run')]
    assert {data['status'] for _,data in events}=={'started','completed'}
    assert len({data['run_id'] for _,data in events})==1


def test_tulotero_manual_grouping_and_csv(window,tmp_path,monkeypatch):
    bets=tuple(Bet('1'*13+s,p) for p in ('M0','M1','20') for s in '1X')
    window.set_system(window.service.imported(window.round,'Tres boletos',bets))
    window.open_tulotero()
    dialog=window.tulotero_window
    assert dialog.preview_model.rowCount()==6
    assert {row[0] for row in dialog.preview_model.rows}=={1,2,3}
    path=tmp_path/'manual.csv'
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *args:(str(path),''))
    dialog.export_buttons[2].click()
    assert Counter(read_ticket_file(path))==Counter(bets)
    assert window.system.bets==bets


def test_unrepresentable_tulotero_does_not_change_goals(window):
    bets=(Bet('1'*14,'M0'),Bet('X'*14,'M1'))
    window.open_tulotero(bets)
    dialog=window.tulotero_window
    assert dialog.preview_model.rowCount()==0 and all(not b.isEnabled() for b in dialog.export_buttons)
    dialog.minimum.setValue(1)
    assert dialog.preview_model.rowCount()==2
    assert bets[0].pleno=='M0' and bets[1].pleno=='M1'


def test_manual_pleno_does_not_change_with_slider(window):
    window.repository.save_round(with_goals());window.load_rounds('DEMO/J01');window.new_system()
    assert window.pleno_mode.currentData()=='manual'
    window.toggle_goal(0,'M');window.toggle_goal(1,'2')
    window.coverage.setValue(5);QTest.qWait(250)
    assert window.system.plenos==('M2',)
    window.pleno_mode.setCurrentIndex(1);QTest.qWait(250)
    assert window.system.plenos!=('M2',)


def test_reduction_three_actual_gui_is_verified(window):
    window.navigation.setCurrentRow(7)
    window.reduction_picker.setCurrentIndex(2);QTest.qWait(250)
    window.toggle_goal(0,'M');window.toggle_goal(1,'0')
    window.apply_reduction();wait_for_data(window)
    report=__import__('json').loads(window.system.parameters)['reduction_verification']
    assert window.system.quantity==24
    assert report['universe_total']==216 and report['minimum_hits']==13
    assert 'mínimo 13' in window.footer.text()


def test_cancelled_optimization_is_audited_without_modifying_system(window,monkeypatch):
    from quiniela_ai_studio.domain import engine, portfolio
    entered=threading.Event()
    def cancellable(*args,cancelled,**kwargs):
        entered.set()
        while not cancelled():threading.Event().wait(.005)
        raise engine.Cancelled('Optimización cancelada.')
    monkeypatch.setattr(portfolio,'optimize_portfolio',cancellable)
    original=window.service.imported(window.round,'Cancelación sintética',generate(BASE72,'M0'))
    window.set_system(original);window.optimize()
    for _ in range(200):
        QTest.qWait(5)
        if entered.is_set():break
    assert entered.is_set()
    window.navigation.setCurrentRow(2)
    assert window.portfolio_cancel.isEnabled() and window.portfolio_cancel.isVisible()
    window.portfolio_cancel.click();wait_for_data(window)
    assert not window.portfolio_cancel.isEnabled()
    events=[json.loads(row[3]) for row in window.repository.audit() if row[1]=='optimization_run']
    assert events[0]['status']=='cancelled' and events[0]['input_hash']==original.hash
    assert window.system==original and 'config' in events[0]


def test_failed_optimization_is_audited_without_modifying_system(window,monkeypatch):
    from quiniela_ai_studio.domain import portfolio
    def failing(*args,**kwargs):raise ValueError('Fallo sintético de referencia.')
    monkeypatch.setattr(portfolio,'optimize_portfolio',failing)
    monkeypatch.setattr(QMessageBox,'warning',lambda *args:QMessageBox.StandardButton.Ok)
    original=window.service.imported(window.round,'Fallo sintético',generate(BASE72,'M0'))
    window.set_system(original);window.optimize();wait_for_data(window)
    events=[json.loads(row[3]) for row in window.repository.audit() if row[1]=='optimization_run']
    assert events[0]['status']=='failed' and 'sintético' in events[0]['error']
    assert window.system==original


def test_advanced_parameters_scroll_without_hiding_budget_actions(window):
    window.navigation.setCurrentRow(2)
    window.portfolio_advanced_toggle.setChecked(True);QTest.qWait(50)
    assert window.minimumSizeHint().height()<=768
    assert window.portfolio_advanced.isVisible()
    for button in (window.budget_apply,window.portfolio_cancel):
        assert button.isVisible()
        assert button.mapTo(window,button.rect().bottomRight()).y()<window.height()
    assert window.portfolio_time.isVisible()
