"""Entidades inmutables. Sin Qt, red, disco ni estado global de interfaz."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, date
import hashlib
import json
import math
import re

SIGNS = "1X2"
GOALS = "012M"


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def validate_column(column):
    if not isinstance(column, str) or not re.fullmatch(r"[1X2]{14}", column):
        raise ValueError("Una columna debe tener exactamente 14 signos 1/X/2.")
    return column


def normalize_base(base):
    if len(base) != 14:
        raise ValueError("La base requiere 14 partidos.")
    if any(not isinstance(s, str) or not s or set(s) - set(SIGNS) for s in base):
        raise ValueError("Cada partido necesita al menos un signo 1/X/2.")
    return tuple("".join(s for s in SIGNS if s in allowed) for allowed in base)


@dataclass(frozen=True)
class Bet:
    column: str
    pleno: str = ""
    quantity: int = 1

    def __post_init__(self):
        validate_column(self.column)
        if self.pleno and not re.fullmatch(r"[012M]{2}", self.pleno):
            raise ValueError("El Pleno requiere dos valores 0/1/2/M.")
        if type(self.quantity) is not int or not 1 <= self.quantity <= 1_000_000:
            raise ValueError("Cantidad de apuesta no válida.")


@dataclass(frozen=True)
class Match:
    number: int
    home: str
    away: str
    kickoff: str = ""
    home_id: str = ""
    away_id: str = ""

    def __post_init__(self):
        if type(self.number) is not int or not 1 <= self.number <= 15 or not self.home or not self.away:
            raise ValueError("Partido inválido.")


@dataclass(frozen=True)
class ProbabilitySnapshot:
    kind: str
    source: str
    captured_at: str
    values: tuple
    model_version: str = ""

    def __post_init__(self):
        object.__setattr__(self, "values", tuple(tuple(row) for row in self.values))
        if self.kind not in ("sport", "public") or not self.source:
            raise ValueError("Fuente deportiva o público requerida.")
        validate_datetime(self.captured_at)
        if len(self.values) != 14:
            raise ValueError("Se requieren probabilidades para los 14 partidos.")
        for row in self.values:
            if len(row) != 3 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in row):
                raise ValueError("Probabilidades: valores finitos entre 0 y 1.")
            if not math.isclose(sum(row), 1, abs_tol=1e-6):
                raise ValueError("Las probabilidades deben sumar 1 (tolerancia 1e-6).")


def validate_datetime(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Las fechas requieren zona horaria.")
    return parsed


@dataclass(frozen=True)
class Round:
    season: str
    number: int
    matches: tuple[Match, ...]
    mode: str
    source: str
    captured_at: str
    price_cents: int = 75
    snapshots: tuple[ProbabilitySnapshot, ...] = ()
    rules_version: str = "local-v1"
    nominal_date: str = ""
    editable_until: str = ""

    def __post_init__(self):
        object.__setattr__(self, "matches", tuple(self.matches))
        object.__setattr__(self, "snapshots", tuple(self.snapshots))
        if self.nominal_date: date.fromisoformat(self.nominal_date)
        if self.editable_until: date.fromisoformat(self.editable_until)
        if not re.fullmatch(r"\d{2}-\d{2}|DEMO", self.season) or type(self.number) is not int or not 1 <= self.number <= 99:
            raise ValueError("Temporada o jornada inválida.")
        if len(self.matches) != 15 or tuple(m.number for m in self.matches) != tuple(range(1, 16)):
            raise ValueError("La jornada requiere 15 partidos ordenados sin duplicados.")
        if self.mode not in ("simulation", "current", "past", "future") or not self.source:
            raise ValueError("Modo o fuente no válidos.")
        if type(self.price_cents) is not int or self.price_cents <= 0:
            raise ValueError("Precio positivo en céntimos requerido.")
        validate_datetime(self.captured_at)
        if len({s.kind for s in self.snapshots}) != len(self.snapshots):
            raise ValueError("v0.1 admite una instantánea por tipo de fuente.")

    @property
    def key(self):
        return f"{self.season}/J{self.number:02}"

    @property
    def editable(self):
        return self.mode == "simulation" or (self.mode == "current" and (
            date.today() <= date.fromisoformat(self.editable_until) if self.editable_until
            else not self.nominal_date or date.fromisoformat(self.nominal_date) == date.today()))

    def snapshot(self, kind):
        return next((s for s in self.snapshots if s.kind == kind), None)


@dataclass(frozen=True)
class SystemVersion:
    system_id: str
    revision: int
    round_key: str
    name: str
    base: tuple[str, ...]
    locks: tuple[bool, ...]
    pleno: str
    bets: tuple[Bet, ...]
    created_at: str
    origin: str = "manual"
    parameters: str = "{}"
    round_snapshot: str = ""

    def __post_init__(self):
        object.__setattr__(self, "base", normalize_base(self.base))
        object.__setattr__(self, "locks", tuple(self.locks))
        object.__setattr__(self, "bets", tuple(self.bets))
        if any(not isinstance(bet, Bet) for bet in self.bets):
            raise ValueError("Apuestas inválidas en el sistema.")
        normalize_base(self.base)
        if len(self.locks) != 14 or any(type(v) is not bool for v in self.locks):
            raise ValueError("Se requieren 14 bloqueos booleanos.")
        if self.pleno and not re.fullmatch(r"[012M]{2}", self.pleno):
            raise ValueError("Pleno inválido.")
        if not self.name.strip() or self.revision < 1 or not self.system_id:
            raise ValueError("Sistema inválido.")
        validate_datetime(self.created_at)
        json.loads(self.parameters)
        if self.round_snapshot and round_from_dict(json.loads(self.round_snapshot)).key != self.round_key:
            raise ValueError("Instantánea de otra jornada.")

    @property
    def hash(self):
        payload = json.dumps([asdict(b) for b in self.bets], sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def quantity(self):
        return sum(b.quantity for b in self.bets)

    def cost(self, round_):
        if self.round_key != round_.key:
            raise ValueError("El sistema pertenece a otra jornada.")
        frozen = round_from_dict(json.loads(self.round_snapshot)) if self.round_snapshot else round_
        return self.quantity * frozen.price_cents


def round_dict(round_):
    return asdict(round_)


def round_from_dict(data):
    return Round(**{**data, "matches": tuple(Match(**m) for m in data["matches"]),
                    "snapshots": tuple(ProbabilitySnapshot(**{**s, "values": tuple(tuple(r) for r in s["values"])}) for s in data.get("snapshots", []))})


def system_dict(system):
    return asdict(system)


def system_from_dict(data):
    return SystemVersion(**{**data, "base": tuple(data["base"]), "locks": tuple(data["locks"]),
                            "bets": tuple(Bet(**b) for b in data["bets"])})
