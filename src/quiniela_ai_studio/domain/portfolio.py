"""Carteras verificables: exhaustivo acotado, ganancia marginal e intercambio."""
import math
import random
import time
from array import array
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
        if not math.isfinite(self.max_seconds) or not .01 <= self.max_seconds <= 300:
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


def normalized_percentages(rows):
    """Acepta fracciones o porcentajes homogéneos por fila; normaliza redondeo ±1%."""
    if len(rows)!=14:
        raise ValueError('Se requieren 14 filas de porcentajes.')
    result=[]
    for row in rows:
        if len(row)!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in row):
            raise ValueError('Porcentajes no válidos.')
        total=sum(row)
        if not (.99<=total<=1.01 or 99<=total<=101):
            raise ValueError('Cada fila debe sumar 1 o 100; no se corrigen datos arbitrarios.')
        result.append(tuple(v/total for v in row))
    return tuple(result)


def probabilities_from_odds(rows):
    """Retirada proporcional del margen: método aproximado, no calibración."""
    if len(rows)!=14 or any(len(row)!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=1 for v in row) for row in rows):
        raise ValueError('14 filas de cuotas decimales >1 requeridas.')
    return tuple(tuple((1/v)/sum(1/o for o in row) for v in row) for row in rows)


def optimize_portfolio(bets, base, config: OptimizationConfig, sport=None, *, public=None,
                       eligible=lambda bet: True, cancelled=lambda: False, progress=lambda done,total: None):
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
    def probability(b):
        if not sport:return None
        value=math.exp(log_probability(b.column,sport))
        return value*pleno_model[b.pleno] if pleno_model else value
    full_probabilities={b:probability(b) for b in candidates}
    mass_keys=(lambda b:(b.column,b.pleno)) if pleno_model else (lambda b:b.column)
    def mass(selected):
        if not sport:return None
        seen=set();total=0.0
        for b in selected:
            key=mass_keys(b)
            if key not in seen:total+=full_probabilities[b];seen.add(key)
        return total
    ranked=tuple(sorted(candidates,key=lambda b:(-(full_probabilities[b] or 0),b.column,b.pleno)))
    pool=candidates
    if len(pool)>config.candidate_limit:
        first=ranked[:config.candidate_limit//2]
        rest=tuple(b for b in pool if b not in set(first))
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
    domain_mass=mass(candidates) or 1.0
    def profile(selected):
        best=[0]*m
        for b in selected:
            for i,hits in enumerate(cache[b.column]):
                if hits>best[i]:best[i]=hits
        cov={k:math.fsum(w for h,w in zip(best,weights) if h>=k) for k in THRESHOLDS}
        return cov
    def score(selected):
        if not selected:return 0.0
        p=mass(selected)
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
                            if value>best_score+1e-12:best_score=value;selected=list(subset)
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
                            peers.sort(key=lambda c:(-(full_probabilities[c] or 0),c.column))
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
    baselines={}
    reference_count=len(selected)
    def reference_selection(ordered):
        chosen=[]
        for b in ordered:
            if b in chosen:continue
            action=[b]
            if config.min_per_pleno>1 and not any(c.pleno==b.pleno for c in chosen):
                peers=[c for c in ordered if c.pleno==b.pleno and c!=b and c not in chosen]
                if len(peers)<config.min_per_pleno-1:continue
                action.extend(peers[:config.min_per_pleno-1])
            if len(chosen)+len(action)<=reference_count:chosen.extend(action)
            if len(chosen)==reference_count:break
        return tuple(chosen)
    previous=reference_selection(tuple(dict.fromkeys(Bet(b.column,b.pleno) for b in admitted)))
    shuffled=list(candidates);random.Random(config.seed).shuffle(shuffled)
    random_reference=reference_selection(shuffled)
    for name,reference in (('anterior_recortada',previous),('v0.1.13_probables',reference_selection(ranked)),('aleatoria',random_reference)):
        value=verify_coverage(reference,universe,cancelled=cancelled)
        value['probability_mass']=mass(reference)
        value['cost_cents']=len(reference)*config.price_cents
        value['channel_feasible']=feasible(reference)
        cov=value['weighted'] or value['uniform']
        value['objective_score']=(value['probability_mass'] or 0) if config.objective=='probability' else (.7*cov['13']+.3*cov['12'] if config.objective=='coverage' else .45*cov['13']+.25*cov['12']+.25*((value['probability_mass']/domain_mass) if value['probability_mass'] is not None else cov['14'])+.05*value['mean_distance']/14)
        baselines[name]=value
    before=verify_coverage(candidates,universe,cancelled=cancelled)
    before['probability_mass']=mass(candidates)
    marginal=[];prior=[]
    for b in selected:
        a=profile(prior);z=profile(prior+[b])
        marginal.append(dict(column=b.column,pleno=b.pleno,gain_13=z[13]-a[13],gain_12=z[12]-a[12],
                             probability_gain=(mass(prior+[b]) or 0)-(mass(prior) or 0)))
        prior.append(b)
    cost=len(selected)*config.price_cents
    if len(selected)<maximum:warnings.append('No se utilizan todos los huecos: eventos redundantes o mínimo por Pleno impiden aportar una apuesta válida adicional.')
    initial_plenos={b.pleno for b in candidates};final_plenos={b.pleno for b in selected}
    if initial_plenos!=final_plenos:warnings.append('La selección excluye algunas parejas del Pleno inicial; ninguna apuesta ha cambiado de Pleno. Revísalo antes de aplicar.')
    report=dict(algorithm_version=ALGORITHM_VERSION,config=asdict(config),algorithm=algorithm,
                optimality=('óptimo global para el objetivo y candidatas' if universe.exact or config.objective=='probability' else 'óptimo sobre muestra; cobertura real no certificada') if optimal else 'aproximación; no óptimo global demostrado',
                objective_score=score(selected),time_limit_reached=timed_out,initial_quantity=sum(b.quantity for b in all_bets),
                rejected_by_conditions=sum(b.quantity for b in all_bets)-sum(b.quantity for b in admitted),
                candidates=len(candidates),pool=len(pool),selected=len(selected),cost_cents=cost,
                remaining_cents=config.budget_cents-cost,before=before,after=metrics,comparisons=baselines,marginal=marginal,
                elapsed_seconds=time.monotonic()-started,warnings=warnings,
                source=sport.source if sport else None,public_source=public.source if public else None,
                probability_model='independencia de 14 encuentros'+(' y goles del Pleno' if pleno_model else '; Pleno no incluido en la masa'),
                expected_value=None,expected_value_reason='Sin recaudación/reparto/modelo de acertantes fiable')
    return OptimizationResult(selected,report)
