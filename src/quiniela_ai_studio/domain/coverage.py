"""Verificación independiente de los aciertos de 14; nunca certifica premios."""
import math
import random
from dataclasses import dataclass
from itertools import product

from .engine import Cancelled, log_probability
from .models import normalize_base, validate_column

THRESHOLDS = (14, 13, 12, 11, 10)


@dataclass(frozen=True)
class Universe:
    outcomes: tuple[str, ...]
    total: int
    exact: bool
    weights: tuple[float, ...] | None
    description: str


def make_universe(base, sport=None, *, outcomes=None, limit=4096, seed=0) -> Universe:
    """Muestra uniforme reproducible; pesos por importancia si no se enumera todo."""
    if type(limit) is not int or limit < 1:
        raise ValueError('Límite de escenarios positivo requerido.')
    rng = random.Random(seed)
    if outcomes is not None:
        all_outcomes = tuple(sorted({validate_column(c) for c in outcomes}))
        if not all_outcomes:
            raise ValueError('Universo de resultados vacío.')
        total = len(all_outcomes)
        exact = total <= limit
        chosen = all_outcomes if exact else tuple(rng.choice(all_outcomes) for _ in range(limit))
        description = 'columnas candidatas admitidas por condiciones'
    else:
        base = normalize_base(base)
        total = math.prod(map(len, base))
        exact = total <= limit
        chosen = tuple(''.join(c) for c in product(*base)) if exact else tuple(''.join(rng.choice(s) for s in base) for _ in range(limit))
        description = 'base completa de 14 signos, incluidos resultados descartados por filtros'
    weights = None
    if sport:
        if sport.kind != 'sport':
            raise ValueError('Popularidad no puede usarse como probabilidad deportiva.')
        logs = [log_probability(c, sport) for c in chosen]
        peak = max(logs)
        if math.isfinite(peak):
            values = [math.exp(value-peak) for value in logs]
            weights = tuple(value/math.fsum(values) for value in values)
    return Universe(chosen, total, exact, weights, description)


def hamming(a: str, b: str) -> int:
    validate_column(a);validate_column(b)
    return sum(x != y for x, y in zip(a, b))


def diversity(bets) -> float:
    """Distancia media de todas las parejas de apuestas, incluyendo Plenos distintos."""
    columns = [b.column for b in bets]
    if len(columns) < 2:
        return 0.0
    # Conteos por signo: calcula todas las distancias sin enumerar O(N²) parejas.
    pairs = len(columns)*(len(columns)-1)//2
    differences = 0
    for position in range(14):
        equal = sum((count := sum(c[position] == sign for c in columns))*(count-1)//2 for sign in '1X2')
        differences += pairs-equal
    return differences/pairs


def verify_coverage(bets, universe: Universe, *, cancelled=lambda: False, progress=lambda done,total: None):
    """Oráculo independiente: coincidencias directas, no matrices del optimizador."""
    columns = sorted({b.column for b in bets})
    counts = {str(k): 0 for k in THRESHOLDS}
    weighted = {str(k): 0.0 for k in THRESHOLDS} if universe.weights else None
    minimum = 14 if columns else 0
    for i, result in enumerate(universe.outcomes):
        if i % 32 == 0:
            if cancelled():raise Cancelled('Verificación cancelada; no se guardan garantías parciales.')
            progress(i, len(universe.outcomes))
        best = max((sum(a == b for a,b in zip(result,column)) for column in columns),default=0)
        minimum = min(minimum,best)
        for k in THRESHOLDS:
            if best >= k:
                counts[str(k)] += 1
                if weighted is not None:weighted[str(k)] += universe.weights[i]
    if cancelled():raise Cancelled('Verificación cancelada.')
    progress(len(universe.outcomes),len(universe.outcomes))
    if weighted is not None:weighted={k:min(1.0,max(0.0,v)) for k,v in weighted.items()}
    return dict(uniform={k:v/len(universe.outcomes) for k,v in counts.items()},weighted=weighted,
                minimum_hits=minimum if universe.exact else None,
                observed_minimum=minimum,status='exacta' if universe.exact else 'estimada por muestreo',
                guarantee='demostrada dentro del universo' if universe.exact else 'no verificada',
                universe_total=universe.total,scenarios=len(universe.outcomes),universe=universe.description,
                effective_samples=1/sum(w*w for w in universe.weights) if universe.weights else None,
                mean_distance=diversity(bets))


def pleno_joint(snapshot, model='independent_goals'):
    """Modelo explícito de marginales: independencia de goles, no dato conjunto real."""
    if model != 'independent_goals' or not snapshot or snapshot.kind!='sport' or not snapshot.pleno_values:
        raise ValueError('Se requiere el modelo explícito de independencia y marginales del Pleno.')
    return {a+b:snapshot.pleno_values[0][i]*snapshot.pleno_values[1][j]
            for i,a in enumerate('012M') for j,b in enumerate('012M')}
