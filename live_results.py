"""Marcador público usado por Quinielista; resultados siempre provisionales.

Fuente y esquema: https://static.quinielista.es/marcador/horizontal/foro/iframeQuinielista.html
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from dataclasses import dataclass

LIVE_URL = 'https://static.dataradar.es/marcador/json/partidos.json'


@dataclass(frozen=True)
class LiveMatch:
    number: int
    home: str
    away: str
    score: str
    sign: str
    pleno: str
    status: str
    final: bool
    updated: int


def parse_live_results(payload: bytes, season: str, round_no: int) -> list[LiveMatch]:
    year = 2000 + int(season.split('-')[-1])
    rows = json.loads(payload)
    if not isinstance(rows, list):
        raise ValueError('Formato de marcador no reconocido.')
    selected = [r for r in rows if int(r['temporada']) == year and int(r['jornada']) == round_no]
    if len(selected) != 15 or sorted(int(r['orden']) for r in selected) != list(range(1, 16)):
        raise ValueError(f'El proveedor no ofrece el directo de la jornada {round_no} ({season}).')
    matches = []
    for row in sorted(selected, key=lambda r: int(r['orden'])):
        state = str(row.get('estado', '')).strip()
        final = state.casefold() in {'finalizado', 'final', 'terminado', 'finalizada'}
        live = str(row.get('live')) == '1'
        pending = state.casefold() in {'sin comenzar', 'pendiente', 'aplazado', 'suspendido'}
        active = (final or live) and not pending
        goals = [str(row.get(key, '')).strip() for key in ('local_goles', 'visitante_goles')]
        score, sign, pleno = '—', '', ''
        if active and all(re.fullmatch(r'\d{1,2}', value) for value in goals):
            home, away = map(int, goals)
            score = f'{home} - {away}'
            sign = '1' if home > away else '2' if home < away else 'X'
            pleno = ''.join(str(g) if g < 3 else 'M' for g in (home, away))
        # Un signo asignado por sorteo se usa solo si el proveedor lo identifica.
        if str(row.get('sorteado')) == '1':
            assigned = str(row.get('signo', '')).upper()
            if assigned in ('1', 'X', '2'):
                sign, final, state = assigned, True, 'Sorteado'
            assigned_pleno = str(row.get('signo_goles', '')).replace('-', '').upper()
            if re.fullmatch(r'[012M]{2}', assigned_pleno):
                pleno = assigned_pleno
        minute = str(row.get('info_minute') or row.get('minuto') or '').strip()
        status = state or ('En juego' if live else 'Sin datos')
        if live and minute:
            status += f' · {minute}'
        if pending:
            status += ' · ' + str(row.get('dia', '')) + ' ' + str(row.get('hora', ''))
        matches.append(LiveMatch(int(row['orden']), row['local'], row['visitante'],
                                 score, sign, pleno, status.strip(), final, int(row.get('uts') or 0)))
    return matches


def fetch_live_results(season: str, round_no: int) -> list[LiveMatch]:
    request = urllib.request.Request(f'{LIVE_URL}?r={time.time_ns()}', headers={
        'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.eduardolosilla.es/',
        'Cache-Control': 'no-cache',
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = response.read(1024 * 1024 + 1)
    if len(payload) > 1024 * 1024:
        raise ValueError('Respuesta del marcador demasiado grande.')
    return parse_live_results(payload, season, round_no)


def evaluate_live_bets(bets: list[str], matches: list[LiveMatch]) -> list[dict]:
    result = []
    for bet in bets:
        known = [m for m in matches[:14] if m.sign]
        hits = sum(bet[m.number - 1] == m.sign for m in known)
        fixed_hits = sum(bet[m.number - 1] == m.sign for m in known if m.final)
        fixed_misses = sum(bet[m.number - 1] != m.sign for m in known if m.final)
        pleno = matches[14]
        p15 = 'Sin apuesta' if len(bet) < 16 else 'Pendiente' if not pleno.pleno else (
            ('Sí' if bet[14:] == pleno.pleno else 'No') + ('' if pleno.final else ' (prov.)'))
        result.append(dict(bet=bet, hits=hits, known=len(known), fixed=fixed_hits,
                           maximum=14 - fixed_misses, pleno=p15))
    return sorted(result, key=lambda r: (r['hits'], r['maximum'], r['fixed']), reverse=True)
