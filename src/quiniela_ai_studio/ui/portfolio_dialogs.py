"""Propuestas y preparación manual: no envía apuestas ni realiza pagos."""
import json
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from quiniela_ai_studio.domain.models import round_from_dict
from quiniela_ai_studio.domain.tickets import ChannelRules, group_tickets
from quiniela_ai_studio.infrastructure.files import atomic_text, write_txt
from quiniela_ai_studio.infrastructure.ticket_files import (
    write_ticket_file,
)


def pct(value):return 'No disponible' if value is None else f'{value:.2%}'


def result_dialog(parent,result,source):
    round_=round_from_dict(json.loads(source.round_snapshot))
    report=result.report;after=report['after']
    dialog=QDialog(parent);dialog.setWindowTitle('Propuesta de optimización · revisa antes de aplicar');dialog.resize(880,650)
    layout=QVBoxLayout(dialog)
    summary=QLabel(f'{report["candidates"]} candidatas → {report["selected"]} apuestas · {report["cost_cents"]/100:.2f} € · remanente {report["remaining_cents"]/100:.2f} €\n{report["algorithm"]} · {report["optimality"]}\nUniverso: {after["universe_total"]} · {after["universe"]} · cobertura {after["status"]}\nGarantía mínima: {after["minimum_hits"] if after["minimum_hits"] is not None else "NO VERIFICADA"} dentro del universo. No garantiza premios económicos.');summary.setWordWrap(True);layout.addWidget(summary)
    warnings=QLabel('\n'.join(report['warnings']) or 'Plenos conservados. La propuesta todavía NO se ha aplicado.');warnings.setWordWrap(True);layout.addWidget(warnings)
    tabs=QTabWidget();layout.addWidget(tabs,1)
    coverage_page=QWidget();coverage_layout=QVBoxLayout(coverage_page);tabs.addTab(coverage_page,'Cobertura')
    _,model=parent.table(('Aciertos','Uniforme','Ponderada','Antes uniforme','Antes ponderada'),coverage_layout)
    model.update_rows([(k+'+' if k!='14' else k,pct(after['uniform'][k]),pct((after['weighted'] or {}).get(k)),pct(report['before']['uniform'][k]),pct((report['before']['weighted'] or {}).get(k))) for k in ('14','13','12','11','10')])
    info=QLabel(f'Masa exacta estimada: {pct(after["probability_mass"])} · {report["probability_model"]}\nDistancia media: {after["mean_distance"]:.3f} · escenarios {after["scenarios"]} · tamaño efectivo ponderado {after["effective_samples"]}\nValor esperado: no disponible; no se convierte popularidad en ROI.');info.setWordWrap(True);coverage_layout.addWidget(info)
    comparisons=QWidget();cl=QVBoxLayout(comparisons);tabs.addTab(comparisons,'Comparar mismo presupuesto')
    _,cm=parent.table(('Selección','Coste','13+ ponderado/uniforme','12+ ponderado/uniforme','Masa exacta','Distancia','Canal válido'),cl)
    rows=[]
    for name,metrics in [('Optimizada',after),*report['comparisons'].items()]:
        rows.append((name,f'{metrics.get("cost_cents",report["cost_cents"])/100:.2f} €',pct((metrics['weighted'] or metrics['uniform'])['13']),pct((metrics['weighted'] or metrics['uniform'])['12']),pct(metrics['probability_mass']),f'{metrics["mean_distance"]:.3f}',str(metrics.get('channel_feasible',True))))
    cm.update_rows(rows)
    note=QLabel('Antes de filtrar se compara el universo completo; las alternativas de esta tabla usan igual número de apuestas y modelo. «Anterior recortada» no es una cartera histórica nueva. Una mejora en cobertura puede reducir la masa de 14.');note.setWordWrap(True);cl.addWidget(note)
    proposals=QWidget();pl=QVBoxLayout(proposals);tabs.addTab(proposals,'Apuestas y aportación marginal')
    _,pm=parent.table(('14 signos','Pleno','Ganancia 13+','Ganancia 12+','Ganancia de masa'),pl)
    pm.update_rows([(x['column'],x['pleno'],pct(x['gain_13']),pct(x['gain_12']),pct(x['probability_gain'])) for x in report['marginal'][:500]])
    row=QHBoxLayout();layout.addLayout(row)
    apply=QPushButton('Aplicar selección');row.addWidget(apply)
    def commit():
        def action():
            if parent.system!=source or parent.round.key!=source.round_key:raise ValueError('La quiniela abierta cambió. Repite el cálculo para aplicar una propuesta.')
            parent.set_system(parent.service.apply_portfolio(source,result));dialog.accept()
        parent.safe(action)
    apply.clicked.connect(commit)
    export=QPushButton('TuLotero: preparar boletos');row.addWidget(export);export.clicked.connect(lambda:parent.open_tulotero(result.bets,round_))
    audit=QPushButton('Guardar informe JSON');row.addWidget(audit)
    def save_audit():
        path,_=QFileDialog.getSaveFileName(dialog,'Informe de optimización','optimizacion.json','JSON (*.json)')
        if path:parent.safe(lambda:atomic_text(path,json.dumps(report,ensure_ascii=False,indent=2)))
    audit.clicked.connect(save_audit)
    close=QPushButton('No aplicar / cerrar');row.addWidget(close);close.clicked.connect(dialog.reject)
    dialog.proposal=result;dialog.apply_button=apply
    return dialog


