"""Referencia sintética reproducible: no datos/apuestas personales ni premios reales."""
import json
import platform
import time
import tracemalloc

from quiniela_ai_studio.domain.engine import generate
from quiniela_ai_studio.domain.portfolio import OptimizationConfig,optimize_portfolio
from quiniela_ai_studio.infrastructure.demo import demo_round


def main():
    base=('1X',)*3+('1X2',)*2+('1',)*9
    bets=generate(base,'M0');sport=demo_round().snapshot('sport')
    tracemalloc.start();start=time.perf_counter()
    result=optimize_portfolio(bets,base,OptimizationConfig(500,75,seed=123),sport)
    elapsed=time.perf_counter()-start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    report=result.report
    print(json.dumps(dict(fixture='SINTÉTICA: 9 fijos, 3 dobles, 2 triples; probabilidades demo 50/30/20',
        python=platform.python_version(),platform=platform.system(),architecture=platform.machine(),
        candidates=report['candidates'],selected=report['selected'],cost_cents=report['cost_cents'],remaining_cents=report['remaining_cents'],
        seconds_with_tracemalloc=elapsed,peak_bytes=peak,algorithm=report['algorithm'],optimality=report['optimality'],
        after=report['after'],reference_v013=report['comparisons']['v0.1.13_probables']),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
