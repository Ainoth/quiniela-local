"""Motor de referencia de v0.1; límites explícitos, sin garantías de reducción."""
import itertools
import math

from quiniela_ai_studio.domain.models import SIGNS, Bet, normalize_base

MAX_GENERATED = 100_000


def iter_bets(base, plenos, cancelled=lambda: False, progress=lambda done, total: None):
    """Itera todo el desarrollo sin materializar el universo ni multiplicar parejas P15."""
    from .selection import Selection
    selection = Selection(tuple(base), tuple(plenos))
    index = 0
    for column in itertools.product(*selection.base):
        for pleno in selection.plenos:
            if index % 4096 == 0:
                if cancelled(): raise Cancelled('Exportación cancelada; el archivo anterior se conserva.')
                progress(index, selection.quantity)
            yield Bet(''.join(column), pleno)
            index += 1
    if cancelled(): raise Cancelled('Exportación cancelada; el archivo anterior se conserva.')
    progress(selection.quantity, selection.quantity)


class Cancelled(Exception):
    pass


def size(base):
    return math.prod(len(s) for s in normalize_base(base))


def column_id(column):
    from quiniela_ai_studio.domain.models import validate_column
    validate_column(column)
    value = 0
    for sign in column:
        value = value * 3 + SIGNS.index(sign)
    return value


def decode_column(value):
    if type(value) is not int or not 0 <= value < 3**14:
        raise ValueError("ID fuera del universo de 14 signos.")
    signs = []
    for _ in range(14):
        value, digit = divmod(value, 3)
        signs.append(SIGNS[digit])
    return "".join(reversed(signs))


def generate(base, pleno, cancelled=lambda: False, progress=lambda done, total: None):
    base = normalize_base(base)
    plenos=(pleno,) if isinstance(pleno,str) else tuple(pleno)
    if not plenos or len(plenos)>16 or len(set(plenos))!=len(plenos):raise ValueError('Selecciona resultados distintos del Pleno.')
    for pair in plenos:Bet('1'*14,pair)
    total = size(base)*len(plenos)
    if total > MAX_GENERATED:
        raise ValueError(f"v0.1 admite hasta {MAX_GENERATED:,} columnas por generación; esta base tiene {total:,}.")
    output = []
    for column in itertools.product(*base):
        for pair in plenos:
            index=len(output)
            if index % 256 == 0:
                if cancelled():raise Cancelled("Generación cancelada; se conserva el sistema anterior.")
                progress(index,total)
            output.append(Bet("".join(column),pair))
    if cancelled():
        raise Cancelled("Generación cancelada; se conserva el sistema anterior.")
    progress(total, total)
    return tuple(output)


# (triples, dobles), aplicado solo a posiciones sin bloqueo.
COVERAGE_LEVELS = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4),
                   (1, 5), (2, 5), (2, 6), (3, 6), (3, 7))


PLENO_COVERAGE_LEVELS = ((1, 1), (1, 1), (1, 2), (1, 2), (2, 2), (2, 2),
                         (2, 3), (2, 3), (3, 3), (3, 4), (4, 4))


def pleno_template(snapshot, level: int) -> tuple[str, str]:
    """Heurística propia: ampliar 0/1/2/M por probabilidad marginal, no garantía."""
    if type(level) is not int or not 0 <= level <= 10:
        raise ValueError("Nivel del Pleno entre 0 y 10 requerido.")
    if not snapshot or not snapshot.pleno_values:
        raise ValueError("No hay porcentajes del Pleno para esta fuente.")
    from .models import GOALS
    widths = PLENO_COVERAGE_LEVELS[level]
    return tuple(''.join(g for g in GOALS if g in sorted(GOALS, key=lambda g: (-snapshot.pleno_values[side][GOALS.index(g)], GOALS.index(g)))[:widths[side]]) for side in range(2))


def coverage_template(base, locks, level, snapshot=None):
    base = normalize_base(base)
    if len(locks) != 14 or any(type(v) is not bool for v in locks) or type(level) is not int or not 0 <= level <= 10:
        raise ValueError("Nivel 0–10 y 14 bloqueos válidos requeridos.")
    rankings = [sorted(SIGNS, key=lambda s: (-snapshot.values[i][SIGNS.index(s)], SIGNS.index(s))) if snapshot else list(SIGNS)
                for i in range(14)]
    available = [i for i in range(14) if not locks[i]]
    if snapshot:
        available.sort(key=lambda i: (max(snapshot.values[i]), i))
    triples, doubles = COVERAGE_LEVELS[level]
    widths = [3] * triples + [2] * doubles
    result = list(base)
    for index, position in enumerate(available):
        width = widths[index] if index < len(widths) else 1
        result[position] = "".join(s for s in SIGNS if s in rankings[position][:width])
    return tuple(result)


