import itertools
import json
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog, QPushButton, QSpinBox, QWidget

from quiniela_ai_studio.domain.models import Bet

pytest_plugins = ('test_ui',)


def test_new_tab_filters_origin_and_persists_group_settings(window):
    bets = tuple(Bet(''.join(prefix) + '1' * 10, 'M0')
                 for prefix in itertools.product('1X', repeat=4))
    system = window.service.imported(window.round, 'Grupos', bets)
    window.set_system(system)
    window.navigation.setCurrentRow(8)
    assert not window.reduction_activation_buttons[9].isChecked()
    window.reduction_activation_buttons[9].setChecked(True)
    window.reduction_tabs.setCurrentIndex(window.reduction_visible_indexes[9])
    assert 9 in window.filter_spec().reduction_tabs_enabled

    group_a = window.advanced_groups[0]
    group_b = window.advanced_groups[1]
    group_a['enabled'].setChecked(True)
    group_b['enabled'].setChecked(True)
    for row in group_a['buttons'][:2]:row[0].setChecked(True)
    for row in group_b['buttons'][2:4]:row[1].setChecked(True)
    group_a['minimum'].setValue(0);group_a['maximum'].setValue(2)
    group_b['minimum'].setValue(0);group_b['maximum'].setValue(2)
    window.advanced_relation_enabled.setChecked(True)
    window.advanced_operation.setCurrentIndex(window.advanced_operation.findData('difference'))
    assert window.advanced_relation_max.maximum() == 14
    window.advanced_relation_min.setValue(0)
    window.advanced_relation_max.setValue(0)
    assert len(window.filter_spec().apply(bets)) == 6
    QTest.qWait(600)

    assert window.system.quantity == 6
    saved = json.loads(window.system.parameters)['filter_spec']['advanced']
    assert [group['name'] for group in saved['groups']] == ['GrupoA', 'GrupoB']
    assert saved['groups'][0]['accepted'] == ['1', '1']
    assert saved['relations'][0]['operation'] == 'difference'
    assert '6 de 16' in window.advanced_feedback.text()

    # La optimización vuelve a leer los filtros avanzados guardados.
    _bets, _base, _config, _round, spec = window.service.optimization_input(window.system, 1000)
    assert spec.advanced.enabled
    window.restore_filter_controls()
    assert window.advanced_groups[0]['enabled'].isChecked()
    assert window.advanced_groups[1]['buttons'][2][1].isChecked()


def test_group_editor_adds_compact_side_by_side_group_cards(window):
    from PySide6.QtWidgets import QTabBar

    assert window.tabs.tabText(1) == 'Reducciones'
    window.tabs.setCurrentIndex(1)
    assert window.navigation.currentRow() == 8
    window.navigation.setCurrentRow(8)
    assert window.reduction_tabs.count() == 5
    assert [window.reduction_tabs.tabText(i) for i in range(5)] == ['Cuenta','SSeguidos','Grupo','FSSeguidos','Interrupciones']
    for reduction_id,tab_index in window.reduction_visible_indexes.items():
        bar=window.reduction_tabs.tabBar()
        assert bar.tabButton(tab_index,QTabBar.ButtonPosition.RightSide) is window.reduction_activation_buttons[reduction_id]
        assert bar.tabButton(tab_index,QTabBar.ButtonPosition.LeftSide) is None
    assert len(window.reduction_tab_pages) == 19  # Las demás pantallas quedan reservadas para fases futuras.
    # Numeric arrows stay read-only; SSeguidos range fields are intentionally editable.
    assert all(field.lineEdit().isReadOnly() for field in window.reduction_tabs.findChildren(QSpinBox))
    assert window.run_minmax_controls['1'][0].isReadOnly() is False
    window.add_advanced_group();window.add_advanced_group();window.add_advanced_group()
    assert len(window.advanced_groups) == 8
    window.reduction_tabs.setCurrentIndex(window.reduction_visible_indexes[9])
    assert window.advanced_group_scroll.widget() is window.advanced_group_canvas
    assert all(len(group['buttons']) == 14 for group in window.advanced_groups)
    assert window.advanced_groups[0]['labels'][0].text() == '01'
    assert 'Equipo local 1' in window.advanced_groups[0]['labels'][0].toolTip()
    assert window.advanced_relation_groups.count() == 28


