"""Reglas matemáticas reutilizables para las pestañas de Reducciones.

Las semánticas de patrones son propias: ventanas consecutivas solapadas sobre
las posiciones elegidas. No pretenden reproducir reglas internas de WIN1X2.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from itertools import pairwise
from typing import Any

RULE_KINDS = frozenset({
    'count_sign', 'longest_run', 'pattern_occurrences', 'changes',
    'max_gap', 'reference_hits', 'equal_pairs', 'weighted_sum',
    'weighted_log_probability', 'hit_frequency', 'allowed_count',
    'allowed_run_length', 'run_frequency', 'allowed_run_count',
    'allowed_run_figure', 'allowed_profile',
    'allowed_interruption_profile', 'allowed_interruption_figure', 'allowed_interruption_total',
    'allowed_sign_distance',
})


@dataclass(frozen=True)
class ReductionRule:
    """Una condición de intervalo inclusivo con alcance y parámetros explícitos."""

    rule_id: str
    kind: str
    minimum: float
    maximum: float
    positions: tuple[int, ...] = tuple(range(14))
    sign: str = ''
    pattern: str = ''
    reference: str = ''
    groups: tuple[tuple[int, ...], ...] = ()
    patterns: tuple[str, ...] = ()
    weights: tuple[tuple[float, float, float], ...] = ()
    references: tuple[str, ...] = ()
    reference_minimum: int = 0
    reference_maximum: int = 14
    allowed_values: tuple[int, ...] = ()
    run_length: int = 0
    run_minimum_enabled: bool | None = None
    run_maximum_enabled: bool | None = None
    allowed_figures: tuple[str, ...] = ()
    run_limits: tuple[tuple[int, int, int], ...] = ()
    profile_kind: str = ''
    allowed_profiles: tuple[tuple[int, ...], ...] = ()
    generation_method: str = ''
    generation_seed: int | None = None
    generation_risk: str = ''
    evidence_source: str = ''
    evidence_seasons: tuple[str, ...] = ()
    evidence_sample_size: int = 0
    evidence_coverage: float = 0.0
    active: bool = True
    tab_index: int = -1

    def __post_init__(self):
        if not self.rule_id or self.kind not in RULE_KINDS:
            raise ValueError('Regla de reducción desconocida o sin identificador.')
        if (isinstance(self.minimum, bool) or isinstance(self.maximum, bool)
                or not isinstance(self.minimum, (int, float))
                or not isinstance(self.maximum, (int, float))
                or not math.isfinite(self.minimum) or not math.isfinite(self.maximum)
                or self.minimum > self.maximum):
            raise ValueError('El intervalo de la condición no es válido.')
        if not self.positions or len(set(self.positions)) != len(self.positions) or any(type(p) is not int or not 0 <= p < 14 for p in self.positions):
            raise ValueError('Selecciona posiciones distintas entre los partidos 1 y 14.')
        if self.kind == 'count_sign' and self.sign not in ('1', 'X', '2', 'V'):
            raise ValueError('El recuento debe ser de 1, X, 2 o variantes.')
        if self.kind == 'longest_run' and self.sign not in ('1', 'X', '2', 'V'):
            raise ValueError('La racha debe ser de 1, X, 2 o variantes.')
        if self.kind == 'longest_run' and any(value is not None and type(value) is not bool
                                              for value in (self.run_minimum_enabled,self.run_maximum_enabled)):
            raise ValueError('La presencia de los límites manuales debe indicarse con valores booleanos.')
        if self.kind in ('allowed_count', 'allowed_run_length', 'allowed_run_count'):
            if self.sign not in ('1', 'X', '2', 'V'):
                raise ValueError('Selecciona 1, X, 2 o variantes.')
            if not self.allowed_values or tuple(sorted(set(self.allowed_values))) != self.allowed_values:
                raise ValueError('Selecciona al menos un valor permitido, sin duplicados.')
            if any(type(value) is not int or not 0 <= value <= len(self.positions) for value in self.allowed_values):
                raise ValueError('Hay un valor permitido fuera del número de partidos.')
            if self.kind == 'allowed_run_count' and (type(self.run_length) is not int or not 1 <= self.run_length <= len(self.positions)):
                raise ValueError('La longitud de racha exacta debe estar entre 1 y 14.')
        if self.kind == 'allowed_run_figure':
            if self.sign not in ('1', 'X', '2', 'V') or (not self.allowed_figures and self.active):
                raise ValueError('Una figura activa necesita el signo y al menos una partición permitida.')
            for figure in self.allowed_figures:
                parts=figure.split('-') if figure else []
                if any(not part.isdigit() or int(part) < 1 for part in parts):
                    raise ValueError('La figura debe ser una partición de longitudes positivas.')
                lengths=tuple(int(part) for part in parts)
                if sum(lengths)>len(self.positions) or lengths!=tuple(sorted(lengths,reverse=True)):
                    raise ValueError('La figura de racha no es una partición válida de hasta 14 partidos.')
                if self.tab_index==17 and sum(lengths)!=self.run_length:
                    raise ValueError('La figura de FSSeguidos debe sumar el total seleccionado.')
            if self.tab_index==17 and (type(self.run_length) is not int or not 0 <= self.run_length <= 14):
                raise ValueError('El total de FSSeguidos debe estar entre 0 y 14.')
        if self.kind == 'allowed_interruption_profile':
            if (self.tab_index!=18 or self.profile_kind!='interruptions' or not self.allowed_profiles
                    or self.positions!=tuple(range(14))):
                raise ValueError('La matriz de Interrupciones necesita perfiles activos en la pestaña correcta.')
            if tuple(sorted(set(self.allowed_profiles)))!=self.allowed_profiles:
                raise ValueError('Los pares de Interrupciones deben ser únicos y estar ordenados.')
            if any(len(profile)!=2 or any(type(value) is not int or not 0<=value<=13 for value in profile)
                   or profile[1]>profile[0] or (profile[0]==0 and profile[1]!=0)
                   for profile in self.allowed_profiles):
                raise ValueError('La matriz permite pares (total, racha) coherentes entre 0 y 13.')
        if self.kind == 'allowed_interruption_figure':
            if self.tab_index!=18 or self.positions!=tuple(range(14)) or type(self.run_length) is not int or not 0<=self.run_length<=13:
                raise ValueError('El total de la figura de interrupciones debe estar entre 0 y 13.')
            if not self.allowed_figures and self.active:
                raise ValueError('Una figura activa necesita al menos una distribución permitida.')
            for figure in self.allowed_figures:
                parts=tuple(int(part) for part in figure.split('-')) if figure else ()
                if (any(not part.isdigit() or int(part)<1 for part in figure.split('-')) if figure else False
                        or sum(parts)!=self.run_length or parts!=tuple(sorted(parts,reverse=True))):
                    raise ValueError('La figura de interrupciones debe sumar su total y estar ordenada.')
        if (self.kind == 'allowed_interruption_total'
                and (self.tab_index!=18 or self.positions!=tuple(range(14)) or not self.allowed_values
                     or tuple(sorted(set(self.allowed_values)))!=self.allowed_values
                     or any(type(value) is not int or not 0<=value<=13 for value in self.allowed_values))):
            raise ValueError('Los totales de Interrupciones deben estar entre 0 y 13.')
        if (self.kind == 'allowed_sign_distance'
                and (self.tab_index != 18 or self.positions != tuple(range(14))
                     or self.sign not in ('1', 'X', '2', 'V') or not self.allowed_values
                     or tuple(sorted(set(self.allowed_values))) != self.allowed_values
                     or any(type(value) is not int or not 0 <= value <= 13
                            for value in self.allowed_values))):
            raise ValueError('La distancia máxima necesita valores distintos entre 0 y 13.')
        if self.kind == 'run_frequency':
            if self.sign not in ('1', 'X', '2', 'V') or not self.run_limits:
                raise ValueError('Selecciona el signo y al menos una figura de racha.')
            if any(type(length) is not int or not 1 <= length <= len(self.positions)
                   or type(low) is not int or type(high) is not int or not 0 <= low <= high <= 14
                   for length, low, high in self.run_limits):
                raise ValueError('Los límites de figuras de racha no son válidos.')
        if self.kind == 'allowed_profile':
            width=3 if self.profile_kind=='counts' else 60 if self.profile_kind=='streaks' else 0
            if self.profile_kind=='interruptions':
                width=2
            if not width or not self.allowed_profiles or any(len(profile)!=width for profile in self.allowed_profiles):
                raise ValueError('El perfil conjunto de condiciones no es válido.')
            maximum=13 if self.profile_kind=='interruptions' else 14
            if any(type(value) is not int or not 0 <= value <= maximum for profile in self.allowed_profiles for value in profile):
                raise ValueError('El perfil contiene un valor fuera de 0–14.')
            if self.profile_kind=='counts' and any(
                profile[0]!=profile[1]+profile[2] or profile[1]+profile[2]>14
                for profile in self.allowed_profiles
            ):
                raise ValueError('El perfil Cuenta debe cumplir V = X + 2 en catorce partidos.')
            if self.evidence_sample_size < 0 or not math.isfinite(self.evidence_coverage) or not 0 <= self.evidence_coverage <= 1:
                raise ValueError('La procedencia estadística del perfil no es válida.')
        if type(self.active) is not bool or type(self.tab_index) is not int or not -1 <= self.tab_index < 19:
            raise ValueError('La activación de la condición no es válida.')
        if self.kind == 'pattern_occurrences':
            if not self.patterns or any(not p or any(s not in '1X2' for s in p) for p in self.patterns):
                raise ValueError('Indica al menos un patrón formado por 1, X o 2.')
            if any(len(p) > len(self.positions) for p in self.patterns):
                raise ValueError('El patrón es más largo que las posiciones elegidas.')
        if self.kind == 'reference_hits':
            _validate_column(self.reference)
        if self.kind == 'equal_pairs':
            if not self.groups or any(len(pair) != 2 or pair[0] == pair[1] for pair in self.groups):
                raise ValueError('Cada coincidencia necesita dos partidos distintos.')
            if any(any(type(p) is not int or not 0 <= p < 14 for p in pair) for pair in self.groups):
                raise ValueError('Partido fuera del rango 1–14.')
        if self.kind in ('weighted_sum', 'weighted_log_probability'):
            if len(self.weights) != 14 or any(len(row) != 3 or any(not math.isfinite(v) or v < 0 for v in row) for row in self.weights):
                raise ValueError('Se necesitan 14 filas de probabilidades válidas.')
            if any(not math.isclose(sum(row), 1.0, abs_tol=0.02) for row in self.weights):
                raise ValueError('Cada fila debe sumar aproximadamente 100 %.')
        if self.kind == 'hit_frequency':
            if not self.references:
                raise ValueError('Añade al menos una columna de referencia.')
            if not 0 <= self.reference_minimum <= self.reference_maximum <= len(self.positions):
                raise ValueError('El intervalo de aciertos por referencia no es válido.')
            for reference in self.references:
                _validate_column(reference)

    def measure(self, column: str) -> float:
        """Devuelve el valor exacto de la condición para una columna de 14 signos."""
        _validate_column(column)
        values = [column[i] for i in self.positions]
        if self.kind == 'count_sign':
            return float(sum((s != '1') if self.sign == 'V' else (s == self.sign) for s in values))
        if self.kind == 'allowed_count':
            return float(sum((s != '1') if self.sign == 'V' else (s == self.sign) for s in values))
        if self.kind == 'allowed_run_length':
            return float(_run_lengths(values, self.sign)[0])
        if self.kind == 'allowed_run_count':
            return float(_run_lengths(values, self.sign)[1].get(self.run_length, 0))
        if self.kind == 'allowed_run_figure':
            counts = _run_lengths(values, self.sign)[1]
            figure = '-'.join(str(length) for length in sorted(
                (length for length, amount in counts.items() for _ in range(amount)), reverse=True
            ))
            return float(figure in self.allowed_figures)
        if self.kind in ('allowed_interruption_profile','allowed_interruption_figure','allowed_interruption_total'):
            from quiniela_ai_studio.domain.interruption_statistics import (
                interruption_profile,
            )
            total,longest,figure=interruption_profile(''.join(values))
            if self.kind=='allowed_interruption_profile':
                return 1.0 if (total,longest) in self.allowed_profiles else 0.0
            if self.kind=='allowed_interruption_total':
                return float(total)
            return 1.0 if total==self.run_length and figure in self.allowed_figures else 0.0
        if self.kind == 'allowed_sign_distance':
            from quiniela_ai_studio.domain.sign_distance import maximum_sign_distance
            return float(maximum_sign_distance(column, self.sign))
        if self.kind == 'run_frequency':
            runs = _run_lengths(values, self.sign)[1]
            return float(sum(low <= runs.get(length, 0) <= high for length, low, high in self.run_limits))
        if self.kind == 'allowed_profile':
            return 1.0 if self._profile(values) in self.allowed_profiles else 0.0
        if self.kind == 'longest_run':
            longest = current = 0
            for sign in values:
                matches = sign != '1' if self.sign == 'V' else sign == self.sign
                current = current + 1 if matches else 0
                longest = max(longest, current)
            return float(longest)
        if self.kind == 'pattern_occurrences':
            return float(sum(
                any(''.join(values[start:start + len(pattern)]) == pattern for pattern in self.patterns)
                for start in range(len(values))
                if start + min(map(len, self.patterns)) <= len(values)
            ))
        if self.kind == 'changes':
            return float(sum(a != b for a, b in pairwise(values)))
        if self.kind == 'max_gap':
            occurrences = [i for i, value in enumerate(values) if value == self.sign]
            return float(max((b - a for a, b in pairwise(occurrences)), default=0))
        if self.kind == 'reference_hits':
            return float(sum(column[i] == self.reference[i] for i in self.positions))
        if self.kind == 'equal_pairs':
            return float(sum(column[a] == column[b] for a, b in self.groups))
        if self.kind == 'weighted_sum':
            return math.fsum(self.weights[i]['1X2'.index(column[i])] for i in self.positions)
        if self.kind == 'weighted_log_probability':
            probabilities = [self.weights[i]['1X2'.index(column[i])] for i in self.positions]
            return -math.inf if any(p == 0 for p in probabilities) else math.fsum(math.log(p) for p in probabilities)
        if self.kind == 'hit_frequency':
            return float(sum(
                self.reference_minimum <= sum(column[i] == reference[i] for i in self.positions) <= self.reference_maximum
                for reference in self.references
            ))
        raise AssertionError(f'Unreachable condition kind: {self.kind}')

    def accepts(self, column: str) -> bool:
        measured = self.measure(column)
        if self.kind in ('allowed_count', 'allowed_run_length', 'allowed_run_count',
                         'allowed_interruption_total', 'allowed_sign_distance'):
            return int(measured) in self.allowed_values
        if self.kind == 'allowed_run_figure':
            return measured == 1.0
        if self.kind in ('allowed_interruption_profile','allowed_interruption_figure'):
            return measured==1.0
        if self.kind == 'run_frequency':
            values = [column[i] for i in self.positions]
            runs = _run_lengths(values, self.sign)[1]
            return all(low <= runs.get(length, 0) <= high for length, low, high in self.run_limits)
        if self.kind == 'allowed_profile':
            values=[column[i] for i in self.positions]
            return self._profile(values) in self.allowed_profiles
        return self.minimum <= measured <= self.maximum

    def _profile(self, values: list[str]) -> tuple[int, ...]:
        if self.profile_kind=='counts':
            return (sum(value!='1' for value in values),sum(value=='X' for value in values),sum(value=='2' for value in values))
        if self.profile_kind=='streaks':
            longest=[]
            for sign in ('1','X','2','V'):
                longest.append(_run_lengths(values,sign)[0])
            exact_counts=[]
            for sign in ('1','X','2','V'):
                counts=_run_lengths(values,sign)[1]
                exact_counts.extend(counts.get(length,0) for length in range(1,15))
            return tuple(longest+exact_counts)
        if self.profile_kind=='interruptions':
            from quiniela_ai_studio.domain.interruption_statistics import (
                interruption_profile,
            )
            total,longest,_figure=interruption_profile(''.join(values))
            return total,longest
        raise AssertionError('Unknown profile kind')

    def parameters(self) -> dict[str, Any]:
        return asdict(self)


def _validate_column(column: str) -> None:
    if not isinstance(column, str) or len(column) != 14 or any(sign not in '1X2' for sign in column):
        raise ValueError('La referencia debe contener exactamente 14 signos 1/X/2.')


def _run_lengths(values: list[str], sign: str) -> tuple[int, dict[int, int]]:
    """Return longest maximal run and counts by exact length (no overlaps).

    V denotes the variant class, so X and 2 are adjacent members of the same
    run. This is the documented original semantics used by Cuenta/Racha.
    """
    runs: dict[int, int] = {}
    current = 0
    longest = 0
    for value in (*values, None):
        if value is None:
            matches=False
        else:
            matches = (value != '1') if sign == 'V' else value == sign
        if matches:
            current += 1
            longest = max(longest, current)
        elif current:
            runs[current] = runs.get(current, 0) + 1
            current = 0
    return longest, runs


def rules_from_parameters(rows) -> tuple[ReductionRule, ...]:
    """Lee la versión serializada y vuelve a validar todos los valores."""
    result = []
    for row in rows or ():
        values = dict(row)
        values['positions'] = tuple(values.get('positions', range(14)))
        values['groups'] = tuple(tuple(pair) for pair in values.get('groups', ()))
        values['patterns'] = tuple(values.get('patterns', ()))
        values['weights'] = tuple(tuple(float(v) for v in values_row) for values_row in values.get('weights', ()))
        values['references'] = tuple(values.get('references', ()))
        values['allowed_values'] = tuple(values.get('allowed_values', ()))
        values['allowed_figures'] = tuple(values.get('allowed_figures', ()))
        values['run_limits'] = tuple(tuple(int(v) for v in item) for item in values.get('run_limits', ()))
        values['allowed_profiles'] = tuple(tuple(int(v) for v in item) for item in values.get('allowed_profiles', ()))
        values['evidence_seasons'] = tuple(values.get('evidence_seasons', ()))
        result.append(ReductionRule(**values))
    return tuple(result)
