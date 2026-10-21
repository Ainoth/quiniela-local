"""Cálculos puros del generador Normal: importación, base y ranking exacto."""

from __future__ import annotations

import csv
import heapq
import io
import itertools
import json
import math
import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass

from .models import SIGNS, Match, normalize_base, validate_column, validate_datetime

SOURCE_SCHEMA = "quiniela_ai_studio.probabilities"
MAX_SOURCE_BYTES = 20 * 1024 * 1024
MAX_ACTION_COLUMNS = 5_000_000


@dataclass(frozen=True)
class ProbabilitySource:
    """Instantánea local normalizada, asociada a una jornada y 14 partidos."""

    round_key: str
    source: str
    captured_at: str
    values: tuple[tuple[float, float, float], ...]
    kind: str = "custom"
    matches: tuple[tuple[str, str], ...] = ()
    original_name: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(tuple(float(value) for value in row) for row in self.values))
        object.__setattr__(self, "matches", tuple(tuple(pair) for pair in self.matches))
        if not self.round_key or not self.source or not self.captured_at:
            raise ValueError("La fuente necesita jornada, nombre y fecha de captura.")
        validate_datetime(self.captured_at)
        if self.kind not in {"classification", "form5", "history", "market", "public", "custom"}:
            raise ValueError("Tipo de fuente no reconocido.")
        if len(self.values) != 14:
            raise ValueError("La matriz de porcentajes debe contener 14 partidos.")
        for row in self.values:
            if len(row) != 3 or any(not math.isfinite(v) or v < 0 or v > 1 for v in row):
                raise ValueError("Cada porcentaje debe ser finito y estar entre 0 y 100%.")
            if not math.isclose(sum(row), 1.0, abs_tol=1e-8):
                raise ValueError("Los porcentajes de cada partido deben sumar 100%.")
        if self.matches and len(self.matches) != 14:
            raise ValueError("La fuente necesita 14 parejas de equipos.")


@dataclass(frozen=True)
class ActionResult:
    """Resultado de una acción y sus conteos verificables."""

    columns: tuple[str, ...]
    ranked_count: int
    rejected_terminations: int
    rejected_coefficient: int
    first_position: int | None
    last_position: int | None


def _probability_rows(values: Sequence[Sequence[float]]) -> tuple[tuple[float, float, float], ...]:
    if len(values) != 14:
        raise ValueError("Se necesitan porcentajes para los 14 partidos.")
    rows = []
    for row in values:
        if len(row) != 3:
            raise ValueError("Cada partido necesita porcentajes 1, X y 2.")
        normalized = tuple(float(value) for value in row)
        if any(not math.isfinite(value) or value < 0 for value in normalized):
            raise ValueError("Los porcentajes deben ser números finitos no negativos.")
        total = math.fsum(normalized)
        if total <= 0:
            raise ValueError("Cada partido necesita al menos un porcentaje positivo.")
        rows.append(tuple(value / total for value in normalized))
    return tuple(rows)


def normalize_percentages(values: Sequence[Sequence[float]], digits: int = 2) -> tuple[tuple[float, float, float], ...]:
    """Normaliza expresamente cada fila; el residuo de redondeo va al signo mayor."""
    if not 0 <= digits <= 6:
        raise ValueError("La precisión debe estar entre 0 y 6 decimales.")
    rows = _probability_rows(values)
    output = []
    for row in rows:
        rounded = [round(value * 100, digits) for value in row]
        target = max(range(3), key=lambda i: (row[i], -i))
        rounded[target] = round(rounded[target] + 100.0 - math.fsum(rounded), digits)
        if rounded[target] < 0:
            raise ValueError("No se pudo normalizar la fila con la precisión elegida.")
        output.append(tuple(value / 100 for value in rounded))
    return tuple(output)


