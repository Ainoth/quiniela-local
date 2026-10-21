"""Carga el histórico incluido con la app sin solicitar archivos al usuario."""

from __future__ import annotations

import csv
from importlib.resources import files


def bundled_results() -> list[dict[str, str]]:
    """Read bundled match outcomes and optional verified 15-match scorelines."""
    resource = files("quiniela_ai_studio").joinpath("data/historico_resultados_quiniela.csv")
    with resource.open("r", encoding="utf-8-sig", newline="") as stream:
        records = list(csv.DictReader(stream))
    required = {"season", "round", "results14"}
    if not records or not required.issubset(records[0]):
        raise ValueError("El histórico incluido no tiene las columnas season, round y results14.")
    return [{**row, "source": "Histórico incluido · HistóricoQuiniela"} for row in records]
