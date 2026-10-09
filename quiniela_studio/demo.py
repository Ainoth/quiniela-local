from .domain import Round, Match, ProbabilitySnapshot, utcnow


def demo_round():
    captured = utcnow()
    # Datos sintéticos explícitos para probar sin conexión ni apuestas reales.
    matches = tuple(Match(i, f'Equipo local {i}', f'Equipo visitante {i}', 'Demostración',
                          f'demo:home:{i}', f'demo:away:{i}') for i in range(1, 16))
    sport = ProbabilitySnapshot('sport', 'Modelo sintético de demostración; no entrenado', captured,
                                tuple((.5, .3, .2) for _ in range(14)), 'demo-1')
    public = ProbabilitySnapshot('public', 'Público sintético; no descargado', captured,
                                 tuple((.6, .25, .15) for _ in range(14)))
    return Round('DEMO', 1, matches, 'simulation', 'Ejemplo sintético incluido', captured, 75, (sport, public), 'demo-precio-75c')