def validate_percentages(values: Sequence[Sequence[float]]) -> tuple[tuple[float, float, float], ...]:
    """Valida sin normalizar silenciosamente porcentajes editados por el usuario."""
    if len(values) != 14:
        raise ValueError("La matriz debe tener exactamente 14 partidos.")
    rows = []
    for row in values:
        values_row = tuple(float(value) for value in row)
        if len(values_row) != 3 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in values_row):
            raise ValueError("Cada porcentaje debe estar entre 0 y 100.")
        if not math.isclose(math.fsum(values_row), 1.0, abs_tol=1e-6):
            raise ValueError("Cada fila debe sumar 100%. Usa «Normalizar filas» para ajustarla.")
        rows.append(values_row)
    return tuple(rows)


def import_probability_source(
    data: bytes,
    *,
    round_key: str,
    matches: Sequence[Match],
    source_kind: str = "custom",
    filename: str = "",
) -> ProbabilitySource:
    """Lee CSV/TXT/JSON abierto y valida jornada, identidad, orden y porcentajes.

    JSON usa el esquema `quiniela_ai_studio.probabilities` v1. CSV/TXT lleva
    cabecera `number,home,away,p1,px,p2`; se admiten fracciones o porcentajes.
    """
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError("La fuente supera el límite de 20 MiB.")
    if len(matches) < 14:
        raise ValueError("La jornada no contiene los 14 partidos de 1X2.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("El archivo debe estar codificado en UTF-8.") from exc
    if not text.strip():
        raise ValueError("El archivo está vacío.")
    if text.lstrip().startswith("{"):
        try:
            document = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON inválido en la línea {exc.lineno}.") from exc
        if document.get("schema") != SOURCE_SCHEMA or document.get("version") != 1:
            raise ValueError(f"Se requiere el esquema {SOURCE_SCHEMA} versión 1.")
        if document.get("round_key") != round_key:
            raise ValueError("La jornada del archivo no coincide con la jornada abierta.")
        source_name = str(document.get("source", "")).strip()
        captured = str(document.get("captured_at", "")).strip()
        kind = str(document.get("kind", source_kind))
        entries = document.get("matches")
        if not isinstance(entries, list) or len(entries) != 14:
            raise ValueError("El JSON debe contener 14 entradas en «matches».")
        rows = []
        for index, (entry, match) in enumerate(zip(entries, matches[:14]), 1):
            if not isinstance(entry, dict) or entry.get("number") != index:
                raise ValueError(f"El partido {index} tiene número u orden incorrecto.")
            _validate_pair(entry.get("home"), entry.get("away"), match, index)
            rows.append(_convert_values((entry.get("p1"), entry.get("px"), entry.get("p2")), index))
    else:
        source_name = ""
        captured = ""
        kind = source_kind
        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        records = list(csv.DictReader(io.StringIO(text), dialect=dialect))
        if len(records) != 14:
            raise ValueError("CSV/TXT debe contener cabecera y exactamente 14 filas.")
        required = {"number", "home", "away", "p1", "px", "p2", "source", "captured_at"}
        keys = {key.strip().lower() for key in records[0] if key}
        if not required <= keys:
            raise ValueError("Cabeceras requeridas: number, home, away, p1, px, p2.")
        rows = []
        for index, (raw, match) in enumerate(zip(records, matches[:14]), 1):
            row = {str(key).strip().lower(): value for key, value in raw.items() if key}
            if str(row.get("number", "")).strip() != str(index):
                raise ValueError(f"El partido {index} tiene número u orden incorrecto.")
            _validate_pair(row.get("home"), row.get("away"), match, index)
            rows.append(_convert_values((row.get("p1"), row.get("px"), row.get("p2")), index))
        source_names = {str(row.get("source", "")).strip() for row in records}
        capture_times = {str(row.get("captured_at", "")).strip() for row in records}
        kinds = {str(row.get("kind", source_kind)).strip() or source_kind for row in records}
        if len(source_names) != 1 or not next(iter(source_names)) or len(capture_times) != 1 or not next(iter(capture_times)):
            raise ValueError("La fuente y fecha de captura deben ser iguales y no vacías en las 14 filas.")
        if len(kinds) != 1:
            raise ValueError("El tipo de fuente debe ser igual en las 14 filas.")
        source_name = next(iter(source_names))
        captured = next(iter(capture_times))
        kind = next(iter(kinds))
    if not source_name or not captured:
        raise ValueError("La fuente debe indicar nombre y fecha de captura.")
    values = validate_percentages(rows)
    return ProbabilitySource(round_key, source_name, captured, values, kind,
                             tuple((m.home, m.away) for m in matches[:14]), filename)


def _validate_pair(home, away, match: Match, index: int) -> None:
    if not isinstance(home, str) or not isinstance(away, str):
        raise ValueError(f"Faltan los equipos del partido {index}.")
    clean = lambda value: " ".join(value.casefold().replace(".", "").split())
    if clean(home) != clean(match.home) or clean(away) != clean(match.away):
        raise ValueError(f"Los equipos del partido {index} no coinciden con la jornada.")


def _convert_values(raw_values, index: int) -> tuple[float, float, float]:
    try:
        values = tuple(float(str(value).strip().replace("%", "").replace(",", ".")) for value in raw_values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Porcentajes inválidos en el partido {index}.") from exc
    total = math.fsum(values)
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError(f"Porcentajes inválidos en el partido {index}.")
    if math.isclose(total, 1.0, abs_tol=1e-6):
        return values
    if 99.0 <= total <= 101.0 and all(value <= 100 for value in values):
        return tuple(value / total for value in values)
    raise ValueError(f"Los porcentajes del partido {index} no suman 100% (ni 1.0).")


def weighted_probabilities(
    sources: Sequence[tuple[ProbabilitySource, float]],
) -> tuple[tuple[float, float, float], ...]:
    """Media ponderada aritmética y normalización por fila; pesos cero se ignoran."""
    active = [(source, float(weight)) for source, weight in sources if float(weight) > 0]
    if not active:
        raise ValueError("Asigna peso positivo a una fuente disponible.")
    round_keys = {source.round_key for source, _ in active}
    if len(round_keys) != 1:
        raise ValueError("No se pueden mezclar fuentes de jornadas diferentes.")
    total_weight = math.fsum(weight for _, weight in active)
    rows = []
    for match_index in range(14):
        row = tuple(math.fsum(source.values[match_index][sign] * weight for source, weight in active) / total_weight for sign in range(3))
        total = math.fsum(row)
        rows.append(tuple(value / total for value in row))
    return tuple(rows)


def best_base(
    probabilities: Sequence[Sequence[float]],
    triples: int,
    doubles: int,
    locks: Sequence[bool] = (False,) * 14,
    locked_base: Sequence[str] | None = None,
) -> tuple[tuple[str, ...], dict]:
    """Maximiza masa de probabilidad con cantidades T/D exactas y bloqueos.

    Programación dinámica maximiza `sum_i sum_{s in S_i} p_i(s)`. Los empates
    conservan la primera ruta lexicográfica de anchuras 1,2,3. Una fila ancha
    pierde exactamente la probabilidad acumulada de los signos excluidos.
    """
    rows = validate_percentages(probabilities)
    if type(triples) is not int or type(doubles) is not int or not 0 <= triples <= 14 or not 0 <= doubles <= 14 or triples + doubles > 14:
        raise ValueError("Triples y dobles deben ser cantidades entre 0 y 14 cuya suma no supere 14.")
    if len(locks) != 14 or any(type(value) is not bool for value in locks):
        raise ValueError("Se requieren 14 estados de bloqueo válidos.")
    locked_base = normalize_base(locked_base or ("1",) * 14)
    fixed = {i: locked_base[i] for i, locked in enumerate(locks) if locked}
    fixed_t = sum(len(value) == 3 for value in fixed.values())
    fixed_d = sum(len(value) == 2 for value in fixed.values())
    if fixed_t > triples or fixed_d > doubles:
        raise ValueError("Los bloqueos ya incluyen más triples o dobles que los solicitados; desbloquea o ajusta las cantidades.")
    need_t, need_d = triples - fixed_t, doubles - fixed_d
    free = [i for i in range(14) if i not in fixed]
    if need_t + need_d > len(free):
        raise ValueError("No hay suficientes partidos desbloqueados para esa combinación.")

    dp: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {(0, 0): (0.0, ())}
    row_mass = []
    orderings = []
    for i, row in enumerate(rows):
        order = tuple(sorted(range(3), key=lambda j: (-row[j], j)))
        orderings.append(order)
        if i in fixed:
            chosen = fixed[i]
            mass = math.fsum(row[SIGNS.index(sign)] for sign in chosen)
            row_mass.append((mass,))
            continue
        masses = tuple(math.fsum(row[index] for index in order[:width]) for width in (1, 2, 3))
        row_mass.append(masses)
        next_dp = {}
        for (used_t, used_d), (score, path) in dp.items():
            for width in (1, 2, 3):
                new_t = used_t + (width == 3)
                new_d = used_d + (width == 2)
                if new_t > need_t or new_d > need_d:
                    continue
                key = (new_t, new_d)
                candidate = (score + masses[width - 1], path + (width,))
                previous = next_dp.get(key)
                if previous is None or candidate[0] > previous[0] + 1e-15:
                    next_dp[key] = candidate
        dp = next_dp
    best = dp.get((need_t, need_d))
    if best is None:
        raise ValueError("No se encontró una asignación de partidos compatible con las cantidades.")
    path_iter = iter(best[1])
    base = []
    decisions = []
    for i, row in enumerate(rows):
        if i in fixed:
            allowed = fixed[i]
        else:
            width = next(path_iter)
            allowed = "".join(SIGNS[j] for j in orderings[i][:width])
        selected_mass = math.fsum(row[SIGNS.index(sign)] for sign in allowed)
        base.append(allowed)
        decisions.append(dict(match=i + 1, width=len(allowed), signs=allowed,
                              probability_mass=selected_mass, excluded_mass=1 - selected_mass,
                              locked=i in fixed))
    return tuple(base), dict(criteria="maximizar_masa_probabilidad_independiente_v1",
                             triples=sum(len(value) == 3 for value in base),
                             doubles=sum(len(value) == 2 for value in base),
                             fixed=sum(len(value) == 1 for value in base),
                             retained_mass=math.fsum(item["probability_mass"] for item in decisions),
                             decisions=decisions)


def best_base_under_limit(
    probabilities: Sequence[Sequence[float]],
    max_columns: int,
    locks: Sequence[bool] = (False,) * 14,
    locked_base: Sequence[str] | None = None,
) -> tuple[tuple[str, ...], dict]:
    """Elige cantidades y partidos maximizando la cobertura bajo un coste.

    Busca exactamente entre anchuras fijas/dobles/triples, con coste
    ``producto(anchuras) <= max_columns``. Maximiza la probabilidad conjunta
    retenida (producto de la masa permitida por partido), en logaritmos.
    Empates: menos columnas y después ruta lexicográfica de anchuras.
    """
    rows = validate_percentages(probabilities)
    if type(max_columns) is not int or max_columns < 1:
        raise ValueError("El máximo debe ser al menos una columna.")
    if len(locks) != 14 or any(type(value) is not bool for value in locks):
        raise ValueError("Se requieren 14 estados de bloqueo válidos.")
    previous = normalize_base(locked_base or ("1",) * 14)
    orders = [tuple(sorted(range(3), key=lambda j: (-row[j], j))) for row in rows]
    # columns -> (log probability mass, widths chosen so far)
    states = {1: (0.0, ())}
    decisions_options = []
    for index, row in enumerate(rows):
        if locks[index]:
            allowed = previous[index]
            width = len(allowed)
            mass = math.fsum(row["1X2".index(sign)] for sign in allowed)
            options = ((width, allowed, mass),)
        else:
            options = tuple(
                (width, "".join("1X2"[sign] for sign in orders[index][:width]),
                 math.fsum(row[sign] for sign in orders[index][:width]))
                for width in (1, 2, 3)
            )
        decisions_options.append(options)
        next_states = {}
        for columns, (score, path) in states.items():
            for width, _signs, mass in options:
                new_columns = columns * width
                if new_columns > max_columns:
                    continue
                candidate = (score + (math.log(mass) if mass > 0 else -math.inf), path + (width,))
                old = next_states.get(new_columns)
                if old is None or candidate[0] > old[0] + 1e-15 or (
                    math.isclose(candidate[0], old[0], abs_tol=1e-15)
                    and candidate[1] < old[1]
                ):
                    next_states[new_columns] = candidate
        states = next_states
        if not states:
            raise ValueError("El máximo de columnas no permite conservar los partidos bloqueados.")
    selected_columns, (log_mass, widths) = min(
        states.items(), key=lambda item: (-item[1][0], item[0], item[1][1])
    )
    base = []
    decisions = []
    for index, (width, options) in enumerate(zip(widths, decisions_options, strict=True)):
        _, signs, mass = next(option for option in options if option[0] == width)
        base.append(signs)
        decisions.append(dict(match=index + 1, width=width, signs=signs,
                              probability_mass=mass, excluded_mass=1 - mass,
                              locked=locks[index]))
    return tuple(base), dict(
        criteria="maximizar_probabilidad_conjunta_bajo_limite_columnas_v1",
        max_columns=max_columns, columns=selected_columns,
        retained_probability=math.exp(log_mass),
        triples=sum(len(value) == 3 for value in base),
        doubles=sum(len(value) == 2 for value in base),
        fixed=sum(len(value) == 1 for value in base), decisions=decisions,
    )


def theoretical_count(triples: int, doubles: int) -> int:
    if type(triples) is not int or type(doubles) is not int or min(triples, doubles) < 0 or triples + doubles > 14:
        raise ValueError("Triples y dobles deben sumar como máximo 14.")
    return 3**triples * 2**doubles


def _rank_dimensions(probabilities, base=None):
    rows = validate_percentages(probabilities)
    allowed = normalize_base(base) if base is not None else ("1X2",) * 14
    dimensions = []
    for index, signs in enumerate(allowed):
        order = sorted((SIGNS.index(sign) for sign in signs), key=lambda sign: (-rows[index][sign], sign))
        dimensions.append(tuple((sign, rows[index][sign]) for sign in order))
    return tuple(dimensions)


def iter_ranked_columns(
    probabilities: Sequence[Sequence[float]],
    *,
    base: Sequence[str] | None = None,
    limit: int | None = None,
    cancelled=lambda: False,
    progress=lambda done, total: None,
) -> Iterator[tuple[int, str, float]]:
    """Enumera exactamente por probabilidad descendente, O(K·14) memoria.

    Empates secundarios por la cadena de signos ascendente `1 < X < 2`.
    Best-first sobre el producto cartesiano: cada vecino reduce/no aumenta
    probabilidad porque cada dimensión ya está ordenada.
    """
    dims = _rank_dimensions(probabilities, base)
    total = math.prod(len(row) for row in dims)
    if limit is None:
        limit = total
    if type(limit) is not int or not 0 <= limit <= total or limit > MAX_ACTION_COLUMNS:
        raise ValueError(f"El límite debe estar entre 0 y {min(total, MAX_ACTION_COLUMNS):,} columnas.")
    start = 0

    def cell(code):
        indices = tuple((code >> (2 * i)) & 0b11 for i in range(14))
        signs = "".join(SIGNS[dims[i][index][0]] for i, index in enumerate(indices))
        tie_key = sum(dims[i][index][0] << (2 * (13 - i)) for i, index in enumerate(indices))
        logs = [math.log(dims[i][index][1]) if dims[i][index][1] > 0 else -math.inf for i, index in enumerate(indices)]
        logp = math.fsum(logs) if all(math.isfinite(value) for value in logs) else -math.inf
        return signs, logp, tie_key

    first_signs, first_logp, first_tie = cell(start)
    heap = [(-first_logp, first_tie, first_signs, start)]
    visited = {start}
    for position in range(1, limit + 1):
        if position == 1 or position % 512 == 0:
            if cancelled():
                raise InterruptedError("Generación cancelada; el archivo de destino permanece intacto.")
            progress(position - 1, limit)
        negative_log, _tie_key, column, code = heapq.heappop(heap)
        logp = -negative_log
        yield position, column, (math.exp(logp) if math.isfinite(logp) else 0.0)
        for dimension in range(14):
            index = (code >> (2 * dimension)) & 0b11
            if index + 1 >= len(dims[dimension]):
                continue
            neighbor = code + (1 << (2 * dimension))
            if neighbor in visited:
                continue
            visited.add(neighbor)
            signs, neighbor_logp, tie_key = cell(neighbor)
            heapq.heappush(heap, (-neighbor_logp, tie_key, signs, neighbor))
    if cancelled():
        raise InterruptedError("Generación cancelada; el archivo de destino permanece intacto.")
    progress(limit, limit)


def column_log_probability(column: str, probabilities: Sequence[Sequence[float]]) -> float:
    """Producto P(c) en logaritmos; devuelve −∞ si hay un signo imposible."""
    validate_column(column)
    rows = validate_percentages(probabilities)
    terms = [rows[index][SIGNS.index(sign)] for index, sign in enumerate(column)]
    if any(value == 0 for value in terms):
        return -math.inf
    return math.fsum(math.log(value) for value in terms)


def select_ranked_action(
    probabilities: Sequence[Sequence[float]],
    *,
    count: int,
    start: int | None = None,
    end: int | None = None,
    base: Sequence[str] | None = None,
    endings: Iterable[int] = (),
    minimum_probability: float = 0.0,
    maximum_probability: float = 1.0,
    cancelled=lambda: False,
    progress=lambda done, total: None,
) -> ActionResult:
    """Aplica rango inclusivo, terminación posicional y C.P. a la clasificación."""
    dims = _rank_dimensions(probabilities, base)
    total = math.prod(len(row) for row in dims)
    if (start is None) != (end is None):
        raise ValueError("Indica Desde y Hasta juntos, o deja ambos vacíos para usar Núm. Colum.")
    first, last = (1, count) if start is None else (start, end)
    if type(first) is not int or type(last) is not int or first < 1 or last < first or last > total:
        raise ValueError(f"El rango inclusivo debe estar entre 1 y {total:,}.")
    if last > MAX_ACTION_COLUMNS:
        raise ValueError(f"El rango exacto supera el límite de {MAX_ACTION_COLUMNS:,} columnas por acción.")
    if (not math.isfinite(minimum_probability) or not 0 <= minimum_probability <= 1
            or not math.isfinite(maximum_probability) or not 0 <= maximum_probability <= 1
            or minimum_probability > maximum_probability):
        raise ValueError("El rango C.P. debe cumplir 0 ≤ mínimo ≤ máximo ≤ 1.")
    selected_endings = frozenset(endings)
    if selected_endings - set(range(10)):
        raise ValueError("Las terminaciones posibles son dígitos 0–9.")
    accepted = []
    rejected_endings = rejected_cp = 0
    first_kept = last_kept = None
    minimum_log = math.log(minimum_probability) if minimum_probability > 0 else -math.inf
    maximum_log = math.log(maximum_probability) if maximum_probability > 0 else -math.inf
    for position, column, probability in iter_ranked_columns(probabilities, base=base, limit=last,
                                                              cancelled=cancelled, progress=progress):
        if position < first:
            continue
        if selected_endings and position % 10 not in selected_endings:
            rejected_endings += 1
            continue
        log_probability = column_log_probability(column, probabilities)
        if log_probability < minimum_log or log_probability > maximum_log:
            rejected_cp += 1
            continue
        accepted.append(column)
        first_kept = position if first_kept is None else first_kept
        last_kept = position
    return ActionResult(tuple(accepted), last - first + 1, rejected_endings, rejected_cp,
                        first_kept, last_kept)


def generate_base_action(
    probabilities: Sequence[Sequence[float]],
    base: Sequence[str],
    *,
    endings: Iterable[int] = (),
    minimum_probability: float = 0.0,
    maximum_probability: float = 1.0,
    cancelled=lambda: False,
    progress=lambda done, total: None,
) -> ActionResult:
    """Ordena exactamente todas las columnas de una base (máx. cinco millones)."""
    normalized = normalize_base(base)
    total = math.prod(len(value) for value in normalized)
    if total > MAX_ACTION_COLUMNS:
        raise ValueError(f"La base contiene {total:,} columnas; por acción el límite es {MAX_ACTION_COLUMNS:,}.")
    return select_ranked_action(probabilities, count=total, base=normalized, endings=endings,
                                minimum_probability=minimum_probability,
                                maximum_probability=maximum_probability,
                                cancelled=cancelled, progress=progress)


def combine_action_columns(actions: Sequence[Sequence[str]], *, keep_duplicates: bool, intersection: bool):
    """Combina resultados: concatenación, unión ordenada estable o intersección."""
    if not actions:
        raise ValueError("Selecciona al menos una acción.")
    normalized = [tuple(validate_column(column) for column in action) for action in actions]
    if intersection:
        common = set(normalized[0])
        for action in normalized[1:]:
            common.intersection_update(action)
        return tuple(sorted(common)), sum(map(len, normalized)) - len(common)
    if keep_duplicates:
        result = tuple(itertools.chain.from_iterable(normalized))
        return result, len(result) - len(set(result))
    result = []
    seen = set()
    for action in normalized:
        for column in action:
            if column not in seen:
                seen.add(column)
                result.append(column)
    return tuple(result), sum(map(len, normalized)) - len(result)


def parse_columns_file(data: bytes) -> tuple[str, ...]:
    """Importa columnas abiertas TXT/CSV/JSON con exactamente 14 signos 1/X/2."""
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError("El archivo supera el límite de 20 MiB.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("El fichero de columnas debe estar codificado en UTF-8.") from exc
    if not text.strip():
        raise ValueError("El fichero no contiene columnas.")
    if text.lstrip().startswith("{"):
        try:
            document = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON inválido en la línea {exc.lineno}.") from exc
        rows = document.get("columns") if document.get("schema") == "quiniela_ai_studio.columns" and document.get("version") == 1 else None
        if not isinstance(rows, list):
            raise ValueError("JSON de columnas no compatible; se requiere quiniela_ai_studio.columns v1.")
        values = [row.get("signs14", "") if isinstance(row, dict) else row for row in rows]
    else:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        delimiter = next((separator for separator in (",", ";", "\t") if separator in first_line), None)
        header = [part.strip().casefold() for part in first_line.split(delimiter)] if delimiter else []
        column_header = next((field for field in ("signs14", "column", "columna", "columna14") if field in header), None)
        values = []
        if column_header:
            records = csv.DictReader(io.StringIO(text), delimiter=delimiter)
            for line_no, row in enumerate(records, 2):
                try: values.append(validate_column(str(row[column_header]).strip().upper()))
                except (ValueError, KeyError, TypeError) as exc:
                    raise ValueError(f"Línea {line_no}: se esperaba una columna con 14 signos 1/X/2.") from exc
        else:
            for line_no, raw in enumerate(text.splitlines(), 1):
                line = raw.strip().upper()
                if not line or line.startswith("#"):
                    continue
                if "," in line or ";" in line or "\t" in line:
                    line = re.split(r"[,;\t]", line, maxsplit=1)[0].strip()
                if len(line) == 16 and re.fullmatch(r"[1X2]{14}[012M]{2}", line):
                    raise ValueError(f"Línea {line_no}: el Pleno al 15 no se descarta al importar columnas; usa el fichero de apuestas completo.")
                try:
                    values.append(validate_column(line))
                except ValueError as exc:
                    raise ValueError(f"Línea {line_no}: {exc}") from exc
    if not values:
        raise ValueError("No se encontraron columnas 1/X/2.")
    return tuple(validate_column(value) for value in values)