def test_if_then_tab_filters_and_restores_without_duplicate_controls(window):
    bets=(Bet('1X'+'1'*12,'00'),Bet('X1'+'1'*12,'00'))
    system=window.service.imported(window.round,'Si entonces',bets);window.set_system(system)
    window.navigation.setCurrentRow(8);window.reduction_tabs.setCurrentIndex(window.reduction_visible_indexes[9])
    window.reduction_active[14]=True  # La regla heredada sigue en el modelo, pero su pestaña no está publicada.
    for index,position in enumerate((0,1)):
        group=window.advanced_groups[index];group['enabled'].setChecked(True)
        group['buttons'][position][0].setChecked(True)
        group['minimum'].setValue(0);group['maximum'].setValue(1)
    window.implication_enabled.setChecked(True)
    window.implication_from.setCurrentIndex(window.implication_from.findData('GrupoA'))
    window.implication_to.setCurrentIndex(window.implication_to.findData('GrupoB'))
    window.implication_from_max.setValue(1);window.implication_from_min.setValue(1)
    window.implication_to_max.setValue(1);window.implication_to_min.setValue(1)
    assert window.advanced_spec().implications[0].antecedent == 'GrupoA'
    assert not window.advanced_spec().accepts(bets[0].column)
    for _ in range(100):
        if window.system.bets==(bets[1],) and window.filter_job is None and not window.filter_timer.isActive():
            break
        QTest.qWait(25)
    assert window.system.bets==(bets[1],)
    saved=json.loads(window.system.parameters)['filter_spec']['advanced']['implications']
    assert saved[0]['antecedent']=='GrupoA' and saved[0]['consequent']=='GrupoB'
    window.restore_filter_controls()
    assert window.implication_enabled.isChecked()


def test_references_and_patterns_are_only_graphical_sign_matrices(window):
    window.navigation.setCurrentRow(8)
    assert all(field.lineEdit().isReadOnly() for field in window.reduction_tabs.findChildren(QSpinBox))
    assert not window.run_minmax_controls['1'][0].isReadOnly()
    pattern_enabled,pattern_matrix,_,_=window.pattern_controls[2]
    pattern_enabled.setChecked(True)
    QTest.mouseClick(pattern_matrix.buttons[0][0],Qt.MouseButton.LeftButton)
    QTest.mouseClick(pattern_matrix.buttons[1][1],Qt.MouseButton.LeftButton)
    assert pattern_matrix.column()=='1X'
    window.repeat_enabled.setChecked(True)
    for row in window.repeat_reference.buttons:
        QTest.mouseClick(row[0],Qt.MouseButton.LeftButton)
    window.frequency_matrix.set_column('X'*14)
    window.add_frequency_reference()
    rules={rule.rule_id:rule for rule in window.build_reduction_rules()}
    assert rules['manual-pattern-2'].patterns==('1X',)
    assert rules['manual-repeat'].reference=='1'*14
    assert rules['manual-hit-frequency'].references==('X'*14,)


def test_count_and_streak_mode_grids_apply_and_outer_squares_preserve_settings(window):
    from quiniela_ai_studio.domain.models import Bet
    bets=(Bet('1'*14,'M0'),Bet('X'*14,'M0'))
    system=window.service.imported(window.round,'Cuenta y rachas',bets);window.set_system(system)
    window.navigation.setCurrentRow(8);window.reduction_tabs.setCurrentIndex(0)
    assert all(not button.isChecked() for button in window.reduction_activation_buttons.values())
    window.reduction_activation_buttons[0].setChecked(True)
    assert [window.mode_tabs['Cuenta'].tabText(i) for i in range(3)]==['Manual','Azar','Automática']
    assert [window.mode_tabs['Racha'].tabText(i) for i in range(window.mode_tabs['Racha'].count())]==['Manual','Azar','Automática']
    count_board=window.findChild(QWidget,'countSelectionBoard')
    assert count_board is not None and count_board.parentWidget().objectName()=='countLeftPanel'
    assert count_board.parentWidget().parentWidget().objectName()=='countManualRow'
    assert window.count_squares[('V',14)].text()!=''
    for mode in (1,2,0):
        window.mode_tabs['Cuenta'].setCurrentIndex(mode)
        assert window.mode_tabs['Cuenta'].widget(mode).isAncestorOf(count_board)
        assert window.classic_reduction_canvases[0].width()==(1330 if mode==2 else 750)
        assert window.count_squares[('V',14)].text()!=''
    window.count_apply['V'].setChecked(True)
    QTest.mouseClick(window.count_squares[('V',14)],Qt.MouseButton.LeftButton)
    assert window.count_squares[('V',14)].isChecked()
    assert window.count_values['V']=={14}
    assert any(rule.rule_id=='count-values-V' for rule in window.filter_spec().reduction_rules)
    window.apply_filters()
    assert window.system.bets==(bets[1],)
    square=window.reduction_activation_buttons[0]
    assert square.isChecked() and not square.text()
    square.setChecked(False);window.apply_filters()
    assert window.system.bets==bets
    assert window.count_squares[('V',14)].isChecked()
    square.setChecked(True);window.apply_filters()
    assert window.system.bets==(bets[1],)
    saved=json.loads(window.system.parameters)['filter_spec']
    assert 0 in saved['reduction_tabs_enabled']
    assert any(row['rule_id']=='count-values-V' for row in saved['reduction_rules'])
    window.restore_filter_controls()
    assert window.count_squares[('V',14)].isChecked()


