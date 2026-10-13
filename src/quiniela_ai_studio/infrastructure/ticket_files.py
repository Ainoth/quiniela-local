"""Formatos de preparación manual, no formatos de importación oficial TuLotero."""
import csv
import io
from collections import Counter

from quiniela_ai_studio.domain.models import Bet
from quiniela_ai_studio.domain.tickets import ChannelRules, group_tickets

from .files import MAX_FILE_BYTES, atomic_text, read_bytes

FIELDS=('Boleto','Apuesta')+tuple(f'Partido{i}' for i in range(1,15))+('GolesLocal','GolesVisitante','CosteBoletoCentimos')


def ticket_rows(tickets,price_cents):
    if type(price_cents) is not int or price_cents<=0:raise ValueError('Precio positivo en céntimos requerido.')
    return [tuple((t.number,i+1,*b.column,*b.pleno,len(t.bets)*price_cents)) for t in tickets for i,b in enumerate(t.bets)]


def parse_ticket_text(payload,format='csv',rules=ChannelRules()):
    if len(payload.encode('utf-8'))>MAX_FILE_BYTES:raise ValueError('Archivo demasiado grande.')
    if format=='txt':
        lines=[line for line in payload.splitlines() if line and not line.startswith('#')]
        reader=csv.reader(lines,delimiter=';')
    elif format=='csv':
        reader=csv.reader(io.StringIO(payload),delimiter=';')
        if tuple(next(reader,()))!=FIELDS:raise ValueError('Cabecera CSV no reconocida.')
    else:raise ValueError('Formato CSV o TXT agrupado requerido.')
    groups={};indexes=set();rows=[]
    for row in reader:
        if len(row)!=len(FIELDS):raise ValueError('Registro de boleto incompleto.')
        ticket,index=int(row[0]),int(row[1]);cost=int(row[-1])
        if ticket<1 or index<1 or cost<1 or (ticket,index) in indexes:raise ValueError('Numeración/coste de boleto inválidos.')
        indexes.add((ticket,index));bet=Bet(''.join(row[2:16]),''.join(row[16:18]))
        if not bet.pleno:raise ValueError('Pleno incompleto.')
        groups.setdefault(ticket,[]).append((index,bet,cost));rows.append(bet)
    if not rows:raise ValueError('No hay apuestas.')
    if sorted(groups)!=list(range(1,len(groups)+1)):raise ValueError('Numeración de boletos no consecutiva.')
    unit_prices=set()
    for group in groups.values():
        if not rules.minimum<=len(group)<=rules.maximum or len({b.pleno for _,b,_ in group})!=1:
            raise ValueError('Un boleto no cumple cantidad mínima/máxima o Pleno común.')
        if sorted(i for i,_,_ in group)!=list(range(1,len(group)+1)) or len({cost for _,_,cost in group})!=1:
            raise ValueError('Apuestas o costes incoherentes.')
        if group[0][2]%len(group):raise ValueError('Coste no divisible entre apuestas.')
        unit_prices.add(group[0][2]//len(group))
    if len(unit_prices)!=1:raise ValueError('Precios unitarios incoherentes entre boletos.')
    return tuple(rows)


def read_ticket_file(path,format='csv',rules=ChannelRules()):
    return parse_ticket_text(read_bytes(path).decode('utf-8-sig'),format,rules)


def write_ticket_file(path,bets,price_cents,*,format='csv',rules=ChannelRules()):
    tickets=group_tickets(tuple(bets),rules);output=io.StringIO();writer=csv.writer(output,delimiter=';',lineterminator='\n')
    if format=='csv':writer.writerow(FIELDS)
    elif format=='txt':output.write('# Quiniela AI Studio · preparación manual por boletos · NO importación oficial\n')
    else:raise ValueError('Formato CSV o TXT agrupado requerido.')
    for row in ticket_rows(tickets,price_cents):writer.writerow(row)
    payload=output.getvalue()
    original=Counter((b.column,b.pleno) for b in bets for _ in range(b.quantity))
    if Counter((b.column,b.pleno) for b in parse_ticket_text(payload,format,rules))!=original:
        raise ValueError('La exportación no conserva exactamente las apuestas; archivo anterior conservado.')
    atomic_text(path,payload)
    if Counter((b.column,b.pleno) for b in read_ticket_file(path,format,rules))!=original:
        raise ValueError('La relectura del archivo exportado no coincide.')
    return tickets
