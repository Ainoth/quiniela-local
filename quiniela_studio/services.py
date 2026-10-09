"""Casos de uso: ninguna dependencia de widgets ni red."""
from dataclasses import replace
import json
import uuid
from .domain import SystemVersion, normalize_base, utcnow, round_dict, round_from_dict
from .engine import coverage_template, optimize, union_base


class SystemService:
    def __init__(self, repository):
        self.repository = repository

    def new(self, round_, name='Mi quiniela'):
        system = SystemVersion(str(uuid.uuid4()), 1, round_.key, name,
                               ('1',) * 14, (False,) * 14, '', (), utcnow(), round_snapshot=json.dumps(round_dict(round_)))
        self.repository.save(system, 'create')
        return system

    def _editable(self, system):
        round_ = self.repository.round(system.round_key)
        if not round_.editable:
            raise ValueError('Jornada de consulta: solo puedes importar para revisar o duplicar en simulación.')
        return round_

    def version(self, system, *, allow_review=False, action='edit', **changes):
        if not allow_review:
            self._editable(system)
        revision = self.repository.load(system.system_id).revision + 1
        updated = replace(system, revision=revision, created_at=utcnow(), **changes)
        self.repository.save(updated, action)
        return updated

    def edit(self, system, base, locks, pleno):
        normalized = normalize_base(base)
        if any(system.locks[i] and normalized[i] != system.base[i] for i in range(14)):
            raise ValueError('Desbloquea el partido antes de cambiar sus signos.')
        return self.version(system, base=normalized, locks=tuple(locks), pleno=pleno, bets=(), origin='manual')

    def template(self, system, level, kind='sport'):
        round_ = self._editable(system)
        frozen = round_from_dict(json.loads(system.round_snapshot)) if system.round_snapshot else round_
        snapshot = frozen.snapshot(kind)
        base = coverage_template(system.base, system.locks, level, snapshot)
        return self.version(system, base=base, bets=(), origin=f'plantilla nivel {level}',
                            parameters=json.dumps(dict(level=level, source=snapshot.source if snapshot else 'orden 1/X/2 sin modelo', kind=kind)))

    def generated(self, system, bets):
        self._editable(system)
        # Si la UI cambió el sistema durante el cálculo, nunca aplicar un resultado obsoleto.
        if self.repository.load(system.system_id).revision != system.revision:
            raise ValueError('El sistema cambió durante la generación. El resultado no se ha aplicado.')
        return self.version(system, bets=tuple(bets), origin='desarrollo cartesiano exacto',
                            parameters=json.dumps(dict(base=system.base, pleno=system.pleno)))

    def optimized(self, system, budget_cents, kind='sport'):
        round_ = self._editable(system)
        if not system.bets:
            raise ValueError('Genera o importa un desarrollo antes de optimizarlo.')
        frozen = round_from_dict(json.loads(system.round_snapshot)) if system.round_snapshot else round_
        if kind not in ('sport', 'public'): raise ValueError('Tipo de fuente desconocido.')
        snapshot = frozen.snapshot(kind)
        if kind == 'public' and snapshot is None: raise ValueError('No hay porcentajes jugados congelados en este sistema.')
        bets = optimize(system.bets, budget_cents, frozen.price_cents, snapshot)
        if not bets:
            raise ValueError('El presupuesto no permite conservar una apuesta.')
        # Unión descriptiva: se conservan exactamente las apuestas seleccionadas.
        union = union_base(bets, system.base)
        base = tuple(system.base[i] if system.locks[i] else union[i] for i in range(14))
        return self.version(system, bets=bets, base=base, origin='selección del desarrollo de origen',
                            parameters=json.dumps(dict(input_hash=system.hash, input_revision=system.revision,
                                                       budget_cents=budget_cents, ranking=kind if snapshot else 'lexicográfico')))

    def refresh_sources(self, system):
        """Adopta fuentes actualizadas mediante versión explícita sin cambiar apuestas/precio."""
        current = self._editable(system)
        frozen = round_from_dict(json.loads(system.round_snapshot)) if system.round_snapshot else current
        if tuple((m.home_id, m.away_id) for m in frozen.matches) != tuple((m.home_id, m.away_id) for m in current.matches):
            raise ValueError('Los equipos han cambiado. Crea un sistema nuevo para revisarlos.')
        updated = replace(current, price_cents=frozen.price_cents, rules_version=frozen.rules_version)
        return self.version(system, round_snapshot=json.dumps(round_dict(updated)),
                            origin='actualización explícita de fuentes; apuestas y precio conservados', action='refresh_sources')

    def filtered(self, system, spec):
        self._editable(system)
        if not system.bets: raise ValueError('Genera o importa apuestas antes de aplicar filtros.')
        bets = spec.apply(system.bets)
        if not bets: raise ValueError('Los filtros eliminarían todas las apuestas. El sistema anterior se conserva.')
        union = union_base(bets, system.base)
        base = tuple(system.base[i] if system.locks[i] else union[i] for i in range(14))
        return self.version(system, bets=bets, base=base, origin='filtros básicos de Quiniela Local', action='filter',
                            parameters=json.dumps(dict(input_revision=system.revision, input_hash=system.hash,
                                                       filter_spec=spec.parameters(), input_quantity=system.quantity,
                                                       output_quantity=sum(b.quantity for b in bets))))

    def restore_origin(self, system):
        self._editable(system)
        source = system
        while True:
            parameters = json.loads(source.parameters)
            previous = parameters.get('input_revision')
            if previous is None or previous >= source.revision: break
            source = self.repository.load(system.system_id, previous)
        legacy = json.loads(source.parameters).get('legacy_parameters', {})
        if legacy.get('original'):
            from .domain import Bet
            bets = tuple(Bet(column, legacy.get('pleno', '').replace('-', '')) for column in legacy['original'])
        else:
            bets = source.bets
        if not bets: raise ValueError('No hay un desarrollo de origen disponible en esta versión.')
        union = union_base(bets, system.base)
        base = tuple(system.base[i] if system.locks[i] else union[i] for i in range(14))
        return self.version(system, bets=bets, base=base, origin=f'desarrollo original de v{source.revision}', action='restore_origin')

    def undo(self, system):
        if system.revision <= 1:
            raise ValueError('No existe una versión anterior.')
        previous = self.repository.load(system.system_id, system.revision - 1)
        return self.version(system, base=previous.base, locks=previous.locks, pleno=previous.pleno,
                            bets=previous.bets, origin=f'restauración v{previous.revision}', action='undo')

    def imported(self, round_, name, bets):
        # Importación de revisión permitida en jornadas históricas; no edita sistemas existentes.
        system = SystemVersion(str(uuid.uuid4()), 1, round_.key, name,
                               union_base(bets, ('1',) * 14), (False,) * 14,
                               bets[0].pleno if len({b.pleno for b in bets}) == 1 else '',
                               tuple(bets), utcnow(), 'archivo importado', round_snapshot=json.dumps(round_dict(round_)))
        self.repository.save(system, 'import')
        return system

    def duplicate(self, system):
        duplicate = replace(system, system_id=str(uuid.uuid4()), revision=1,
                            name=system.name + ' · copia', created_at=utcnow(), origin=f'copia de {system.system_id} v{system.revision}')
        self.repository.save(duplicate, 'duplicate')
        return duplicate