def test_cuenta_dashboard_shows_joint_figures_distribution_seasons_and_distance_filter(window):
    from quiniela_ai_studio.domain.models import Bet

    window.navigation.setCurrentRow(8)
    window.reduction_tabs.setCurrentIndex(window.reduction_visible_indexes[0])
    window.reduction_active[0]=True
    assert window.findChild(QWidget,'countProfilesPanel') is not None
    assert set(window.count_distribution_labels)=={'1','X','2'}
    assert window.history_season_squares['Cuenta']
    assert [window.count_season_table.horizontalHeaderItem(i).text() for i in range(4)]==['1','X','2','Temporadas']
    assert window.count_season_table.rowCount()==len(window.history_season_squares['Cuenta'])
    assert window.findChild(QWidget,'countClassicRightPanel') is not None
    assert window.findChild(QWidget,'countLegacyFilters') is not None
    assert window.count_legacy_sums.rowCount()==10
    assert window.count_legacy_sums.verticalScrollBar().maximum()==0
    assert window.count_legacy_sums.item(0,1).text()==''
    assert window.findChild(QWidget,'countHistogramIcon') is not None
    assert window.findChild(QWidget,'countFiguresActions') is not None
    assert window.count_squares[('V',15)].isEnabled() is False
    assert window.count_squares[('V',15)].text()=='—'
    assert all(button is not None for button in (
        window.findChild(QPushButton,'countMarkAll'),window.findChild(QPushButton,'countInitialize'),
        window.findChild(QPushButton,'countFiguresMarkAll'),window.findChild(QPushButton,'countFiguresInitialize')))
    rows=window._selected_count_history_rows()
    total=sum(int(label.text()) for label,_percent in window.count_distribution_labels.values())
    assert total==14*len(rows)
    season_square=next(iter(window.history_season_squares['Cuenta'].values()))
    excluded_season=next(season for season,square in window.history_season_squares['Cuenta'].items() if square is season_square)
    excluded_rows=sum(row.get('season')==excluded_season for row in rows)
    season_square.setChecked(False)
    assert sum(int(label.text()) for label,_percent in window.count_distribution_labels.values())==14*(len(rows)-excluded_rows)
    season_square.setChecked(True)
    season_row=next(row for row in range(window.count_season_table.rowCount())
                    if window.count_season_table.item(row,3).text()==excluded_season)
    season_item=window.count_season_table.item(season_row,3)
    season_item.setCheckState(Qt.CheckState.Unchecked)
    assert excluded_season not in {season for season,square in window.history_season_squares['Cuenta'].items() if square.isChecked()}
    season_item.setCheckState(Qt.CheckState.Checked)

    candidates=(Bet('X'+'1'*13,'M0'),Bet('2'+'1'*13,'M0'),Bet('XX'+'1'*12,'M0'))
    window.count_profiles_selected={(1,1,0)}
    window.count_profile_active=True
    rules={rule.rule_id:rule for rule in window.build_reduction_rules()}
    assert rules['count-joint-profiles'].allowed_profiles==((1,1,0),)
    assert window.filter_spec().apply(candidates)==(candidates[0],)

    assert window.count_distance_apply is not None and not window.filter_checks['x_distance'].isVisible()
    window.count_distance_apply.setChecked(True)
    minimum,maximum=window.filter_ranges['x_distance']
    minimum.setValue(2);maximum.setValue(2)
    window.count_profiles_selected.clear();window.count_profile_active=False
    window.count_distance_apply.setChecked(True)
    distance_candidates=(Bet('X1X'+'1'*11,'M0'),Bet('X11X'+'1'*10,'M0'))
    assert window.filter_spec().apply(distance_candidates)==(distance_candidates[0],)
    window.reduction_active[0]=False
    assert window.filter_spec().apply(distance_candidates)==distance_candidates


