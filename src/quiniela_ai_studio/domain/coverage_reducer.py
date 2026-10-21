"""Reductor propio de cobertura (Hermes/Atenea/Artemisa), independiente de Qt."""

from __future__ import annotations

import itertools
import math
import time
from dataclasses import dataclass

from .coverage import make_universe, verify_coverage
from .engine import Cancelled
from .models import Bet

ALGORITHM_VERSION = 'athena-cover-1.0.0'
EXACT_SUBSET_LIMIT = 100_000


@dataclass(frozen=True)
class CoverageReductionConfig:
    minimum_hits: int
    budget_cents: int
    price_cents: int
    method: str = 'hermes'
    seed: int = 0
    max_seconds: float = 10.0
    scenario_limit: int = 100_000
    candidate_limit: int = 1_000

    def __post_init__(self):
        if type(self.minimum_hits) is not int or not 10 <= self.minimum_hits <= 14:
            raise ValueError('El objetivo debe estar entre 10 y 14 aciertos.')
        if type(self.budget_cents) is not int or self.budget_cents < 0 or type(self.price_cents) is not int or self.price_cents <= 0:
            raise ValueError('Presupuesto y precio deben ser válidos.')
        if self.method not in ('hermes', 'athena', 'artemisa'):
            raise ValueError('Método Atenea desconocido.')
        if type(self.seed) is not int or type(self.scenario_limit) is not int or not 1 <= self.scenario_limit <= 250_000:
            raise ValueError('Semilla o límite de escenarios no válido.')
        if type(self.candidate_limit) is not int or not 1 <= self.candidate_limit <= 5_000:
            raise ValueError('El límite de candidatas debe estar entre 1 y 5.000.')
        if isinstance(self.max_seconds, bool) or not isinstance(self.max_seconds, (int, float)) or not math.isfinite(self.max_seconds) or not .1 <= self.max_seconds <= 300:
            raise ValueError('El tiempo debe estar entre 0,1 y 300 segundos.')


@dataclass(frozen=True)
class CoverageReductionResult:
    bets: tuple[Bet, ...]
    report: dict


