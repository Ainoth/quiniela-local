"""SQLite, transacciones, versiones inmutables y copia consistente."""
import json
from pathlib import Path
import sqlite3
import uuid
from .domain import round_dict, round_from_dict, system_dict, system_from_dict, utcnow


class Repository:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute('PRAGMA foreign_keys=ON')
        version = self.db.execute('PRAGMA user_version').fetchone()[0]
        if version > 1:
            raise ValueError('Esta base necesita una versión posterior de Studio.')
        if version == 0:
            with self.db:
                self.db.executescript('''
                BEGIN;
                CREATE TABLE rounds (key TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE systems (id TEXT PRIMARY KEY, round_key TEXT NOT NULL REFERENCES rounds(key));
                CREATE TABLE versions (system_id TEXT REFERENCES systems(id), revision INTEGER,
                    payload TEXT NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(system_id,revision));
                CREATE TABLE audit (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL,
                    action TEXT NOT NULL, system_id TEXT, revision INTEGER, details TEXT NOT NULL);
                PRAGMA user_version=1;
                COMMIT;
                ''')

    def save_round(self, round_):
        with self.db:
            self.db.execute('INSERT INTO rounds VALUES (?,?) ON CONFLICT(key) DO UPDATE SET payload=excluded.payload',
                            (round_.key, json.dumps(round_dict(round_), ensure_ascii=False)))

    def round(self, key):
        row = self.db.execute('SELECT payload FROM rounds WHERE key=?', (key,)).fetchone()
        if row is None:
            raise ValueError('Jornada no encontrada.')
        return round_from_dict(json.loads(row[0]))

    def rounds(self):
        return [round_from_dict(json.loads(row[0])) for row in self.db.execute('SELECT payload FROM rounds ORDER BY key DESC')]

    def save(self, system, action='save'):
        with self.db:
            existing = self.db.execute('SELECT round_key FROM systems WHERE id=?', (system.system_id,)).fetchone()
            if existing and existing[0] != system.round_key:
                raise ValueError('Un sistema no se puede reasignar a otra jornada.')
            latest = self.db.execute('SELECT COALESCE(MAX(revision),0) FROM versions WHERE system_id=?', (system.system_id,)).fetchone()[0]
            if system.revision != latest + 1:
                raise ValueError('La versión ha cambiado; vuelve a abrir el sistema.')
            self.db.execute('INSERT OR IGNORE INTO systems VALUES (?,?)', (system.system_id, system.round_key))
            self.db.execute('INSERT INTO versions VALUES (?,?,?,?)',
                            (system.system_id, system.revision, json.dumps(system_dict(system), ensure_ascii=False), system.hash))
            self.db.execute('INSERT INTO audit(created_at,action,system_id,revision,details) VALUES (?,?,?,?,?)',
                            (utcnow(), action, system.system_id, system.revision, system.origin))

    def load(self, system_id, revision=None):
        if revision is None:
            row = self.db.execute('SELECT payload,hash FROM versions WHERE system_id=? ORDER BY revision DESC LIMIT 1', (system_id,)).fetchone()
        else:
            row = self.db.execute('SELECT payload,hash FROM versions WHERE system_id=? AND revision=?', (system_id, revision)).fetchone()
        if row is None:
            raise ValueError('Sistema no encontrado.')
        system = system_from_dict(json.loads(row[0]))
        if system.hash != row[1]:
            raise ValueError('El contenido del sistema no coincide con su hash.')
        return system

    def systems(self, round_key=None):
        query = 'SELECT id FROM systems' + (' WHERE round_key=?' if round_key else '')
        return [self.load(row[0]) for row in self.db.execute(query, (round_key,) if round_key else ())]

    def audit(self):
        return self.db.execute('SELECT created_at,action,revision,details FROM audit ORDER BY id DESC LIMIT 100').fetchall()

    def backup(self, target):
        target = Path(target)
        if target.resolve() == self.path.resolve() or target.exists():
            raise ValueError('Elige un archivo de copia nuevo, distinto de la base activa.')
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(target) as backup_db:
            self.db.backup(backup_db)

    def close(self):
        self.db.close()
