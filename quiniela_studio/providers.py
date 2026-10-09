"""Lectores locales; no importa la UI histórica ni hace descargas implícitas."""
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import re
import uuid
from .domain import Round, Match, ProbabilitySnapshot, utcnow
from .files import read_bytes, atomic_text


def text(path):
    return read_bytes(path).decode('cp1252')


def scrutiny_record(line):
    if len(line) < 119 or not line[:2].strip().isdigit():
        raise ValueError('Registro PRE incompleto.')
    number = int(line[:2])
    result = line[104:118].upper()
    if not re.fullmatch('[1X2]{14}', result):
        return None
    if line[118].upper() not in '0123456789ABCDEF':
        return None
    code = int(line[118], 16)
    pleno = '012M'[code // 4] + '012M'[code % 4]
    winners, amounts = {}, {}
    for i, category in enumerate((15, 14, 13, 12, 11, 10)):
        winners[category] = int(line[2 + 7*i:9 + 7*i].strip() or '0')
        amount = Decimal(line[44 + 10*i:54 + 10*i].strip().replace('.', '').replace(',', '.') or '0')
        if not amount.is_finite() or amount < 0 or amount * 100 != int(amount * 100):
            raise ValueError('Importe PRE inválido.')
        amounts[category] = int(amount * 100)
    return dict(round_no=number, result=result, pleno=pleno, prizes=amounts, winners=winners)


def load_win1x2(directory, today=None):
    directory = Path(directory)
    today = today or date.today()
    names = {}
    for path in directory.iterdir():
        if path.name.upper() == 'WEQUIPOS.TXT' or path.name.upper().startswith('EQ'):
            if path.suffix.lower() != '.txt':
                continue
            for line in text(path).splitlines():
                if '-' in line:
                    code, name = line.split('-', 1)
                    if len(code.strip()) == 3:
                        names[code.strip().upper()] = name.strip()
    rounds = []
    for path in sorted(directory.glob('*')):
        if not re.fullmatch(r'PRE\d{2}-\d{2}\.txt', path.name, re.I):
            continue
        season = path.stem[3:]
        dates_path = directory / f'FEC{season}.txt'
        if not dates_path.exists():
            continue
        dates = {int(m[1]): datetime.strptime(m[2], '%d/%m/%Y').date()
                 for line in text(dates_path).splitlines()
                 if (m := re.match(r'(\d{2}):(\d{2}/\d{2}/\d{4})', line))}
        # Sin hora de cierre fiable, solo la fecha nominal de hoy permite edición.
        schedules = {}
        for candidate in directory.iterdir():
            if candidate.name.lower() == f'hor{season}.txt'.lower():
                schedules = {int(line[:2]): [line[2+i*15:2+(i+1)*15] for i in range(15)]
                             for line in text(candidate).splitlines() if line[:2].isdigit()}
        captured = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        for line in text(path).splitlines():
            if len(line) < 209 or not line[:2].strip().isdigit():
                continue
            number = int(line[:2]); nominal = dates.get(number)
            if nominal is None:
                continue
            codes = [line[119+i*3:122+i*3].upper() for i in range(30)]
            if any(not re.fullmatch('[A-Z0-9]{3}', code) for code in codes):
                continue
            matches = tuple(Match(i+1, names.get(codes[2*i], codes[2*i]), names.get(codes[2*i+1], codes[2*i+1]),
                                  schedules.get(number, ['']*15)[i], f'win1x2:{season}:{codes[2*i]}',
                                  f'win1x2:{season}:{codes[2*i+1]}') for i in range(15))
            mode = 'current' if nominal == today else 'past' if nominal < today else 'future'
            rounds.append(Round(season, number, matches, mode, f'WIN1X2 local · {path.name}', captured,
                                rules_version='referencia-local-75c; confirmar canal antes de jugar', nominal_date=nominal.isoformat()))
    if not rounds:
        raise ValueError('No se encontraron jornadas PRE/FEC válidas.')
    return tuple(rounds)


def migrate_legacy(path, repository, service):
    """Copia el original y recupera selecciones cuya jornada está identificada.

    Columnas globales nunca se atribuyen automáticamente a la jornada vigente.
    """
    path = Path(path)
    raw = read_bytes(path)
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('El archivo anterior no es un diccionario JSON.')
    predictions = data.get('predictions', data)
    if not isinstance(predictions, dict):
        raise ValueError('Pronósticos anteriores inválidos.')
    target = repository.path.parent / ('migration-' + uuid.uuid4().hex)
    target.mkdir()
    backup = target / path.name
    backup.write_bytes(raw)
    groups = {}
    unresolved = {}
    for key, value in predictions.items():
        match = re.fullmatch(r'(\d{2}-\d{2})-(\d{1,2})-(\d{1,2})', str(key))
        if not match:
            unresolved[str(key)] = value
            continue
        season, number, position = match.groups()
        round_key = f'{season}/J{int(number):02}'
        groups.setdefault(round_key, {})[int(position)] = value
    # Validar y preparar todas las versiones antes de escribir ninguna.
    prepared = []
    for key, values in groups.items():
        try:
            round_ = repository.round(key)
            base = tuple(values.get(i, '1') for i in range(1, 15))
            from .domain import SystemVersion, normalize_base
            base = normalize_base(base)
            pleno = str(values.get(15, '')).replace('-', '')
            system = SystemVersion(str(uuid.uuid4()), 1, key, 'Pronóstico recuperado', base,
                                   (False,)*14, pleno, (), utcnow(), 'migración de selecciones; sin columnas asignadas',
                                   round_snapshot=json.dumps(__import__('dataclasses').asdict(round_)))
            prepared.append(system)
        except (ValueError, TypeError):
            unresolved[key] = values
    # Mantener los desarrollos globales originales en un archivo SIN ASIGNAR.
    unassigned = dict(predictions=unresolved, development_columns=data.get('development_columns'),
                      development_source=data.get('development_source'), original=str(backup))
    atomic_text(target / 'sin-asignar.json', json.dumps(unassigned, ensure_ascii=False, indent=2))
    # Savepoints permiten rollback integral aunque Repository.save use transacciones.
    with repository.db:
        for system in prepared:
            repository.db.execute('INSERT INTO systems VALUES (?,?)', (system.system_id, system.round_key))
            from .domain import system_dict
            repository.db.execute('INSERT INTO versions VALUES (?,?,?,?)', (system.system_id, 1, json.dumps(system_dict(system)), system.hash))
            repository.db.execute('INSERT INTO audit(created_at,action,system_id,revision,details) VALUES (?,?,?,?,?)',
                                  (utcnow(), 'migration', system.system_id, 1, str(backup)))
    return len(prepared), target
