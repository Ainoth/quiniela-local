"""Ejecución por streaming y exportación atómica de acciones del generador Normal."""

from __future__ import annotations

import csv
import json
import math
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Callable, Sequence

from quiniela_ai_studio.domain.normal_generation import (
    MAX_ACTION_COLUMNS,
    column_log_probability,
    iter_ranked_columns,
)


def generate_actions_file(
    path: str | Path,
    actions: Sequence[dict],
    *,
    keep_duplicates: bool = False,
    intersection: bool = False,
    cancelled: Callable[[], bool] = lambda: False,
    progress: Callable[[int, int, str], None] = lambda done, total, message: None,
) -> dict:
    """Ordena acciones en SQLite temporal y publica TXT/CSV/JSON mediante rename.

    Las columnas se escriben en disco de forma incremental; los resultados no se
    materializan todos en RAM. Las posiciones probabilísticas se conservan antes
    de aplicar terminaciones, y `Desde`/`Hasta` se interpretan inclusivamente.
    """
    if not actions:
        raise ValueError("Activa al menos una fila de acciones.")
    path = Path(path)
    format_ = path.suffix.lower().lstrip(".")
    if format_ not in {"txt", "csv", "json"}:
        raise ValueError("Elige un destino TXT, CSV o JSON.")
    path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    db_fd, db_name = tempfile.mkstemp(prefix=".qais-actions-", suffix=".sqlite3", dir=path.parent)
    os.close(db_fd)
    out_fd, out_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(out_fd)
    db_path, temporary = Path(db_name), Path(out_name)
    per_action = []
    total_candidates = sum(int(action["rank_end"]) for action in actions)
    total_candidates = max(1, total_candidates)
    completed = 0
    try:
        with sqlite3.connect(db_path) as db:
            db.execute("PRAGMA journal_mode=OFF")
            db.execute("PRAGMA synchronous=OFF")
            db.execute("CREATE TABLE result (action INTEGER NOT NULL, position INTEGER NOT NULL, column TEXT NOT NULL, probability REAL, PRIMARY KEY(action,position))")
            for action_index, action in enumerate(actions):
                if cancelled():
                    raise InterruptedError("Generación cancelada; el fichero anterior se conserva.")
                label = str(action.get("label", f"Acción {action_index + 1}"))
                from_position = int(action.get("rank_start", 1))
                through = int(action["rank_end"])
                endings = frozenset(action.get("endings", ()))
                minimum_cp = float(action.get("minimum_probability", 0))
                maximum_cp = float(action.get("maximum_probability", 1))
                if (not math.isfinite(minimum_cp) or not 0 <= minimum_cp <= 1
                        or not math.isfinite(maximum_cp) or not 0 <= maximum_cp <= 1
                        or minimum_cp > maximum_cp):
                    raise ValueError(f"{label}: el rango C.P. debe cumplir 0 ≤ mínimo ≤ máximo ≤ 1.")
                base = action.get("base")
                if action.get("imported_columns") is not None:
                    imported = tuple(action["imported_columns"])
                    if len(imported) > MAX_ACTION_COLUMNS:
                        raise ValueError(f"{label}: el fichero supera el límite de {MAX_ACTION_COLUMNS:,} columnas.")
                    iterator = ((position, column, None) for position, column in enumerate(imported, 1))
                    from_position, through = max(1, from_position), min(through, len(imported))
                    ranked_count = max(0, through - from_position + 1)
                else:
                    iterator = iter_ranked_columns(action["probabilities"], base=base,
                                                   limit=through,
                                                   cancelled=cancelled,
                                                   progress=lambda done, total: None)
                    ranked_count = max(0, through - from_position + 1)
                before_endings = before_cp = accepted = 0
                minimum_log = math.log(minimum_cp) if minimum_cp > 0 else -math.inf
                maximum_log = math.log(maximum_cp) if maximum_cp > 0 else -math.inf
                first_kept = last_kept = None
                db.execute("BEGIN")
                for position, column, probability in iterator:
                    if position % 1024 == 0 and cancelled():
                        raise InterruptedError("Generación cancelada; el fichero anterior se conserva.")
                    if position < from_position:
                        continue
                    before_endings += 1
                    if endings and position % 10 not in endings:
                        completed += 1
                        continue
                    if probability is not None:
                        log_probability = column_log_probability(column, action["probabilities"])
                        if log_probability < minimum_log or log_probability > maximum_log:
                            before_cp += 1
                            completed += 1
                            continue
                    db.execute("INSERT INTO result VALUES (?,?,?,?)", (action_index, position, column, probability))
                    accepted += 1
                    first_kept = position if first_kept is None else first_kept
                    last_kept = position
                    completed += 1
                    if completed % 1024 == 0:
                        if cancelled():
                            raise InterruptedError("Generación cancelada; el fichero anterior se conserva.")
                        progress(completed, total_candidates, f"{label}: {completed:,} posiciones revisadas")
                db.commit()
                per_action.append(dict(label=label, ranked_count=ranked_count,
                                       positions_checked=before_endings,
                                       rejected_endings=before_endings - accepted - before_cp,
                                       rejected_coefficient=before_cp, accepted=accepted,
                                       first_position=first_kept, last_position=last_kept,
                                       requested_start=from_position, requested_end=through,
                                       endings=sorted(endings), minimum_probability=minimum_cp,
                                       maximum_probability=maximum_cp,
                                       triples=action.get("triples", 0), doubles=action.get("doubles", 0),
                                       base=list(base) if base else None, base_decision=action.get("base_decision"),
                                       ranking_method="exact best-first log probability; ties by 1<X<2 lexical",
                                       source=action.get("source_audit") or ({key: action.get("source", {}).get(key) for key in ("round_key", "source", "kind", "captured_at")} if action.get("source") else None),
                                       probabilities=[list(row) for row in action["probabilities"]] if action.get("probabilities") else None))

            selected_count = len(actions)
            count_before = db.execute("SELECT COUNT(*) FROM result").fetchone()[0]
            if intersection:
                query = "SELECT column FROM result GROUP BY column HAVING COUNT(DISTINCT action)=? ORDER BY column"
                args = (selected_count,)
            elif keep_duplicates:
                query = "SELECT column FROM result ORDER BY action,position"
                args = ()
            else:
                query = "SELECT column FROM result GROUP BY column ORDER BY MIN(action),MIN(position)"
                args = ()
            count_final = db.execute(f"SELECT COUNT(*) FROM ({query})", args).fetchone()[0]
            duplicate_count = 0 if intersection or keep_duplicates else count_before - count_final
            intersection_removed = count_before - count_final if intersection else 0
            with temporary.open("w", encoding="utf-8", newline="\n") as output:
                if format_ == "txt":
                    for index, (column,) in enumerate(db.execute(query, args), 1):
                        if index % 4096 == 0:
                            if cancelled():
                                raise InterruptedError("Generación cancelada; el fichero anterior se conserva.")
                            progress(completed + index, total_candidates + count_final,
                                     f"Escribiendo {index:,}/{count_final:,}")
                        output.write(column + "\n")
                elif format_ == "csv":
                    writer = csv.writer(output, lineterminator="\n")
                    writer.writerow(("signs14",))
                    for column, in db.execute(query, args):
                        writer.writerow((column,))
                else:
                    output.write('{"schema":"quiniela_ai_studio.columns","version":1,"columns":[')
                    first = True
                    for column, in db.execute(query, args):
                        if not first:
                            output.write(",")
                        output.write(json.dumps({"signs14": column}, separators=(",", ":")))
                        first = False
                    output.write("]}\n")
                output.flush()
                os.fsync(output.fileno())
        if cancelled():
            raise InterruptedError("Generación cancelada; el fichero anterior se conserva.")
        os.replace(temporary, path)
        elapsed = time.monotonic() - started
        report = dict(path=str(path), format=format_, actions=per_action,
                      count_before_combination=count_before, duplicates_removed=duplicate_count,
                      columns_removed_by_intersection=intersection_removed,
                      intersection=intersection, keep_duplicates=keep_duplicates,
                      count_final=count_final, elapsed_seconds=elapsed,
                      combination=("intersección" if intersection else "concatenación" if keep_duplicates else "unión sin duplicados"))
        progress(total_candidates + count_final, total_candidates + count_final,
                 f"Finalizado: {count_final:,} columnas · {elapsed:.2f} s")
        return report
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    finally:
        db_path.unlink(missing_ok=True)
