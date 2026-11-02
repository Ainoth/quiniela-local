"""Explain why an observed winning column was rejected by saved reductions."""

from __future__ import annotations

from itertools import pairwise

from quiniela_ai_studio.domain.filters import filters_from_parameters

_TAB_NAMES = {
    0: "Cuenta", 1: "SSeguidos", 2: "Interrupciones", 3: "Patrones",
    4: "Parejas", 5: "Tríos", 6: "Cuartetos", 7: "Quintetos",
    8: "Coincidencias", 9: "Grupo", 10: "Relaciones", 11: "Frecuencia",
    12: "Valoraciones", 13: "Columnas base", 14: "Si… entonces",
    15: "Reservas", 16: "Atenea", 17: "FSSeguidos", 18: "Interrupciones",
}


def explain_filter_rejections(column: str, parameters: dict) -> tuple[dict[str, str], ...]:
    """Return each active condition that rejects a concrete 14-sign result.

    This reports the saved local filter configuration, not a third-party
    implementation. The labels follow the visible Reducciones tabs.
    """
    if len(column) != 14 or set(column) - set("1X2"):
        raise ValueError("El diagnóstico necesita los 14 signos ganadores.")
    spec = filters_from_parameters(parameters)
    enabled = set(spec.reduction_tabs_enabled)
    failures: list[dict[str, str]] = []

    def add(tab: int, condition: str, observed: str, expected: str) -> None:
        failures.append({
            "reduction": _TAB_NAMES.get(tab, "Reducción"),
            "condition": condition,
            "observed": observed,
            "expected": expected,
        })

    if 0 in enabled or spec.quick_conditions_active:
        counts = {"V": sum(s != "1" for s in column), "X": column.count("X"), "2": column.count("2")}
        for sign, limits in (("V", spec.variants), ("X", spec.x_count), ("2", spec.two_count)):
            if not limits[0] <= counts[sign] <= limits[1]:
                add(0, f"Cantidad de {sign}", str(counts[sign]), f"{limits[0]}–{limits[1]}")
        if 0 in enabled or 2 in enabled:
            from quiniela_ai_studio.domain.sign_distance import maximum_sign_distance
            distance = maximum_sign_distance(column, "X")
            if not spec.x_distance[0] <= distance <= spec.x_distance[1]:
                add(0, "Distancia entre equis", str(distance), f"{spec.x_distance[0]}–{spec.x_distance[1]}")
    if 2 in enabled or spec.quick_conditions_active:
        changes = sum(left != right for left, right in pairwise(column))
        if not spec.changes[0] <= changes <= spec.changes[1]:
            add(2, "Número de interrupciones", str(changes), f"{spec.changes[0]}–{spec.changes[1]}")
    for sign, limit in (("1", spec.max_one_run), ("X", spec.max_x_run), ("2", spec.max_two_run)):
        if 1 in enabled and _longest_run(column, sign) > limit:
            add(1, f"Racha máxima de {sign}", str(_longest_run(column, sign)), f"≤ {limit}")
    if 8 in enabled and spec.reference:
        hits = sum(a == b for a, b in zip(column, spec.reference))
        if not spec.coincidences[0] <= hits <= spec.coincidences[1]:
            add(8, "Coincidencias con la referencia", str(hits), f"{spec.coincidences[0]}–{spec.coincidences[1]}")

    advanced = spec.advanced
    tabs = set(advanced.enabled_tabs)
    group_hits = {group.name: group.hits(column) for group in advanced.groups}
    failed_advanced = []
    if 9 in tabs:
        failed_advanced.extend(
            (9, group.name, group_hits[group.name], group.minimum, group.maximum)
            for group in advanced.groups
            if not group.minimum <= group_hits[group.name] <= group.maximum
        )
    for relation in advanced.relations:
        relation_tab = 13 if relation.operation == "sum" else 10
        if relation_tab not in tabs:
            continue
        values = [group_hits[name] for name in relation.groups]
        value = sum(values) if relation.operation == "sum" else abs(values[0] - values[1])
        if not relation.minimum <= value <= relation.maximum:
            failed_advanced.append((relation_tab, "Relación " + relation.operation, value, relation.minimum, relation.maximum))
    for rule in advanced.implications if 14 in tabs else ():
        trigger = rule.antecedent_minimum <= group_hits[rule.antecedent] <= rule.antecedent_maximum
        if trigger and not rule.consequent_minimum <= group_hits[rule.consequent] <= rule.consequent_maximum:
            failed_advanced.append((14, f"Si {rule.antecedent}, entonces {rule.consequent}", group_hits[rule.consequent], rule.consequent_minimum, rule.consequent_maximum))
    allowance = advanced.allowed_failures if 15 in tabs else 0
    if len(failed_advanced) > allowance:
        for tab, name, value, low, high in failed_advanced:
            add(tab, name, str(value), f"{low}–{high}")
        if allowance:
            add(15, "Tolerancia de fallos", str(len(failed_advanced)), f"máximo {allowance}")

    for rule in spec.reduction_rules:
        if not rule.active or rule.tab_index not in enabled:
            continue
        try:
            accepted = rule.accepts(column)
        except (ValueError, IndexError, KeyError):
            continue
        if accepted:
            continue
        measured = rule.measure(column)
        observed = str(int(measured)) if measured.is_integer() else str(measured)
        if rule.kind in ("allowed_count", "allowed_run_length", "allowed_run_count", "allowed_interruption_total", "allowed_sign_distance"):
            expected = "valores " + ", ".join(map(str, rule.allowed_values))
        elif rule.kind in ("allowed_run_figure", "allowed_interruption_figure"):
            expected = "figuras " + ", ".join(rule.allowed_figures)
        elif rule.kind in ("allowed_profile", "allowed_interruption_profile"):
            expected = "uno de los perfiles seleccionados"
        elif rule.kind == "run_frequency":
            expected = "límites seleccionados por longitud de racha"
        else:
            expected = f"{rule.minimum:g}–{rule.maximum:g}"
        condition = _condition_label(rule)
        add(rule.tab_index, condition, observed, expected)
    return tuple(failures)


def _longest_run(column: str, sign: str) -> int:
    longest = current = 0
    for value in (*column, "!"):
        if value == sign:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _condition_label(rule) -> str:
    """Prefer a plain description over the internal serialized rule ID."""
    sign = rule.sign or ""
    labels = {
        "allowed_count": f"Cantidad de {sign}",
        "allowed_run_length": f"Racha máxima de {sign}",
        "allowed_run_count": f"Rachas de longitud {rule.run_length} de {sign}",
        "allowed_run_figure": f"Figura de rachas de {sign} (total {rule.run_length})",
        "allowed_profile": "Perfil de Cuenta" if rule.profile_kind == "counts" else "Perfil conjunto",
        "allowed_interruption_profile": "Par total/racha de interrupciones",
        "allowed_interruption_figure": f"Figura de interrupciones (total {rule.run_length})",
        "allowed_interruption_total": "Total de interrupciones",
        "allowed_sign_distance": f"Distancia máxima de {sign}",
        "run_frequency": f"Frecuencia de rachas de {sign}",
    }
    if rule.kind in labels:
        return labels[rule.kind]
    return rule.rule_id.replace("-", " ").replace("_", " ").strip().capitalize()