def log_probability(column, snapshot):
    return sum(math.log(p) if p else -math.inf for p in (snapshot.values[i][SIGNS.index(s)] for i, s in enumerate(column)))


def probability_mass(bets, snapshot):
    return math.fsum(math.exp(log_probability(c, snapshot)) for c in {b.column for b in bets})


def optimize(bets, budget_cents, price_cents, snapshot=None):
    if type(budget_cents) is not int or budget_cents < 0 or type(price_cents) is not int or price_cents <= 0:
        raise ValueError("Presupuesto y precio en céntimos válidos requeridos.")
    # Las cantidades se agregan por apuesta exacta, nunca por la unión visible.
    grouped = {}
    for bet in bets:
        key = (bet.column, bet.pleno)
        grouped[key] = grouped.get(key, 0) + bet.quantity
    ordered = sorted(grouped, key=lambda key: (-log_probability(key[0], snapshot), key) if snapshot else key)
    remaining = budget_cents // price_cents
    result = []
    for key in ordered:
        quantity = min(grouped[key], remaining)
        if quantity:
            result.append(Bet(*key, quantity))
            remaining -= quantity
    return tuple(result)


def union_base(bets, fallback):
    return tuple("".join(s for s in SIGNS if any(b.column[i] == s for b in bets)) for i in range(14)) if bets else normalize_base(fallback)


def evaluate(bets, result, pleno="", finalized=None, prizes=None, official=False, pleno_final=None):
    if len(result) != 14 or set(result) - set("1X2-"):
        raise ValueError("Introduce 14 signos 1/X/2; usa - para resultados pendientes.")
    if pleno and (len(pleno) != 2 or set(pleno) - set("012M")):
        raise ValueError("Pleno inválido.")
    finalized = tuple(finalized if finalized is not None else (False,) * 14)
    if len(finalized) != 14 or any(type(v) is not bool for v in finalized) or any(f and result[i] == '-' for i, f in enumerate(finalized)):
        raise ValueError("Los finalizados necesitan un resultado.")
    if pleno_final is None:pleno_final=bool(pleno)
    if type(pleno_final) is not bool:raise ValueError('Estado de Pleno inválido.')
    definitive = all(finalized) and '-' not in result
    if prizes is not None and (not official or not definitive):
        raise ValueError("Los importes requieren resultado definitivo y escrutinio publicado.")
    if prizes and any(type(k) is not int or k not in (10, 11, 12, 13, 14, 15) or type(v) is not int or v < 0 for k, v in prizes.items()):
        raise ValueError("Premios no válidos en céntimos.")
    rows = []
    counts = {c: 0 for c in (10, 11, 12, 13, 14, 15)}
    for bet in bets:
        hits = sum(s == r for s, r in zip(bet.column, result) if r != '-')
        fixed = sum(s == r and f for s, r, f in zip(bet.column, result, finalized))
        maximum = 14 - sum(s != r and f for s, r, f in zip(bet.column, result, finalized))
        pleno_hit = bool(pleno and bet.pleno == pleno)
        if definitive and hits >= 10:
            counts[hits] += bet.quantity
            if hits == 14 and pleno_hit and pleno_final:
                counts[15] += bet.quantity
        rows.append(dict(column=bet.column, pleno=bet.pleno, quantity=bet.quantity, hits=hits,
                         confirmed=fixed, maximum=maximum, misses=sum(r!="-" for r in result)-hits, pending=result.count("-"),
                         pleno_hit=pleno_hit,full15_hit=bool(definitive and hits==14 and pleno_hit and pleno_final)))
    return dict(rows=sorted(rows, key=lambda r: (-r['hits'], -r['maximum'], r['column'])), counts=counts,
                known=sum(s != '-' for s in result), definitive=definitive,
                prize_cents=sum(counts[k] * v for k, v in (prizes or {}).items()) if prizes is not None else None)