def test_sseguidos_three_modes_compact_panels_filter_and_share_state(window):
    from quiniela_ai_studio.domain.models import Bet
    bets=(Bet('1'*14,'M0'),Bet('1X'*7,'M0'),Bet('XX'+'1'*12,'M0'))
    window.set_system(window.service.imported(window.round,'Signos seguidos',bets))
    window.navigation.setCurrentRow(8)
    assert window.reduction_tabs.tabText(window.reduction_visible_indexes[1])=='SSeguidos'
    assert window.reduction_activation_buttons[1].isChecked() is False
    assert window.mode_tabs['SSeguidos'] is window.mode_tabs['Racha']
    assert [window.mode_tabs['SSeguidos'].tabText(i) for i in range(3)]==['Manual','Azar','Automática']
    assert len(window.run_minmax_controls)==4
    methods=window.mode_tabs['SSeguidos'];board=window.findChild(QWidget,'streakSelectionBoard')
    count_board=window.findChild(QWidget,'countSelectionBoard')
    assert board.parentWidget() is methods.widget(0)
    assert count_board.parentWidget().objectName()=='countLeftPanel'
    assert len(board.findChildren(QWidget,'streakSignPanel'))==4
    assert all(panel.width()==166 for panel in board.findChildren(QWidget,'streakSignPanel'))
    assert board.height()<=600
    assert window.history_season_grids['Racha'].columnCount()==2
    assert window.classic_reduction_canvases[1].decorative is False
    assert window.classic_reduction_canvases[1].width()==960
    methods.setCurrentWidget(window.run_mode_pages['Automática'])
    assert window.classic_reduction_canvases[1].width()==950
    methods.setCurrentWidget(window.run_mode_pages['Manual'])
    assert all(len(window.run_frequency_controls[sign])==13 for sign in ('1','X','2','V'))

    minimum,maximum=window.run_minmax_controls['1']
    minimum.setText('2');maximum.setText('12')
    minimum.editingFinished.emit()
    assert window.run_minmax_values['1']=={'minimum':2,'maximum':12}
    exact_pairs=window.run_count_squares[('1',2,0)]
    exact_pairs.setChecked(True)
    assert window.run_count_values['1'][2]=={0}
    assert all(window.reduction_activation_buttons[index].isChecked() is False
               for index in (0,1,9))
    window.run_apply['1'].setChecked(True)
    assert window.filter_spec().apply(bets)==bets
    window.reduction_activation_buttons[1].setChecked(True)
    spec=window.filter_spec()
    assert spec.apply(bets)==(bets[2],)
    assert any(rule.rule_id=='streak-max-1' and rule.minimum==2 and rule.maximum==12
               and rule.active and rule.tab_index==1 for rule in spec.reduction_rules)
    assert any(rule.rule_id=='streak-count-1-2' and rule.allowed_values==(0,)
               and rule.active for rule in spec.reduction_rules)

    window.apply_filters()
    saved=json.loads(window.system.parameters)['filter_spec']
    assert 1 in saved['reduction_tabs_enabled']
    assert any(row['rule_id']=='streak-max-1' and row['minimum']==2 and row['maximum']==12
               for row in saved['reduction_rules'])
    assert any(row['rule_id']=='streak-count-1-2' and row['allowed_values']==[0]
               for row in saved['reduction_rules'])
    window.restore_filter_controls()
    assert window.run_minmax_controls['1'][0].text()=='2'
    assert window.run_minmax_controls['1'][1].text()=='12'
    assert window.run_count_squares[('1',2,0)].isChecked()
    assert window.reduction_activation_buttons[1].isChecked()


def test_sseguidos_minmax_choices_follow_current_base(window):
    system=window.service.new(window.round,'Base fija de unos')
    window.set_system(system)
    assert window.run_possible_bounds['1']==(14,14)
    assert window.run_possible_bounds['X']==(0,0)
    assert window.run_minmax_controls['1'][0].text()==''
    assert window.run_minmax_controls['1'][1].text()==''
    assert window.run_minmax_controls['X'][0].text()==''
    assert window.run_minmax_controls['X'][1].text()==''
    assert window.run_count_squares[('1',14,1)].isEnabled()
    assert not window.run_count_squares[('1',14,0)].isEnabled()
    assert window.run_count_squares[('1',13,0)].isEnabled()
    assert window.run_minmax_labels['1'][0].text()=='Base 14–14'


