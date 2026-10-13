"""Exact published reductions; selected matches and remaining direct combinations."""
from collections.abc import Callable
from dataclasses import dataclass
from itertools import product
from math import prod

from .engine import MAX_GENERATED, Cancelled, size
from .models import Bet
from .reduction_tables import TABLES, ReductionTable
from .selection import Selection


@dataclass(frozen=True)
class ReductionPlan:
    table: ReductionTable
    selection: Selection
    positions: tuple[int, ...]
    before: int
    after: int


def reduction_template(base, locks, number: int, weights):
    """Base independiente: múltiples en posiciones ambiguas, fijos según fuente."""
    from .models import SIGNS, normalize_base
    base = normalize_base(base)
    if type(number) is not int or not 1 <= number <= len(TABLES):
        raise ValueError('Elige una de las seis reducciones.')
    if len(locks) != 14 or any(type(v) is not bool for v in locks):
        raise ValueError('Se requieren 14 bloqueos válidos.')
    table = TABLES[number - 1]
    ranking = [sorted(SIGNS, key=lambda s: (-weights.values[i][SIGNS.index(s)], SIGNS.index(s))) for i in range(14)]
    result = [base[i] if locks[i] else ranking[i][0] for i in range(14)]
    remaining = sorted((i for i in range(14) if not locks[i]), key=lambda i: (max(weights.values[i]), i))
    positions = []
    for width in (3, 2):
        locked = [i for i in range(14) if locks[i] and len(base[i]) == width]
        required = table.widths.count(width)
        if len(locked) > required or required - len(locked) > len(remaining):
            raise ValueError('Los bloqueos no permiten este tipo de reducida. Desbloquea o elige otra tabla.')
        chosen = locked + remaining[:required - len(locked)]
        remaining = remaining[required - len(locked):]
        for i in chosen:
            if not locks[i]:
                result[i] = ''.join(s for s in SIGNS if s in ranking[i][:width])
        positions.extend(chosen)
    return tuple(result), tuple(sorted(positions))


def plan_reduction(base, plenos, number: int, positions) -> ReductionPlan:
    """Map table groups to selected match ordinals, doubles and triples separately."""
    if type(number) is not int or not 1 <= number <= 6:
        raise ValueError('Elige una de las seis reducciones.')
    selection = Selection(tuple(base), tuple(plenos))
    table = TABLES[number - 1]
    chosen = tuple(positions)
    if (len(chosen) != len(table.widths) or any(type(i) is not int or not 0 <= i < 14 for i in chosen)
            or len(set(chosen)) != len(chosen)):
        raise ValueError(f'Marca exactamente {len(table.widths)} partidos para esta reducción.')
    groups = {width: sorted(i for i in chosen if len(selection.base[i]) == width) for width in (2, 3)}
    if any(len(groups[width]) != table.widths.count(width) for width in (2, 3)):
        raise ValueError(f'Esta reducción necesita {table.widths.count(2)} dobles y {table.widths.count(3)} triples marcados.')
    ordered = tuple(groups[width].pop(0) for width in table.widths)
    extra = prod(len(mask) for i, mask in enumerate(selection.base) if i not in chosen)
    return ReductionPlan(table, selection, ordered, size(selection.base) * len(selection.plenos),
                         len(table.patterns) * extra * len(selection.plenos))


def reduced_bets(plan: ReductionPlan, cancelled: Callable[[], bool] = lambda: False) -> tuple[Bet, ...]:
    """Use exact matrix columns; never replace an official table with a heuristic."""
    if plan.after > MAX_GENERATED:
        raise ValueError('La reducción supera 100.000 apuestas incluyendo el Pleno. Reduce otros dobles/triples o resultados del Pleno.')
    result = []
    other = tuple(i for i in range(14) if i not in plan.positions)
    for pattern in plan.table.patterns:
        for extra in product(*(plan.selection.base[i] for i in other)):
            column = [''] * 14
            for i, digit in zip(plan.positions, pattern):column[i] = plan.selection.base[i][digit]
            for i, sign in zip(other, extra):column[i] = sign
            for pleno in plan.selection.plenos:
                if len(result) % 256 == 0 and cancelled():raise Cancelled('Reducción cancelada.')
                result.append(Bet(''.join(column), pleno))
    if cancelled():raise Cancelled('Reducción cancelada.')
    return tuple(result)