def tulotero_dialog(parent,bets,round_):
    dialog=QDialog(parent);dialog.setWindowTitle('TuLotero · preparación manual de boletos');dialog.resize(900,650)
    layout=QVBoxLayout(dialog)
    note=QLabel(f'{round_.key} · {sum(b.quantity for b in bets)} apuestas · precio congelado {round_.price_cents/100:.2f} €\nPerfil revisado 13/10/2026: 2–8 sencillas por boleto, Pleno común. Revisa las reglas del canal antes de jugar. CSV/TXT son archivos de preparación propios, no importación automática documentada. No se envía ni se paga nada.');note.setWordWrap(True);layout.addWidget(note)
    row=QHBoxLayout();layout.addLayout(row)
    saved=parent.repository.setting('tulotero_channel_rules',dict(minimum=2,maximum=8))
    row.addWidget(QLabel('Mínimo por boleto'));minimum=QSpinBox();minimum.setRange(1,100);minimum.setValue(saved.get('minimum',2));row.addWidget(minimum)
    row.addWidget(QLabel('Máximo por boleto'));maximum=QSpinBox();maximum.setRange(1,100);maximum.setValue(saved.get('maximum',8));row.addWidget(maximum)
    feedback=QLabel();feedback.setWordWrap(True);layout.addWidget(feedback)
    view,model=parent.table(('Boleto','Apuesta','Signos 1–14','Local','Visitante','Coste boleto'),layout)
    buttons=QHBoxLayout();layout.addLayout(buttons)
    exports=[]
    for label,format in (('TXT actual','raw'),('TXT por boletos','txt'),('CSV por boletos','csv')):
        button=QPushButton(label);buttons.addWidget(button);exports.append(button)
        def export(checked=False,format=format):
            path,_=QFileDialog.getSaveFileName(dialog,'Guardar preparación manual',f'boletos-{round_.season}-J{round_.number:02d}.{"csv" if format=="csv" else "txt"}')
            if not path:return
            def action():
                if format=='raw':write_txt(Path(path),bets)
                else:write_ticket_file(path,bets,round_.price_cents,format=format,rules=ChannelRules(minimum=minimum.value(),maximum=maximum.value()))
                feedback.setText('Guardado y relectura verificada: '+path+' · introduce las apuestas manualmente en TuLotero.')
            parent.safe(action)
        button.clicked.connect(export)
    web=QPushButton('Abrir TuLotero');buttons.addWidget(web);web.setEnabled(round_.season!='DEMO' and round_.editable)
    web.clicked.connect(lambda:QDesktopServices.openUrl(QUrl('https://tulotero.es/jugar-quiniela/')))
    close=QPushButton('Cerrar');buttons.addWidget(close);close.clicked.connect(dialog.reject)
    def update():
        try:
            rules=ChannelRules(minimum=minimum.value(),maximum=maximum.value());tickets=group_tickets(bets,rules)
            parent.repository.set_setting('tulotero_channel_rules',dict(minimum=rules.minimum,maximum=rules.maximum))
            rows=[]
            for t in tickets:
                for i,b in enumerate(t.bets):
                    if len(rows)<500:rows.append((t.number,i+1,b.column,b.pleno[0],b.pleno[1],f'{len(t.bets)*round_.price_cents/100:.2f} €'))
            custom=' Perfil personalizado: compatibilidad TuLotero NO confirmada.' if (rules.minimum,rules.maximum)!=(2,8) else ''
            model.update_rows(rows);feedback.setText(f'{len(tickets)} boletos · Plenos conservados · vista de las primeras 500 apuestas. Perfil configurable, no compra validada.'+custom)
            for button in exports:button.setEnabled(True)
        except ValueError as exc:
            model.update_rows([]);feedback.setText(str(exc))
            for button in exports:button.setEnabled(False)
    minimum.valueChanged.connect(update);maximum.valueChanged.connect(update);update()
    dialog.minimum=minimum;dialog.maximum=maximum;dialog.preview_model=model;dialog.export_buttons=exports
    return dialog