def test_sseguidos_empty_bound_remains_empty_after_persistence(window):
    from quiniela_ai_studio.domain.models import Bet
    bets=(Bet('1'*14,'M0'),)
    window.set_system(window.service.imported(window.round,'Límite opcional',bets))
    window.navigation.setCurrentRow(8)
    _minimum,maximum=window.run_minmax_controls['1']
    maximum.setText('14');maximum.editingFinished.emit()
    window.run_apply['1'].setChecked(True)
    rule=next(rule for rule in window.build_reduction_rules() if rule.rule_id=='streak-max-1')
    assert rule.run_minimum_enabled is False and rule.run_maximum_enabled is True
    window.reduction_activation_buttons[1].setChecked(True)
    window.apply_filters()
    window.restore_filter_controls()
    assert window.run_minmax_controls['1'][0].text()==''
    assert window.run_minmax_controls['1'][1].text()=='14'


def test_sseguidos_automatic_keeps_joint_profiles_and_is_not_a_duplicate_filter(window):
    from quiniela_ai_studio.domain.models import Bet
    home='1'*14
    draw='X'*14
    mixed='1'*7+'X'*7
    bets=tuple(Bet(column,'M0') for column in (home,draw,mixed))
    window.set_system(window.service.imported(window.round,'Perfiles conjuntos',bets))
    window.historical_reduction_results=[
        {'season':'2098-2099','round':'1','results14':home,'source':'integrado'},
        {'season':'2098-2099','round':'2','results14':draw,'source':'integrado'},
    ]
    window.refresh_history_seasons()
    risk,summary,_calculate=window.mode_automatic_controls['Racha']
    assert risk.checkedButton().text()=='Mínimo'
    window.calculate_automatic_mode('Racha',('1','X','2','V'),window.run_lengths,{},risk,summary)
    profiles=[rule for rule in window.build_reduction_rules()
              if rule.kind=='allowed_profile' and rule.profile_kind=='streaks']
    assert len(profiles)==1
    assert profiles[0].evidence_seasons==('2098-2099',)
    window.reduction_activation_buttons[1].setChecked(True)
    assert window.filter_spec().apply(bets)==(bets[0],bets[1])
    window.apply_filters()
    window.restore_filter_controls()
    restored=[rule for rule in window.build_reduction_rules()
              if rule.kind=='allowed_profile' and rule.profile_kind=='streaks']
    assert len(restored)==1 and restored[0].allowed_profiles==profiles[0].allowed_profiles
    assert window.run_figure_values['1'][14]=={'14'}
    assert window.run_figure_values['X'][14]=={'14'}
    assert window.mode_tabs['SSeguidos'].tabText(window.mode_tabs['SSeguidos'].currentIndex())=='Automática'


def test_fsseguidos_filters_exact_partition_separately_and_persists(window):
    from quiniela_ai_studio.domain.models import Bet

    expected='X22'+'1'+'XX'+'1'+'2'+'1'+'X'+'1'*4
    rejected='X22X'+'1'+'2X2'+'1'*6
    assert len(expected)==len(rejected)==14
    bets=(Bet(expected,'M0'),Bet(rejected,'M0'))
    window.set_system(window.service.imported(window.round,'Figuras exactas',bets))
    window.navigation.setCurrentRow(8)
    assert [window.mode_tabs['FSSeguidos'].tabText(i) for i in range(3)]==['Manual','Azar','Automática']
    assert all(not square.isChecked() for square in window.reduction_activation_buttons.values())
    assert window.fss_figure_totals['V']==0
    assert window.filter_spec().apply(bets)==bets

    window.fss_total_controls['V'].setValue(7)
    choices=window.fss_figure_lists['V']
    selected=next(choices.item(i) for i in range(choices.count())
                  if choices.item(i).data(Qt.ItemDataRole.UserRole)=='3-2-1-1')
    selected.setSelected(True)
    window.fss_figure_apply['V'].setChecked(True)
    rules=[rule for rule in window.build_reduction_rules() if rule.tab_index==17]
    assert any(rule.sign=='V' and rule.run_length==7 and rule.allowed_figures==('3-2-1-1',)
               and rule.active for rule in rules)
    assert window.filter_spec().apply(bets)==bets  # La pestaña exterior sigue desactivada.

    window.reduction_activation_buttons[17].setChecked(True)
    assert window.filter_spec().apply(bets)==(bets[0],)
    window.apply_filters()
    saved=json.loads(window.system.parameters)['filter_spec']
    assert 17 in saved['reduction_tabs_enabled']
    row=next(row for row in saved['reduction_rules'] if row['rule_id']=='fss-figure-V-7')
    assert row['allowed_figures']==['3-2-1-1'] and row['run_length']==7 and row['active']

    window.restore_filter_controls()
    assert window.reduction_activation_buttons[17].isChecked()
    assert window.fss_total_controls['V'].value()==7
    assert window.fss_figure_apply['V'].isChecked()
    restored=window.fss_figure_lists['V']
    assert any(restored.item(i).data(Qt.ItemDataRole.UserRole)=='3-2-1-1' and restored.item(i).isSelected()
               for i in range(restored.count()))