def reduce_coverage(bets, base, config: CoverageReductionConfig, *, sport=None,
                    cancelled=lambda: False, progress=lambda done, total: None) -> CoverageReductionResult:
    """Maximiza cobertura de >=k dentro del desarrollo de origen.

    La verificación final recorre el universo independientemente de los bitsets
    de búsqueda. ``exact`` solo es verdadero si la enumeración del universo se
    completó; ``optimal`` solo para Artemisa si completó todas las combinaciones.
    """
    started=time.monotonic();deadline=started+config.max_seconds
    all_candidates=tuple(Bet(column,pleno) for column,pleno in sorted({(b.column,b.pleno) for b in bets}))
    # If the source is too large, take deterministic evenly spaced candidates
    # instead of the lexicographically earliest prefix (which is highly biased).
    if len(all_candidates)>config.candidate_limit:
        last=len(all_candidates)-1
        indices=tuple((i*last)//(config.candidate_limit-1) for i in range(config.candidate_limit)) if config.candidate_limit>1 else (0,)
        candidates=tuple(all_candidates[i] for i in indices)
    else:candidates=all_candidates
    if not candidates:raise ValueError('No hay apuestas candidatas. Genera o recupera apuestas antes de reducir.')
    maximum=min(len(candidates),config.budget_cents//config.price_cents)
    if maximum<1:raise ValueError('El presupuesto no alcanza para una apuesta.')
    universe=make_universe(base,sport,limit=config.scenario_limit,seed=config.seed)
    outcomes=universe.outcomes;target_mask=(1<<len(outcomes))-1
    masks=[];timed_out=False
    total=len(candidates)*len(outcomes)
    done=0
    for bet in candidates:
        mask=0
        complete=True
        for index,outcome in enumerate(outcomes):
            if done%8192==0:
                if cancelled():raise Cancelled('Reducción cancelada; se conservan las apuestas anteriores.')
                if time.monotonic()>=deadline:
                    complete=False;timed_out=True;break
                progress(done,total)
            if sum(a==b for a,b in zip(bet.column,outcome))>=config.minimum_hits:
                mask|=1<<index
            done+=1
        if complete:masks.append(mask)
        else:break
    candidates=candidates[:len(masks)]
    if not candidates:raise ValueError('El tiempo no permitió preparar candidatas; aumenta el límite de búsqueda.')
    selected=[];covered=0;optimal=False;search_complete=False;exact_search_skipped=False
    if config.method=='artemisa':
        subset_count=sum(math.comb(len(candidates),k) for k in range(1,min(maximum,len(candidates))+1))
        if subset_count<=EXACT_SUBSET_LIMIT:
            best_mask=0;best_indices=();best_count=-1
            for size in range(1,min(maximum,len(candidates))+1):
                for indices in itertools.combinations(range(len(candidates)),size):
                    if cancelled():raise Cancelled('Búsqueda exacta cancelada; se conservan las apuestas anteriores.')
                    if time.monotonic()>=deadline:
                        timed_out=True;break
                    union=0
                    for index in indices:union|=masks[index]
                    value=union.bit_count()
                    if value>best_count:
                        best_count=value;best_mask=union;best_indices=indices
                    if union==target_mask:
                        best_mask=union;best_indices=indices;best_count=value;break
                if timed_out or best_mask==target_mask:break
            search_complete=not timed_out
            optimal=search_complete
            selected=list(best_indices);covered=best_mask
        else:
            exact_search_skipped=True
    if not selected:
        available=set(range(len(candidates)))
        while available and len(selected)<maximum:
            if cancelled():raise Cancelled('Reducción cancelada; se conservan las apuestas anteriores.')
            if time.monotonic()>=deadline:timed_out=True;break
            best=max(available,key=lambda i:((masks[i]&~covered).bit_count(),-i))
            gain=(masks[best]&~covered).bit_count()
            if gain==0:break
            selected.append(best);available.remove(best);covered|=masks[best]
            progress(len(selected),maximum)
        if config.method in ('athena','artemisa') and selected and not timed_out:
            # Reemplazos 1:1 conservan presupuesto y mejoran la cobertura.
            changed=True
            while changed and time.monotonic()<deadline:
                changed=False
                for old in tuple(selected):
                    base_mask=0
                    for index in selected:
                        if index!=old:base_mask|=masks[index]
                    for new in range(len(candidates)):
                        if new in selected:continue
                        proposal=base_mask|masks[new]
                        if proposal.bit_count()>covered.bit_count():
                            selected[selected.index(old)]=new;covered=proposal;changed=True;break
                    if changed:break
            # Elimina apuestas redundantes tras lograr la misma cobertura.
            for index in tuple(reversed(selected)):
                remaining=0
                for other in selected:
                    if other!=index:remaining|=masks[other]
                if remaining==covered:
                    selected.remove(index)
    if not selected:
        raise ValueError('No hay una apuesta que cubra resultados del universo elegido.')
    selected_bets=tuple(candidates[index] for index in selected)
    verified=verify_coverage(selected_bets,universe,cancelled=cancelled)
    exact_universe=bool(universe.exact)
    exact_search=bool(optimal and config.method=='artemisa')
    label={'hermes':'Hermes · greedy marginal','athena':'Atenea · greedy + intercambios','artemisa':'Artemisa · búsqueda exacta acotada'}[config.method]
    report={
        'algorithm':ALGORITHM_VERSION,'method':label,'target_hits':config.minimum_hits,
        'budget_cents':config.budget_cents,'price_cents':config.price_cents,
        'count':len(selected_bets),'cost_cents':len(selected_bets)*config.price_cents,
        'candidate_count':len(candidates),'input_candidate_count':len(all_candidates),'universe_total':universe.total,
        'scenarios':len(universe.outcomes),'universe_exact':exact_universe,
        'search_optimal':exact_search,'search_complete':search_complete,'exact_search_skipped':exact_search_skipped,
        'timed_out':timed_out,'coverage':verified,
        'guarantee':bool(exact_universe and verified['minimum_hits']>=config.minimum_hits),
        'seed':config.seed,'duration_seconds':time.monotonic()-started,
        'warning':'Cobertura condicional de 14 signos dentro del universo indicado; no predice la jornada ni el Pleno al 15.',
    }
    return CoverageReductionResult(selected_bets,report)
