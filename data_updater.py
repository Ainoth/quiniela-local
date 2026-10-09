"""Descarga directa y segura de datos, sin depender de WebW1X2.exe."""

from __future__ import annotations

import io
import math
import os
import re
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree

WIN1X2_ZIP = "https://www.win1x2.com/datos/actudato.zip"
QUINIELISTA_PERCENTAGES = "https://www.quinielista.es/xml2/porcentajes_completo.asp?jornada={round_no}"
MAX_DOWNLOAD = 25 * 1024 * 1024
MAX_UNPACKED = 60 * 1024 * 1024


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "QuinielaLocal/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise OSError(f"El servidor respondió con HTTP {response.status}")
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError("La descarga supera el tamaño máximo permitido")
    return data


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".descarga")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def update_win1x2_files(data_dir: Path) -> list[str]:
    """Valida el paquete completo antes de reemplazar cada fichero de Datosg."""
    payload = _download(WIN1X2_ZIP)
    updated: list[tuple[Path, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        if not members or sum(item.file_size for item in members) > MAX_UNPACKED:
            raise ValueError("El paquete de WIN1X2 está vacío o tiene un tamaño inesperado")
        for item in members:
            normalized = item.filename.replace("\\", "/")
            parts = Path(normalized).parts
            if len(parts) != 2 or parts[0].upper() != "DATOSG":
                raise ValueError(f"Ruta no permitida dentro del ZIP: {item.filename}")
            name = parts[1]
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
                raise ValueError(f"Nombre de archivo no permitido: {name}")
            updated.append((data_dir / name, archive.read(item)))
    # Solo se escribe después de validar todos los miembros.
    for target, data in updated:
        _atomic_write(target, data)
    return [target.name for target, _ in updated]


def fetch_percentages(season: str, round_no: int, cache_dir: Path) -> Path:
    payload = _download(QUINIELISTA_PERCENTAGES.format(round_no=round_no))
    _validated_percentages(payload, season, round_no)
    target = cache_dir / f"porcentajes_{season}_J{round_no:02d}.xml"
    _atomic_write(target, payload)
    return target


def _validated_percentages(payload: bytes, season: str, round_no: int):
    root = ElementTree.fromstring(payload)
    header = root if root.tag == "porcentajes" else root.find(".//porcentajes")
    if header is None or header.attrib.get("temporada") != str(2000 + int(season[3:])) or header.attrib.get("jornada") != str(round_no):
        raise ValueError("Los porcentajes no identifican la temporada y jornada solicitadas.")
    matches = root.findall(".//partido")
    if len(matches) != 15:
        raise ValueError(f"Se esperaban 15 partidos y se recibieron {len(matches)}")
    for number, match in enumerate(matches, 1):
        if int(match.attrib.get("num", "-1")) != number:
            raise ValueError("El XML contiene una numeración de partidos inesperada")
        values = [float(match.attrib[f"p_jugados_{sign}"]) for sign in ("1", "X", "2")]
        # El partido 15 es un marcador (Pleno al 15), no un signo 1-X-2.
        if any(not math.isfinite(v) or v < 0 or v > 100 for v in values):
            raise ValueError("Porcentajes no válidos.")
        if number <= 14 and not 99.0 <= sum(values) <= 101.0:
            raise ValueError(f"Los porcentajes del partido {number} no suman 100")
    return [tuple(v * 100 / sum(row) for v in row) for row in (
        [float(m.attrib[f"p_jugados_{s}"]) for s in ("1", "X", "2")]
        for m in matches[:14]
    )]


def read_percentages(season: str, round_no: int, cache_dir: Path) -> list[tuple[float, float, float]] | None:
    path = cache_dir / f"porcentajes_{season}_J{round_no:02d}.xml"
    if not path.exists():
        return None
    try:
        return _validated_percentages(path.read_bytes(), season, round_no)
    except (ValueError, KeyError, ElementTree.ParseError, OSError):
        return None