def test_fsseguidos_automatic_uses_integrated_history_and_azar_repeats_seed(window):
    from quiniela_ai_studio.domain.models import Bet

    columns=('1'*14,'X'*14,'2'*14)
    window.set_system(window.service.imported(window.round,'Histórico de figuras',tuple(Bet(column,'M0') for column in columns)))
    window.historical_reduction_results=[
        {'season':'2097-2098','round':str(index+1),'results14':column,'source':'fixture real'}
        for index,column in enumerate(columns)
    ]
    window.refresh_history_seasons()
    risk,summary,_calculate=window.mode_automatic_controls['FSSeguidos']
    assert risk.checkedButton().text()=='Mínimo'
    window._calculate_automatic_fss_mode(risk,summary)
    assert window.fss_generation_metadata['method']=='automática'
    assert window.fss_generation_metadata['seasons']==('2097-2098',)
    assert all(window.fss_figure_apply[sign].isChecked() for sign in ('1','X','2','V'))
    assert '3 resultados finales' in summary.text()

    random_risk,seed,random_summary=window.mode_azar_controls['FSSeguidos']
    seed.setValue(481);window._calculate_random_fss_mode(random_risk,seed,random_summary)
    first=({sign:{total:set(figures) for total,figures in window.fss_figure_values[sign].items()}
            for sign in ('1','X','2','V')},random_summary.text())
    window._calculate_random_fss_mode(random_risk,seed,random_summary)
    second=({sign:{total:set(figures) for total,figures in window.fss_figure_values[sign].items()}
             for sign in ('1','X','2','V')},random_summary.text())
    assert first==second
    assert 'Semilla 481' in random_summary.text()


def test_interruption_matrix_and_distances_are_separate_active_filters_and_persist(window):
    from quiniela_ai_studio.domain.interruption_statistics import interruption_profile
    from quiniela_ai_studio.domain.models import Bet

    expected='12X22X11221111'
    bits=(1,1,1,0,1,1,0,1,1,0,0,0,0)
    alternate=['1']
    for changed in bits:
        alternate.append(('X' if alternate[-1]=='1' else '1') if changed else alternate[-1])
    alternate=''.join(alternate)
    assert interruption_profile(expected)==(7,3,'3-2-1-1')
    assert interruption_profile(alternate)==(7,3,'3-2-2')
    bets=(Bet(expected,'M0'),Bet(alternate,'M0'))
    window.set_system(window.service.imported(window.round,'Interrupciones',bets))
    window.navigation.setCurrentRow(8)
    assert [window.mode_tabs['Interrupciones'].tabText(i) for i in range(3)]==['Manual','Azar','Automática']
    assert not window.reduction_activation_buttons[18].isChecked()
    assert not window.interruption_apply.isChecked() and not window.distance_apply.isChecked()
    assert window.filter_spec().apply(bets)==bets

    matrix_cell=window.interruption_matrix.buttons[(7,3)]
    assert matrix_cell.isEnabled()
    matrix_cell.setChecked(True);window.interruption_apply.setChecked(True)
    window.reduction_activation_buttons[18].setChecked(True)
    assert window.filter_spec().apply(bets)==bets

    window._reset_interruption_matrix()
    window.interruption_total_buttons[7].setChecked(True)
    figure=window.interruption_figure_buttons[(7,'3-2-1-1')]
    figure.setChecked(True);window.distance_apply.setChecked(True)
    assert window.filter_spec().apply(bets)==(bets[0],)
    assert not window.interruption_apply.isChecked()
    assert window.distance_apply.isChecked()
    assert window.mode_tabs['Interrupciones'].count()==3

    window.apply_filters();QTest.qWait(500)
    saved=json.loads(window.system.parameters)['filter_spec']
    assert 18 in saved['reduction_tabs_enabled']
    assert any(rule['kind']=='allowed_interruption_figure' and rule['allowed_figures']==['3-2-1-1']
               and rule['run_length']==7 and rule['active'] for rule in saved['reduction_rules'])
    window.restore_filter_controls()
    assert window.reduction_activation_buttons[18].isChecked()
    assert window.distance_apply.isChecked() and not window.interruption_apply.isChecked()
    assert window.interruption_total_buttons[7].isChecked()
    assert window.interruption_figure_buttons[(7,'3-2-1-1')].isChecked()


