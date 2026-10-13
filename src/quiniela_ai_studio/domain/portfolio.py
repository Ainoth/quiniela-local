"""Carteras verificables: exhaustivo acotado, ganancia marginal e intercambio."""
import math
import random
import time
from array import array
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from itertools import combinations

from .coverage import THRESHOLDS, diversity, make_universe, verify_coverage
from .engine import Cancelled, log_probability
from .models import Bet

ALGORITHM_VERSION = 'portfolio-1.0.0'


@dataclass(frozen=True)
class OptimizationConfig:
    budget_cents: int
    price_cents: int
    objective: str = 'auto'
    seed: int = 0
    max_seconds: float = 10.0
    scenario_limit: int = 2048
    candidate_limit: int = 256
    exhaustive_limit: int = 20000
    min_per_pleno: int = 1
    universe_scope: str = 'base'
    include_pleno_probability: bool = False

    def __post_init__(self):
        if type(self.budget_cents) is not int or self.budget_cents < 0 or type(self.price_cents) is not int or self.price_cents <= 0:
            raise ValueError('Presupuesto y precio positivos en céntimos requeridos.')
        if self.objective not in ('auto','probability','coverage','expected'):
            raise ValueError('Objetivo desconocido.')
        if not finite_number(self.max_seconds) or not .01 <= self.max_seconds <= 300:
            raise ValueError('Tiempo máximo entre 0,01 y 300 segundos.')
        if self.universe_scope not in ('base','candidates'):
            raise ValueError('Universo base o candidatas requerido.')
        if type(self.seed) is not int or any(type(v) is not int or v < 1 for v in (self.scenario_limit,self.candidate_limit,self.exhaustive_limit,self.min_per_pleno)):
            raise ValueError('Semilla entera y límites positivos requeridos.')
        if self.scenario_limit>10000 or self.candidate_limit>2048:
            raise ValueError('Límites máximos: 10.000 escenarios y 2.048 candidatas.')


@dataclass(frozen=True)
class OptimizationResult:
    bets: tuple[Bet, ...]
    report: dict


class Deadline(Exception):
    pass


