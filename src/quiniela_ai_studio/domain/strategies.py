"""Pesos de selección originales; no son probabilidades ni premios esperados."""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SelectionWeights:
    values: tuple
    pleno_values: tuple
    source: str


def selection_weights(round_, kind='sport', differentiation=0):
    """Ordena con log(p) - alpha log(q); popularidad no equivale a rentabilidad."""
    if type(differentiation) is not int or not 0 <= differentiation <= 10:
        raise ValueError('Diferenciación entre 0 y 10 requerida.')
    selected = round_.snapshot(kind)
    if selected is None:
        raise ValueError('Esta fuente no tiene porcentajes. Descárgalos antes de recomendar signos.')
    if differentiation == 0:
        return SelectionWeights(selected.values, selected.pleno_values, selected.source)
    sport, public = round_.snapshot('sport'), round_.snapshot('public')
    if kind != 'sport' or not sport or not public:
        raise ValueError('Diferenciar requiere elegir Mercado y disponer de mercado y popularidad descargados.')
    alpha = differentiation / 10

    def weights(p, q):
        logs = [math.log(v) - alpha * math.log(max(crowd, 1e-6)) if v > 0 else -math.inf for v, crowd in zip(p, q)]
        peak = max(logs)
        raw = [math.exp(value - peak) for value in logs]
        return tuple(value / sum(raw) for value in raw)

    values = tuple(weights(p, q) for p, q in zip(sport.values, public.values))
    pleno = sport.pleno_values
    if sport.pleno_values and public.pleno_values:
        pleno = tuple(weights(p, q) for p, q in zip(sport.pleno_values, public.pleno_values))
    return SelectionWeights(values, pleno, f'Pesos originales mercado/popularidad · nivel {differentiation}/10; no probabilidades')
