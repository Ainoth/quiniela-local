"""Formatos propios versionados y TXT de apuestas sin recorte de filas."""
from collections import Counter
import json
import os
from pathlib import Path
from .domain import Bet, round_dict, round_from_dict, system_dict, system_from_dict

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