def test_interruption_random_and_automatic_modes_use_reproducible_and_integrated_data(window):
    from quiniela_ai_studio.domain.models import Bet

    columns=('12X22X11221111','11X21221XX121X','1'*14)
    window.set_system(window.service.imported(window.round,'Perfiles de interrupciones',tuple(Bet(column,'M0') for column in columns)))
    window.historical_reduction_results=[
        {'season':'2097-2098','round':str(index+1),'results14':column,'source':'fixture'}
        for index,column in enumerate(columns)
    ]
    window.refresh_history_seasons()
    random_risk,seed,summary=window.mode_azar_controls['Interrupciones']
    assert random_risk.currentText()=='Mínimo'
    seed.setValue(742);window._calculate_random_interruption_mode(random_risk,seed,summary)
    first=(window.interruption_selected_pairs,set(window.interruption_selected_figures))
    window._calculate_random_interruption_mode(random_risk,seed,summary)
    assert first==(window.interruption_selected_pairs,set(window.interruption_selected_figures))
    assert window.interruption_generation_metadata['seed']==742

    auto_risk,auto_summary,_calculate=window.mode_automatic_controls['Interrupciones']
    assert auto_risk.currentText()=='Mínimo'
    window._calculate_automatic_interruption_mode(auto_risk,auto_summary)
    assert window.interruption_generation_metadata['method']=='automática'
    assert window.interruption_generation_metadata['seasons']==('2097-2098',)
    assert '3 resultados finales' in auto_summary.text()


def test_sign_distances_subtab_filters_and_restores_without_changing_figures(window):
    from quiniela_ai_studio.domain.models import Bet

    accepted = Bet('1XX1' + '1' * 10, 'M0')
    rejected = Bet('11X1' + '1' * 10, 'M0')
    bets = (accepted, rejected)
    window.set_system(window.service.imported(window.round, 'Distancias', bets))
    window.navigation.setCurrentRow(8)
    window.reduction_tabs.setCurrentIndex(window.reduction_visible_indexes[18])
    window._show_interruption_subtab(1)
    assert window.interruption_surfaces.currentIndex() == 1
    assert not window.sign_distance_squares[('1', 14)].isEnabled()
    window.sign_distance_squares[('1', 3)].setChecked(True)
    window.sign_distance_apply['1'].setChecked(True)
    assert window.filter_spec().apply(bets) == bets
    window.reduction_activation_buttons[18].setChecked(True)
    assert window.filter_spec().apply(bets) == (accepted,)
    assert not window.distance_apply.isChecked()
    window.apply_filters();QTest.qWait(500)
    saved=json.loads(window.system.parameters)['filter_spec']
    assert any(row['kind']=='allowed_sign_distance' and row['sign']=='1'
               and row['allowed_values']==[3] and row['active']
               for row in saved['reduction_rules'])
    window.restore_filter_controls()
    assert window.sign_distance_squares[('1',3)].isChecked()
    assert window.sign_distance_apply['1'].isChecked()
    window.sign_distance_apply['1'].setChecked(False)
    assert window.filter_spec().apply(bets) == bets
    assert window.sign_distance_squares[('1',3)].isChecked()


def test_automatic_mode_refuses_synthetic_history_and_uses_joint_profiles(window):
    from quiniela_ai_studio.domain.reduction_rules import ReductionRule
    from quiniela_ai_studio.domain.streak_statistics import (
        count_profile,
        frequent_profiles,
    )
    profiles,total=frequent_profiles((count_profile('1X22X'+'1'*9),count_profile('1X22X'+'1'*9)),1)
    assert total==2 and profiles==((4,2,2),)
    automatic=ReductionRule('test-profile','allowed_profile',0,14,profile_kind='counts',allowed_profiles=profiles)
    assert automatic.accepts('1X22X'+'1'*9)
    assert window.tabs.tabText(1)=='Reducciones'


def test_random_mode_is_seeded_and_reports_real_origin_counts(window):
    from quiniela_ai_studio.domain.models import Bet
    bets=(Bet('1'*14,'M0'),Bet('X'*14,'M0'))
    window.set_system(window.service.imported(window.round,'Azar reproducible',bets))
    window.navigation.setCurrentRow(8)
    risk,seed,summary=window.mode_azar_controls['Cuenta'];risk.setCurrentIndex(3);seed.setValue(73)
    args=('Cuenta',('V','X','2'),window.count_values,window.count_squares,risk,seed,summary)
    window.calculate_random_mode(*args);first={key:set(value) for key,value in window.count_values.items()}
    rule_rows=[rule.parameters() for rule in window.build_reduction_rules() if rule.kind=='allowed_count']
    assert rule_rows and all(row['generation_seed']==73 and row['generation_method']=='azar' for row in rule_rows)
    window.calculate_random_mode(*args)
    assert window.count_values==first
    assert 'de 2 apuestas' in summary.text()
    window.apply_filters();window.restore_filter_controls()
    assert window.mode_azar_controls['Cuenta'][1].value()==73
    assert window.mode_azar_controls['Cuenta'][0].currentText()=='Alto'


