"""Sistemas de escritorio: SQLite local, versiones inmutables y migración segura."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def validate_payload(payload: dict) -> dict:
    value = json.loads(json.dumps(payload, allow_nan=False))
    picks = value.get("picks", [""] * 14)
    if len(picks) != 14 or any(not isinstance(s, str) or not set(s) <= set("1X2") for s in picks):
        raise ValueError("La base debe contener 14 selecciones 1/X/2.")
    value["picks"] = ["".join(s for s in "1X2" if s in p) for p in picks]
    for key in ("columns", "original"):
        cols = value.get(key)
        if cols is not None and (not isinstance(cols, list) or any(
            not isinstance(c, str) or not re.fullmatch(r"[1X2]{14}", c) for c in cols
        )):
            raise ValueError("Las columnas deben tener exactamente 14 signos.")
    pleno = value.get("pleno", "")
    if pleno and not re.fullmatch(r"[012M]-[012M]", pleno):
        raise ValueError("Pleno no válido.")
    return value


class SystemStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.db.close()
            raise ValueError("Esta base de datos pertenece a una versión más reciente.")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS systems (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, season TEXT NOT NULL,
            round_no INTEGER NOT NULL, created TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY, system_id INTEGER NOT NULL REFERENCES systems(id),
            sequence INTEGER NOT NULL, created TEXT NOT NULL, payload TEXT NOT NULL,
            hash TEXT NOT NULL, UNIQUE(system_id,sequence));
          CREATE TABLE IF NOT EXISTS active (
            season TEXT NOT NULL, round_no INTEGER NOT NULL,
            system_id INTEGER NOT NULL REFERENCES systems(id), PRIMARY KEY(season,round_no));
          CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          PRAGMA user_version=1;
        """)

    def get_meta(self, key, default=None):
        row = self.db.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_meta(self, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO metadata VALUES (?,?)", (key, json.dumps(value)))

    def create(self, season: str, round_no: int, name: str, payload: dict) -> int:
        if not re.fullmatch(r"\d{2}-\d{2}", season) or not 1 <= round_no <= 99:
            raise ValueError("Temporada o jornada no válidas.")
        payload = validate_payload(payload)
        if not name.strip():
            raise ValueError("Indica un nombre para el sistema.")
        with self.db:
            result = self.db.execute("INSERT INTO systems(name,season,round_no,created) VALUES (?,?,?,?)",
                                     (name.strip(), season, round_no, self.now()))
            system_id = result.lastrowid
            self._append(system_id, payload)
        return system_id

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _append(self, system_id, payload):
        text = json.dumps(validate_payload(payload), sort_keys=True, ensure_ascii=False, allow_nan=False)
        digest = hashlib.sha256(text.encode()).hexdigest()
        last = self.db.execute("SELECT sequence,hash FROM versions WHERE system_id=? ORDER BY sequence DESC LIMIT 1",
                               (system_id,)).fetchone()
        if last and last["hash"] == digest:
            return
        self.db.execute("INSERT INTO versions(system_id,sequence,created,payload,hash) VALUES (?,?,?,?,?)",
                        (system_id, last["sequence"] + 1 if last else 1, self.now(), text, digest))

    def append(self, system_id, payload):
        if not self.db.execute("SELECT id FROM systems WHERE id=?", (system_id,)).fetchone():
            raise ValueError("Sistema inexistente.")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            self._append(system_id, payload)

    def activate(self, system_id):
        row = self.get(system_id)
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO active VALUES (?,?,?)", (row["season"], row["round_no"], system_id))

    def active(self, season, round_no):
        row = self.db.execute("SELECT system_id FROM active WHERE season=? AND round_no=?", (season, round_no)).fetchone()
        return self.get(row[0]) if row else None

    def get(self, system_id, sequence=None):
        query = """SELECT s.*,v.sequence,v.payload,v.hash FROM systems s JOIN versions v ON v.system_id=s.id
                   WHERE s.id=?"""
        args = [system_id]
        if sequence is not None:
            query += " AND v.sequence=?"
            args.append(sequence)
        row = self.db.execute(query + " ORDER BY v.sequence DESC LIMIT 1", args).fetchone()
        if not row:
            raise ValueError("Sistema o versión no encontrados.")
        result = dict(row)
        if hashlib.sha256(result["payload"].encode()).hexdigest() != result["hash"]:
            raise ValueError("La versión guardada no supera la comprobación de integridad.")
        result["payload"] = validate_payload(json.loads(result["payload"]))
        return result

    def list(self):
        return [self.get(row[0]) for row in self.db.execute("SELECT id FROM systems ORDER BY id DESC").fetchall()]

    def versions(self, system_id):
        return [dict(r) for r in self.db.execute("SELECT sequence,created,hash FROM versions WHERE system_id=? ORDER BY sequence DESC", (system_id,))]

    def migrate_legacy(self, path: Path):
        if self.get_meta("legacy_migrated", False) or not path.exists():
            return
        saved = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(saved, dict):
            raise ValueError("El archivo antiguo no es un diccionario de pronósticos.")
        backup = self.path.parent / "legacy-pronosticos.json"
        if not backup.exists():
            shutil.copy2(path, backup)
        predictions = saved.get("predictions", saved)
        groups = {}
        for key, value in predictions.items():
            m = re.fullmatch(r"(\d{2}-\d{2})-(\d{1,2})-(\d{1,2})", key)
            if not m or not isinstance(value, str):
                continue
            season, number, position = m.groups()
            p = groups.setdefault((season, int(number)), {"picks": [""] * 14, "pleno": "", "source": "Migrado del PC"})
            if 1 <= int(position) <= 14:
                p["picks"][int(position)-1] = value
            elif int(position) == 15:
                p["pleno"] = value
        # Todas las entradas se validan antes de empezar a migrarlas.
        for payload in groups.values():
            validate_payload(payload)
        with self.db:
            for (season, number), payload in groups.items():
                cur = self.db.execute("INSERT INTO systems(name,season,round_no,created) VALUES (?,?,?,?)",
                                      ("Quiniela migrada", season, number, self.now()))
                self._append(cur.lastrowid, payload)
                self.db.execute("INSERT OR IGNORE INTO active VALUES (?,?,?)", (season, number, cur.lastrowid))
            columns = saved.get("development_columns")
            if columns:
                validate_payload({"picks": [""] * 14, "columns": columns})
                # Sin identidad fiable no se vincula el desarrollo a la jornada actual.
                self.db.execute("INSERT OR REPLACE INTO metadata VALUES (?,?)", ("unassigned_legacy", json.dumps(columns)))
            self.db.execute("INSERT OR REPLACE INTO metadata VALUES ('legacy_migrated','true')")

    def close(self):
        self.db.close()