def finite_number(value: object) -> bool:
    """Rechaza también enteros que desbordan la conversión interna a float."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def reference_portfolio(ordered: Iterable[Bet], count: int, minimum: int) -> tuple[Bet, ...]:
    """Referencia de cardinalidad exacta, con cuotas viables por Pleno.

    Prioriza grupos según su primera aparición y apuestas dentro del grupo
    según el orden recibido. El DP de cardinalidades evita comparaciones
    artificialmente más baratas; no pretende optimizar probabilidades.
    """
    ordered = tuple(dict.fromkeys(ordered))
    if minimum == 1:
        if len(ordered) < count:
            raise ValueError('No existe referencia válida con la misma cantidad de apuestas.')
        return ordered[:count]
    groups = {}
    for bet in dict.fromkeys(ordered):
        groups.setdefault(bet.pleno, []).append(bet)
    values = list(groups.values())
    reachable = [0] * (len(values) + 1)
    reachable[-1] = 1  # bit cero: seleccionar cero apuestas es viable.
    mask = (1 << (count + 1)) - 1
    for index in range(len(values) - 1, -1, -1):
        bits = reachable[index + 1]
        for size in range(minimum, min(count, len(values[index])) + 1):
            bits |= reachable[index + 1] << size
        reachable[index] = bits & mask
    if not (reachable[0] >> count) & 1:
        raise ValueError('No existe referencia válida con la misma cantidad de apuestas.')
    chosen = []
    remaining = count
    for index, group in enumerate(values):
        for size in list(range(min(remaining, len(group)), minimum - 1, -1)) + [0]:
            if (reachable[index + 1] >> (remaining - size)) & 1:
                chosen.extend(group[:size])
                remaining -= size
                break
    return tuple(chosen)


def normalized_percentages(rows):
    """Acepta fracciones o porcentajes homogéneos por fila; normaliza redondeo ±1%."""
    if len(rows)!=14:
        raise ValueError('Se requieren 14 filas de porcentajes.')
    result=[]
    for row in rows:
        if len(row)!=3 or any(not finite_number(v) or v<0 for v in row):
            raise ValueError('Porcentajes no válidos.')
        total=sum(row)
        if not (.99<=total<=1.01 or 99<=total<=101):
            raise ValueError('Cada fila debe sumar 1 o 100; no se corrigen datos arbitrarios.')
        result.append(tuple(v/total for v in row))
    return tuple(result)


def probabilities_from_odds(rows):
    """Retirada proporcional del margen: método aproximado, no calibración."""
    if len(rows)!=14 or any(len(row)!=3 or any(not finite_number(v) or v<=1 for v in row) for row in rows):
        raise ValueError('14 filas de cuotas decimales >1 requeridas.')
    return tuple(tuple((1/v)/sum(1/o for o in row) for v in row) for row in rows)


def optimize_portfolio(bets, base, config: OptimizationConfig, sport=None, *, public=None,
                       eligible=lambda bet: True, cancelled=lambda: False, progress=lambda done,total: None) -> OptimizationResult:
    """Selecciona apuestas únicas conservando sus Plenos. Solo certifica búsqueda completa."""
    if config.objective=='expected':
        raise ValueError('Valor esperado no disponible: faltan recaudación, reglas de reparto y modelo fiable de acertantes. Popularidad no es ROI.')
    if sport and sport.kind!='sport':raise ValueError('El público no es una probabilidad deportiva.')
    if config.objective=='probability' and not sport:raise ValueError('Máxima probabilidad requiere una fuente deportiva.')
    if cancelled():raise Cancelled('Optimización cancelada.')
    started=time.monotonic();deadline=started+config.max_seconds
    def checkpoint():
        if cancelled():raise Cancelled('Optimización cancelada; la quiniela anterior se conserva.')
        if time.monotonic()>=deadline:raise Deadline()
    all_bets=tuple(bets)
    admitted=tuple(b for b in all_bets if eligible(b))
    candidates=tuple(Bet(*key) for key in sorted({(b.column,b.pleno) for b in admitted}))
    if not candidates:raise ValueError('No hay candidatas que cumplan las condiciones.')
    if any(not b.pleno for b in candidates):raise ValueError('Completa el Pleno de todas las candidatas antes de optimizar.')
    maximum=min(len(candidates),config.budget_cents//config.price_cents)
    if maximum<config.min_per_pleno:raise ValueError('El presupuesto no permite el mínimo de apuestas del canal.')
    scenario_limit=min(config.scenario_limit,max(1,2_000_000//len(candidates)))
    universe=make_universe(base,sport,outcomes=[b.column for b in candidates] if config.universe_scope=='candidates' else None,
                           limit=scenario_limit,seed=config.seed)
    warnings=[]
    if not sport:warnings.append('Sin probabilidades deportivas: objetivo con cobertura uniforme; no se inventan probabilidades.')
    if sport and universe.weights is None:warnings.append('Masa de probabilidad nula en el universo: cobertura ponderada no disponible.')
    if not universe.exact:warnings.append('Muestreo uniforme con ponderación por importancia; no es una garantía. Revisar tamaño efectivo de muestra.')
    pleno_model=None
    if config.include_pleno_probability:
        from .coverage import pleno_joint
        pleno_model=pleno_joint(sport)
        warnings.append('Probabilidad del Pleno estimada con independencia explícita de goles local/visitante y de los 14 encuentros.')
    def event_log(b):
        value=log_probability(b.column,sport) if sport else -math.inf
        if pleno_model:
            for side,sign in enumerate(b.pleno):
                marginal=sport.pleno_values[side]['012M'.index(sign)]
                value+=math.log(marginal) if marginal>0 else -math.inf
        return value
    logs={b:event_log(b) for b in candidates}
    peak=max(logs.values())
    # Escala común positiva: preserva el objetivo incluso cuando exp(logP)
    # se redondea a cero para todas las columnas.
    relative_probabilities={b:math.exp(value-peak) if math.isfinite(peak) else 0.0 for b,value in logs.items()}
    full_probabilities={b:math.exp(value) if sport else None for b,value in logs.items()}
    if sport and any(math.isfinite(logs[b]) and full_probabilities[b]==0 for b in candidates):
        warnings.append('Probabilidades absolutas inferiores a la precisión float: pueden mostrarse como 0. La selección utiliza logaritmos y pesos reescalados, no ceros ficticios.')
    mass_keys=(lambda b:(b.column,b.pleno)) if pleno_model else (lambda b:b.column)
    def mass(selected, *, relative=False):
        if not sport:return None
        seen=set();total=0.0
        for b in selected:
            key=mass_keys(b)
            if key not in seen:total+=(relative_probabilities if relative else full_probabilities)[b];seen.add(key)
        return total
    def mass_log(selected):
        unique={mass_keys(b):logs[b] for b in selected}
        top=max(unique.values(),default=-math.inf)
        return top+math.log(math.fsum(math.exp(v-top) for v in unique.values())) if math.isfinite(top) else None
    ranked=tuple(sorted(candidates,key=lambda b:(-logs[b],b.column,b.pleno)))
    pool=candidates
    if len(pool)>config.candidate_limit:
        first=ranked[:config.candidate_limit//2]
        first_set=set(first)
        rest=tuple(b for b in pool if b not in first_set)
        sample=random.Random(config.seed).sample(rest,config.candidate_limit-len(first))
        pool=tuple(sorted(first+tuple(sample),key=lambda b:(b.column,b.pleno)))
        warnings.append(f'Cartera heurística sobre {len(pool)} candidatas de {len(candidates)}: mitad por probabilidad, mitad muestreo reproducible.')
    # Matriz compacta de aciertos, compartida por las parejas de Pleno de una columna.
    cache={};m=len(universe.outcomes)
    try:
        for i,b in enumerate(pool):
            checkpoint()
            if b.column not in cache:
                cache[b.column]=array('B',(14-sum(a!=c for a,c in zip(b.column,outcome)) for outcome in universe.outcomes))
            progress(i+1,len(pool))
    except Deadline:
        raise ValueError('El tiempo no permite preparar coberturas; aumenta el límite o reduce candidatas/escenarios. No se ha guardado nada.') from None
    weights=universe.weights or tuple(1/m for _ in range(m))
    domain_mass=mass(candidates,relative=True) or 1.0
    def profile(selected):
        best=[0]*m
        for b in selected:
            for i,hits in enumerate(cache[b.column]):
                if hits>best[i]:best[i]=hits
        cov={k:math.fsum(w for h,w in zip(best,weights) if h>=k) for k in THRESHOLDS}
        return cov
    def score(selected):
        if not selected:return 0.0
        p=mass(selected,relative=True)
        if config.objective=='probability':return p or 0
        cov=profile(selected)
        if config.objective=='coverage':return .7*cov[13]+.3*cov[12]
        return .45*cov[13]+.25*cov[12]+.25*((p/domain_mass) if p is not None else cov[14])+.05*diversity(selected)/14
    def feasible(selected):
        groups={b.pleno for b in selected}
        return all(sum(b.pleno==p for b in selected)>=config.min_per_pleno for p in groups)
    # Inicialización viable determinista, no depende del orden del fichero.
    selected=[]
    for pleno in sorted({b.pleno for b in pool}):
        group=[b for b in pool if b.pleno==pleno]
        if len(group)>=config.min_per_pleno and len(selected)+config.min_per_pleno<=maximum:
            selected.extend(group[:config.min_per_pleno])
    selected=selected[:maximum];incumbent=selected[:]
    if not selected:raise ValueError('No hay suficientes apuestas por Pleno para cumplir el mínimo del canal.')
    algorithm='greedy marginal + intercambio local';optimal=False;timed_out=False
    exhaustive_size=sum(math.comb(len(pool),count) for count in range(1,maximum+1)) if len(pool)<=30 else config.exhaustive_limit+1
    exhaustive_allowed=(len(pool)==len(candidates) and exhaustive_size<=config.exhaustive_limit
                        and exhaustive_size*maximum*m<=5_000_000)
    if config.objective=='probability' and config.min_per_pleno==1:
        # Masa aditiva sobre eventos exactos distintos: ordenación es óptima para este objetivo.
        unique={}
        for b in ranked:unique.setdefault(mass_keys(b),b)
        selected=list(unique.values())[:maximum]
        algorithm='máxima masa exacta: eventos distintos ordenados';optimal=True
    else:
        best_score=score(selected)
        try:
            if exhaustive_allowed:
                algorithm='enumeración exhaustiva de subconjuntos admisibles'
                done=0
                for count in range(1,maximum+1):
                    for subset in combinations(pool,count):
                        checkpoint()
                        if feasible(subset):
                            value=score(subset)
                            if value>best_score:best_score=value;selected=list(subset)
                        done+=1;progress(done,exhaustive_size)
                optimal=True
            else:
                selected=[]
                while len(selected)<maximum:
                    checkpoint();best_action=None;best_gain=-math.inf;current=score(selected)
                    for bi,b in enumerate(pool):
                        if bi%16==0:checkpoint()
                        if b in selected:continue
                        action=[b]
                        if config.min_per_pleno>1 and not any(c.pleno==b.pleno for c in selected):
                            peers=[c for c in pool if c.pleno==b.pleno and c!=b]
                            if len(peers)<config.min_per_pleno-1:continue
                            peers.sort(key=lambda c:(-logs[c],c.column))
                            action.extend(peers[:config.min_per_pleno-1])
                        if len(selected)+len(action)>maximum:continue
                        gain=(score(selected+action)-current)/len(action)
                        if gain>best_gain+1e-12:best_gain=gain;best_action=action
                    if not best_action or best_gain<=1e-12:break
                    selected.extend(best_action);progress(len(selected),maximum)
                if not selected:raise ValueError('No hay una cartera viable para este presupuesto/canal.')
                improved=True
                while improved:
                    improved=False;current=score(selected)
                    for index in range(len(selected)):
                        checkpoint()
                        for ci,candidate in enumerate(pool):
                            if ci%16==0:checkpoint()
                            if candidate in selected:continue
                            trial=selected[:];trial[index]=candidate
                            if feasible(trial) and (value:=score(trial))>current+1e-12:
                                selected=trial;current=value;improved=True
        except Deadline:
            timed_out=True;optimal=False
            if not selected or score(incumbent)>score(selected):selected=incumbent
            warnings.append('Límite de tiempo alcanzado; se conserva la mejor cartera completa encontrada.')
    selected=tuple(selected)
    if not feasible(selected):raise ValueError('No se obtuvo una cartera válida para el canal.')
    for b in selected:
        if b.column not in cache:
            cache[b.column]=array('B',(14-sum(a!=c for a,c in zip(b.column,outcome)) for outcome in universe.outcomes))
    # Verificación separada del motor y baselines de igual cardinalidad/presupuesto.
    metrics=verify_coverage(selected,universe,cancelled=cancelled)
    metrics['probability_mass']=mass(selected)
    metrics['probability_mass_log']=mass_log(selected) if sport else None
    baselines={}
    reference_count=len(selected)
    def reference_selection(ordered):
        return reference_portfolio(ordered, reference_count, config.min_per_pleno)
    previous=reference_selection(tuple(dict.fromkeys(Bet(b.column,b.pleno) for b in admitted)))
    shuffled=list(candidates);random.Random(config.seed).shuffle(shuffled)
    random_reference=reference_selection(shuffled)
    for name,reference in (('anterior_recortada',previous),('v0.1.13_probables',reference_selection(ranked)),('aleatoria',random_reference)):
        value=verify_coverage(reference,universe,cancelled=cancelled)
        value['probability_mass']=mass(reference)
        value['probability_mass_log']=mass_log(reference) if sport else None
        value['cost_cents']=len(reference)*config.price_cents
        value['channel_feasible']=feasible(reference)
        cov=value['weighted'] or value['uniform']
        p=mass(reference,relative=True)
        value['objective_score']=(p or 0) if config.objective=='probability' else (.7*cov['13']+.3*cov['12'] if config.objective=='coverage' else .45*cov['13']+.25*cov['12']+.25*((p/domain_mass) if p is not None else cov['14'])+.05*value['mean_distance']/14)
        baselines[name]=value
    before=verify_coverage(candidates,universe,cancelled=cancelled)
    before['probability_mass']=mass(candidates)
    before['probability_mass_log']=mass_log(candidates) if sport else None
    marginal=[];prior=[]
    for b in selected:
        a=profile(prior);z=profile(prior+[b])
        marginal.append(dict(column=b.column,pleno=b.pleno,gain_13=z[13]-a[13],gain_12=z[12]-a[12],
                             probability_gain=(mass(prior+[b]) or 0)-(mass(prior) or 0)))
        prior.append(b)
    cost=len(selected)*config.price_cents
    if len(selected)<maximum:
        reason='se alcanzó el límite de tiempo' if timed_out else 'no se encontró una ampliación con ganancia positiva que respete el mínimo por Pleno dentro de las candidatas exploradas'
        warnings.append(f'Se usan {len(selected)} de hasta {maximum} apuestas: {reason}. No se afirma que no exista otra cartera mejor.')
    initial_plenos={b.pleno for b in candidates};final_plenos={b.pleno for b in selected}
    if initial_plenos!=final_plenos:warnings.append('La selección excluye algunas parejas del Pleno inicial; ninguna apuesta ha cambiado de Pleno. Revísalo antes de aplicar.')
    report=dict(algorithm_version=ALGORITHM_VERSION,config=asdict(config),algorithm=algorithm,
                optimality=('óptimo global para el objetivo y candidatas' if universe.exact or config.objective=='probability' else 'óptimo sobre muestra; cobertura real no certificada') if optimal else 'aproximación; no óptimo global demostrado',
                objective_score=score(selected),time_limit_reached=timed_out,initial_quantity=sum(b.quantity for b in all_bets),
                probability_objective_scale='exp(logP - máximo logP de las candidatas); escala común, conserva el orden',
                rejected_by_conditions=sum(b.quantity for b in all_bets)-sum(b.quantity for b in admitted),
                candidates=len(candidates),pool=len(pool),selected=len(selected),cost_cents=cost,
                remaining_cents=config.budget_cents-cost,before=before,after=metrics,comparisons=baselines,marginal=marginal,
                elapsed_seconds=time.monotonic()-started,warnings=warnings,
                source=sport.source if sport else None,public_source=public.source if public else None,
                probability_model='independencia de 14 encuentros'+(' y goles del Pleno' if pleno_model else '; Pleno no incluido en la masa'),
                expected_value=None,expected_value_reason='Sin recaudación/reparto/modelo de acertantes fiable')
    return OptimizationResult(selected,report)