def test_automatic_mode_imported_final_results_builds_joint_filter(window):
    from quiniela_ai_studio.domain.models import Bet
    bets=(Bet('1'*14,'M0'),Bet('X'*14,'M0'))
    window.set_system(window.service.imported(window.round,'Automática histórica',bets))
    window.historical_reduction_results=[
        {'season':'2024-25','round':'1','results14':'X'*14,'source':'historial.csv'},
        {'season':'2024-25','round':'2','results14':'X'*14,'source':'historial.csv'},
    ]
    window.refresh_history_seasons()
    assert window.count_squares[('V',14)].text()=='2'
    assert window.count_squares[('X',14)].text()=='2'
    assert window.count_squares[('2',0)].text()=='2'
    assert window.count_squares[('V',14)].width()==24
    risk,summary,_calculate=window.mode_automatic_controls['Cuenta'];risk.setCurrentIndex(0)
    window.calculate_automatic_mode('Cuenta',('V','X','2'),window.count_values,window.count_squares,risk,summary)
    window.reduction_activation_buttons[0].setChecked(True)
    spec=window.filter_spec()
    assert spec.apply(bets)==(bets[1],)
    profile=next((rule for rule in spec.reduction_rules if rule.kind=='allowed_profile'),None)
    assert profile is not None
    assert profile.evidence_sample_size==2
    assert profile.evidence_seasons==('2024-25',)
    assert profile.evidence_coverage==1
    window.apply_filters();window.restore_filter_controls()
    assert window.history_season_squares['Cuenta']['2024-25'].isChecked()
    assert window.mode_automatic_controls['Cuenta'][0].currentText()=='Mínimo'


def test_automatic_season_picker_is_compact_and_has_bulk_selection(window):
    window.historical_reduction_results=[
        {'season':'2023-2024','round':'1','results14':'1'*14,'source':'history.csv'},
        {'season':'2024-2025','round':'1','results14':'X'*14,'source':'history.csv'},
        {'season':'2024-2025','round':'2','results14':'2'*14,'source':'history.csv'},
    ]
    window.refresh_history_seasons()
    seasons=window.history_season_squares['Cuenta']
    assert list(seasons)==['2024-2025','2023-2024']
    assert window.history_season_grids['Cuenta'].columnCount()==2
    assert window.history_season_summaries['Cuenta'].text()=='2 temp. · 3 jornadas · 0 con marcador'
    assert window.findChild(QPushButton,'historyImportButton') is not None
    assert all(button.text()!='Importar CSV/JSON' for button in window.reduction_tabs.findChildren(QPushButton))
    window.history_season_select_none['Cuenta'].click()
    assert not any(square.isChecked() for square in seasons.values())
    window.history_season_select_all['Cuenta'].click()
    assert all(square.isChecked() for square in seasons.values())


def test_automatic_import_rejects_synthetic_demo_without_mutating_history(window,monkeypatch):
    fixture=Path(__file__).resolve().parents[2]/'fixtures'/'resultados_demo_v1.json'
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args:(str(fixture),'JSON (*.json)'))
    before=list(window.historical_reduction_results)
    with pytest.raises(ValueError,match='demostración'):
        window.import_reduction_history()
    assert window.historical_reduction_results==before


def test_history_import_preserves_scores_and_rejects_sign_conflicts(window,tmp_path,monkeypatch):
    import csv
    path=tmp_path/'scores.csv'
    fields=['season','round','results14']+[f'score_{i:02}' for i in range(1,16)]
    row={'season':'2099-2100','round':'1','results14':'1'*14,**{f'score_{i:02}':'1-0' for i in range(1,16)}}
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerow(row)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args:(str(path),'CSV (*.csv)'))
    window.import_reduction_history()
    imported=next(item for item in window.historical_reduction_results if item['season']=='2099-2100')
    assert imported['score_01']=='1-0' and imported['score_15']=='1-0'
    row['score_01']='0-1'
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerow(row)
    with pytest.raises(ValueError,match='contradice'):
        window.import_reduction_history()
