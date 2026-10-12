"""Formatos propios versionados y TXT de apuestas sin recorte de filas."""
from collections import Counter
import json
import os
from pathlib import Path
from quiniela_ai_studio.domain.models import Bet, round_dict, round_from_dict, system_dict, system_from_dict

MAX_FILE_BYTES = 20 * 1024 * 1024


def read_bytes(path):
    with Path(path).open('rb') as file:
        data = file.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError('El archivo supera 20 MiB.')
    return data


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(text, encoding='utf-8', newline='\n')
    os.replace(temporary, path)


def read_txt(path, preserve_quantity=True):
    text = read_bytes(path).decode('utf-8-sig')
    values = []
    for index, line in enumerate(text.splitlines(), 1):
        line = line.strip().upper()
        if not line:
            continue
        if len(line) not in (14, 16):
            raise ValueError(f'Línea {index}: se requieren 14 o 16 signos.')
        try:
            bet = Bet(line[:14], line[14:])
        except ValueError as exc:
            raise ValueError(f'Línea {index}: {exc}') from exc
        values.append((bet.column, bet.pleno))
    if not values:
        raise ValueError('No hay apuestas en el archivo.')
    counts = Counter(values)
    return tuple(Bet(*key, count if preserve_quantity else 1) for key, count in counts.items())


def write_txt(path, bets):
    if not bets:
        raise ValueError('No hay apuestas para exportar.')
    if any(not b.pleno for b in bets):
        raise ValueError('Completa el Pleno de todas las apuestas antes de exportar TXT.')
    if sum(b.quantity for b in bets) * 17 > MAX_FILE_BYTES:
        raise ValueError('La exportación TXT excede el límite de 20 MiB; utiliza JSON.')
    atomic_text(path, ''.join((b.column + b.pleno + '\n') * b.quantity for b in bets))


def write_system(path, system, round_):
    if system.round_key != round_.key:
        raise ValueError('Sistema y jornada no coinciden.')
    atomic_text(path, json.dumps(dict(format='quiniela-studio', version=1,
        round=round_dict(round_), system=system_dict(system)), ensure_ascii=False, indent=2))


def read_system(path):
    data = json.loads(read_bytes(path))
    if data.get('schema') == 'quiniela_ai_studio.selection':
        return read_selection_project(data)
    if data.get('format') != 'quiniela-studio' or data.get('version') != 1:
        raise ValueError('Formato o versión JSON no admitida.')
    round_ = round_from_dict(data['round'])
    system = system_from_dict(data['system'])
    if system.round_key != round_.key:
        raise ValueError('El sistema y los datos pertenecen a jornadas distintas.')
    return round_, system


def read_round(path):
    data = json.loads(read_bytes(path))
    if data.get('format') != 'quiniela-studio-round' or data.get('version') != 1:
        raise ValueError('Se requiere una jornada JSON de Studio versión 1.')
    return round_from_dict(data['round'])


def write_development(path, system, round_, *, format='txt', cancelled=lambda:False, progress=lambda done,total:None):
    """Exportación atómica perezosa; sistemas con apuestas exportan solo sus apuestas exactas."""
    import tempfile
    from dataclasses import replace
    from quiniela_ai_studio.domain.engine import iter_bets, Cancelled
    from quiniela_ai_studio.domain.selection import Selection
    if format not in ('txt','json'):raise ValueError('Formato TXT o JSON requerido.')
    if system.round_key!=round_.key:raise ValueError('Jornada y sistema diferentes.')
    if not system.bets and json.loads(system.parameters).get('filter_spec'):
        raise ValueError('No hay apuestas que guardar. Cambia las condiciones de Optimizar.')
    if system.bets:
        bets=iter(system.bets);total=system.quantity;exported=system
    else:
        selection=Selection(system.base,system.plenos)
        bets=iter_bets(selection.base,selection.plenos,cancelled)
        total=selection.quantity
        exported=replace(system,origin='desarrollo directo exportado; borrador de origen conservado')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='\n',dir=path.parent,delete=False) as output:
            temporary=Path(output.name)
            if format=='json':
                header=system_dict(replace(exported,bets=()))
                del header['bets']
                output.write('{"format":"quiniela-studio","version":1,"round":')
                output.write(json.dumps(round_dict(round_),ensure_ascii=False))
                output.write(',"system":'+json.dumps(header,ensure_ascii=False)[:-1]+',"bets":[')
            count=0;first=True
            for bet in bets:
                if count%4096==0:
                    if cancelled():raise Cancelled('Exportación cancelada; el archivo anterior se conserva.')
                    progress(count,total)
                if format=='txt':
                    if not bet.pleno:raise ValueError('Completa el Pleno antes de exportar TXT.')
                    for _ in range(bet.quantity):output.write(bet.column+bet.pleno+'\n')
                else:
                    if not first:output.write(',')
                    output.write(json.dumps(dict(column=bet.column,pleno=bet.pleno,quantity=bet.quantity)))
                    first=False
                count+=bet.quantity
            if format=='json':output.write(']}}\n')
            if cancelled():raise Cancelled('Exportación cancelada; el archivo anterior se conserva.')
            output.flush();os.fsync(output.fileno())
        os.replace(temporary,path);progress(count,total)
        return count
    finally:
        if temporary and temporary.exists():temporary.unlink()


def read_selection_project(data):
    """Adaptador del proyecto demo de referencia, sin inventar identidad de jornadas reales."""
    from dataclasses import replace
    import uuid
    from quiniela_ai_studio.domain.selection import Selection, GameRuleset
    from quiniela_ai_studio.domain.engine import iter_bets, MAX_GENERATED
    from quiniela_ai_studio.domain.models import SystemVersion, utcnow
    from quiniela_ai_studio.infrastructure.demo import demo_round
    if data.get('version')!=1 or data.get('demo') is not True:
        raise ValueError('Este esquema de selección requiere versión 1 y demo explícita; jornadas reales requieren identidad completa.')
    if not data.get('draw_id'):raise ValueError('Falta la identidad draw_id del proyecto.')
    rule=GameRuleset(data.get('ruleset_id',''),data.get('unit_price_cents'))
    pairs=data.get('full15',[])
    if any(not isinstance(pair,list) or len(pair)!=2 or any(not isinstance(v,str) for v in pair) for pair in pairs):
        raise ValueError('Cada Pleno debe ser una pareja explícita de goles.')
    selection=Selection(tuple(data.get('picks14',[])),tuple(''.join(pair) for pair in pairs))
    if selection.quantity>MAX_GENERATED:raise ValueError('Proyecto demasiado grande para importación materializada; usa exportación directa.')
    round_=replace(demo_round(),price_cents=rule.price_cents,rules_version=rule.version,source='DEMO · proyecto de referencia '+data['draw_id'])
    system=SystemVersion(str(uuid.uuid4()),1,round_.key,data['draw_id'],selection.base,(False,)*14,
                         selection.plenos[0] if len(selection.plenos)==1 else '',tuple(iter_bets(selection.base,selection.plenos)),
                         utcnow(),'proyecto demo importado',json.dumps(dict(selection_project=data)),json.dumps(round_dict(round_)))
    return round_,system
