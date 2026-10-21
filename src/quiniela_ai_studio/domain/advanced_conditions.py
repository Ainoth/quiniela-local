"""Condiciones originales por grupos para filtrar apuestas de 14 partidos."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass

from .engine import Cancelled


@dataclass(frozen=True)
class HitGroup:
    """Compara una selección de partidos con sus signos de referencia."""

    name: str
    positions: tuple[int, ...]
    accepted: tuple[str, ...]
    minimum: int
    maximum: int

    def __post_init__(self):
        if not self.name or not self.name.isidentifier():
            raise ValueError("Cada grupo necesita un nombre sencillo, por ejemplo GrupoA.")
        if not self.positions or len(set(self.positions)) != len(self.positions) or any(not 0 <= p < 14 for p in self.positions):
            raise ValueError(f"El grupo {self.name} necesita partidos distintos del 1 al 14.")
        if len(self.accepted) != len(self.positions) or any(
            not mask or any(sign not in "1X2" for sign in mask) or len(set(mask)) != len(mask)
            for mask in self.accepted
        ):
            raise ValueError(f"El grupo {self.name} necesita al menos un signo válido por partido seleccionado.")
        if not 0 <= self.minimum <= self.maximum <= len(self.positions):
            raise ValueError(f"El intervalo de aciertos del grupo {self.name} no es válido.")

    def hits(self, column: Sequence[str]) -> int:
        return sum(column[position] in mask for position, mask in zip(self.positions, self.accepted, strict=True))


@dataclass(frozen=True)
class HitRelation:
    """Limita la suma o la diferencia absoluta de aciertos entre grupos."""

    operation: str
    groups: tuple[str, ...]
    minimum: int
    maximum: int

    def __post_init__(self):
        if self.operation not in ("sum", "difference"):
            raise ValueError("La relación debe ser suma o diferencia.")
        if len(self.groups) < 2 or len(set(self.groups)) != len(self.groups):
            raise ValueError("Una relación necesita al menos dos grupos distintos.")
        if self.operation == "difference" and len(self.groups) != 2:
            raise ValueError("La diferencia relaciona exactamente dos grupos.")
        if self.minimum < 0 or self.maximum < self.minimum:
            raise ValueError("El intervalo de la relación no es válido.")
        maximum_possible = 14 if self.operation == "difference" else 14 * len(self.groups)
        if self.maximum > maximum_possible:
            raise ValueError("El máximo de la relación supera los aciertos posibles.")


@dataclass(frozen=True)
class HitImplication:
    """If one group reaches a hit interval, require an interval in another."""

    antecedent: str
    antecedent_minimum: int
    antecedent_maximum: int
    consequent: str
    consequent_minimum: int
    consequent_maximum: int

    def __post_init__(self):
        if not self.antecedent or not self.consequent or self.antecedent == self.consequent:
            raise ValueError('La condición necesita dos grupos distintos.')
        if not (0 <= self.antecedent_minimum <= self.antecedent_maximum <= 14
                and 0 <= self.consequent_minimum <= self.consequent_maximum <= 14):
            raise ValueError('Los intervalos de la condición si… entonces no son válidos.')


@dataclass(frozen=True)
class AdvancedConditions:
    """Reglas opcionales combinadas; la tolerancia cuenta reglas incumplidas."""

    groups: tuple[HitGroup, ...] = ()
    relations: tuple[HitRelation, ...] = ()
    allowed_failures: int = 0
    implications: tuple[HitImplication, ...] = ()
    enabled_tabs: tuple[int, ...] = tuple(range(17))

    def __post_init__(self):
        names = {group.name for group in self.groups}
        if len(names) != len(self.groups):
            raise ValueError("Los nombres de los grupos deben ser únicos.")
        if any(not set(relation.groups) <= names for relation in self.relations):
            raise ValueError("Una relación menciona un grupo que no existe.")
        if any(rule.antecedent not in names or rule.consequent not in names for rule in self.implications):
            raise ValueError('Una condición si… entonces menciona un grupo que no existe.')
        if not 0 <= self.allowed_failures <= len(self.groups) + len(self.relations) + len(self.implications):
            raise ValueError("La tolerancia supera el número de condiciones activas.")
        if any(type(index) is not int or not 0 <= index < 17 for index in self.enabled_tabs):
            raise ValueError('La activación de las pestañas avanzadas no es válida.')

    @property
    def enabled(self) -> bool:
        tabs=set(self.enabled_tabs)
        return bool((self.groups and 9 in tabs) or (self.relations and (9 in tabs or 13 in tabs))
                    or (self.implications and 14 in tabs))

    def accepts(self, column: Sequence[str]) -> bool:
        if len(column) != 14 or any(sign not in "1X2" for sign in column):
            raise ValueError("Las condiciones avanzadas requieren 14 signos 1/X/2.")
        values = {group.name: group.hits(column) for group in self.groups}
        tabs=set(self.enabled_tabs)
        failed = sum(not group.minimum <= values[group.name] <= group.maximum for group in self.groups) if 9 in tabs else 0
        active_relations=[relation for relation in self.relations
                          if (9 if relation.operation=='difference' else 13) in tabs]
        for relation in active_relations:
            selected = [values[name] for name in relation.groups]
            value = sum(selected) if relation.operation == "sum" else abs(selected[0] - selected[1])
            failed += not relation.minimum <= value <= relation.maximum
        active_implications=self.implications if 14 in tabs else ()
        for rule in active_implications:
            trigger=rule.antecedent_minimum <= values[rule.antecedent] <= rule.antecedent_maximum
            failed += trigger and not rule.consequent_minimum <= values[rule.consequent] <= rule.consequent_maximum
        allowance=self.allowed_failures if 15 in tabs else 0
        return failed <= allowance

    def apply(self, bets, cancelled: Callable[[], bool] = lambda: False):
        result = []
        for index, bet in enumerate(bets):
            if index % 256 == 0 and cancelled():
                raise Cancelled("Cálculo de condiciones avanzadas cancelado.")
            if self.accepts(bet.column):
                result.append(bet)
        if cancelled():
            raise Cancelled("Cálculo de condiciones avanzadas cancelado.")
        return tuple(result)

    def failure_counts(self, bets) -> tuple[tuple[str, int], ...]:
        """Count original stake quantities failing each rule; counts can overlap."""
        tabs=set(self.enabled_tabs)
        active_groups=self.groups if 9 in tabs else ()
        active_relations=[relation for relation in self.relations if (10 if relation.operation=='difference' else 13) in tabs]
        active_implications=self.implications if 14 in tabs else ()
        counts = {group.name: 0 for group in active_groups}
        for index, relation in enumerate(active_relations, 1):
            label = f"Relación {index} ({'suma' if relation.operation == 'sum' else 'diferencia'})"
            counts[label] = 0
        relation_labels = tuple(key for key in counts if key.startswith("Relación "))
        implication_labels=[]
        for index,rule in enumerate(active_implications,1):
            label=f'Si {rule.antecedent}… entonces {rule.consequent} ({index})'
            counts[label]=0;implication_labels.append(label)
        for bet in bets:
            values = {group.name: group.hits(bet.column) for group in self.groups}
            for group in active_groups:
                if not group.minimum <= values[group.name] <= group.maximum:
                    counts[group.name] += bet.quantity
            for relation, label in zip(active_relations, relation_labels, strict=True):
                selected = [values[name] for name in relation.groups]
                value = sum(selected) if relation.operation == "sum" else abs(selected[0] - selected[1])
                if not relation.minimum <= value <= relation.maximum:
                    counts[label] += bet.quantity
            for rule,label in zip(active_implications,implication_labels,strict=True):
                trigger=rule.antecedent_minimum <= values[rule.antecedent] <= rule.antecedent_maximum
                if trigger and not rule.consequent_minimum <= values[rule.consequent] <= rule.consequent_maximum:
                    counts[label]+=bet.quantity
        return tuple(counts.items())

    def parameters(self):
        return {"groups": [asdict(group) for group in self.groups],
                "relations": [asdict(relation) for relation in self.relations],
                "allowed_failures": self.allowed_failures,
                "implications": [asdict(rule) for rule in self.implications],
                "enabled_tabs": self.enabled_tabs}


def advanced_from_parameters(data: dict | None) -> AdvancedConditions:
    data = data or {}
    groups = tuple(
        HitGroup(
            str(item["name"]),
            tuple(item["positions"]),
            tuple(item["accepted"]) if "accepted" in item else tuple(item["signs"]),
            int(item["minimum"]),
            int(item["maximum"]),
        )
        for item in data.get("groups", ())
    )
    relations = tuple(HitRelation(str(item["operation"]), tuple(item["groups"]),
                                  int(item["minimum"]), int(item["maximum"]))
                      for item in data.get("relations", ()))
    implications=tuple(HitImplication(str(item['antecedent']),int(item['antecedent_minimum']),
        int(item['antecedent_maximum']),str(item['consequent']),int(item['consequent_minimum']),
        int(item['consequent_maximum'])) for item in data.get('implications',()))
    return AdvancedConditions(groups, relations, int(data.get("allowed_failures", 0)),implications,
                              tuple(data.get('enabled_tabs',range(17))))
