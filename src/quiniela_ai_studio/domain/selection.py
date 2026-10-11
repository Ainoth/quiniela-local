"""Selección y reglas versionadas; modalidades separadas y dinero entero."""

from dataclasses import dataclass
from math import prod

from .models import Bet, normalize_base


@dataclass(frozen=True)
class GameRuleset:
    version: str
    price_cents: int
    modality: str = "quiniela"

    def __post_init__(self):
        if (
            not self.version
            or type(self.price_cents) is not int
            or self.price_cents <= 0
        ):
            raise ValueError(
                "Indica una versión de reglas y un precio positivo en céntimos."
            )
        if self.modality != "quiniela":
            raise ValueError(
                "Elige8 está reservado como modalidad independiente, todavía no implementada."
            )

    def cost(self, quantity: int) -> int:
        if type(quantity) is not int or quantity < 0:
            raise ValueError("Cantidad entera no negativa requerida.")
        return quantity * self.price_cents


@dataclass(frozen=True)
class Selection:
    base: tuple[str, ...]
    plenos: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "base", normalize_base(self.base))
        object.__setattr__(self, "plenos", tuple(self.plenos))
        if (
            not self.plenos
            or len(self.plenos) > 16
            or len(set(self.plenos)) != len(self.plenos)
        ):
            raise ValueError("Selecciona entre 1 y 16 parejas de Pleno distintas.")
        for pleno in self.plenos:
            if not pleno:
                raise ValueError("Completa el Pleno antes de generar o exportar.")
            Bet("1" * 14, pleno)

    @property
    def quantity(self) -> int:
        return prod(len(p) for p in self.base) * len(self.plenos)
