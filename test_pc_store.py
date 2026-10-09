import json
import tempfile
import unittest
from pathlib import Path
from pc_store import SystemStore


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.store = SystemStore(self.path / "desktop_data" / "systems.sqlite3")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def payload(self, sign="1"):
        return {"picks": [sign] * 14, "columns": [sign * 14], "original": [sign * 14], "pleno": "M-1"}

    def test_versions_are_immutable_and_repeated_saves_do_not_duplicate(self):
        sid = self.store.create("26-27", 12, "Prueba", self.payload())
        self.store.append(sid, self.payload())
        self.assertEqual(len(self.store.versions(sid)), 1)
        self.store.append(sid, self.payload("X"))
        self.assertEqual(self.store.get(sid, 1)["payload"]["columns"], ["1" * 14])
        self.assertEqual(self.store.get(sid)["sequence"], 2)

    def test_rounds_and_systems_do_not_mix(self):
        a = self.store.create("26-27", 11, "A", self.payload())
        b = self.store.create("26-27", 12, "B", self.payload("X"))
        self.store.activate(a)
        self.store.activate(b)
        self.assertEqual(self.store.active("26-27", 11)["id"], a)
        self.assertEqual(self.store.active("26-27", 12)["id"], b)
        self.assertIsNone(self.store.active("25-26", 12))

    def test_invalid_columns_are_rejected_without_new_version(self):
        sid = self.store.create("26-27", 12, "A", self.payload())
        with self.assertRaises(ValueError):
            self.store.append(sid, {"columns": ["123"]})
        self.assertEqual(len(self.store.versions(sid)), 1)

    def test_legacy_backup_and_unassigned_columns_are_preserved(self):
        path = self.path / "pronosticos.json"
        old = {"predictions": {"26-27-11-1": "1X", "26-27-11-15": "M-1", "26-27-12-1": "2"}, "development_columns": ["1" * 14]}
        path.write_text(json.dumps(old), encoding="utf-8")
        before = path.read_bytes()
        self.store.migrate_legacy(path)
        self.assertEqual(self.store.active("26-27", 11)["payload"]["picks"][0], "1X")
        self.assertEqual(self.store.active("26-27", 12)["payload"]["picks"][0], "2")
        self.assertIsNone(self.store.active("26-27", 11)["payload"].get("columns"))
        self.assertEqual(self.store.get_meta("unassigned_legacy"), ["1" * 14])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual((self.store.path.parent / "legacy-pronosticos.json").read_bytes(), before)
        self.store.migrate_legacy(path)
        self.assertEqual(len(self.store.list()), 2)

    def test_invalid_migration_rolls_back_and_does_not_mark_complete(self):
        path = self.path / "pronosticos.json"
        path.write_text(json.dumps({"predictions": {"26-27-12-1": "1"}, "development_columns": ["bad"]}))
        with self.assertRaises(ValueError):
            self.store.migrate_legacy(path)
        self.assertEqual(self.store.list(), [])
        self.assertFalse(self.store.get_meta("legacy_migrated", False))

    def test_corrupted_payload_detected(self):
        sid = self.store.create("26-27", 12, "A", self.payload())
        with self.store.db:
            self.store.db.execute("UPDATE versions SET payload='{}' WHERE system_id=?", (sid,))
        with self.assertRaises(ValueError):
            self.store.get(sid)


if __name__ == "__main__":
    unittest.main()
