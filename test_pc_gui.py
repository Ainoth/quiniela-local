"""Pruebas GUI opt-in; solo escriben en directorios temporales de fixtures."""
import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import app
from test_pc_data import percentages_xml


@unittest.skipUnless(os.environ.get("RUN_PC_GUI_TESTS") == "1", "Activar RUN_PC_GUI_TESTS=1 con una pantalla disponible")
class GuiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        data = self.directory / "Datosg"
        data.mkdir()
        cache = self.directory / "cache"
        cache.mkdir()
        self.cache = cache
        today = date.today()
        codes = ''.join(f"A{i:02}B{i:02}" for i in range(15))
        for season in ("26-27", "25-26"):
            days = [(10, today-timedelta(days=1)), (11, today), (12, today+timedelta(days=1))]
            (data / f"FEC{season}.txt").write_text('\n'.join(f"{n:02}:{day:%d/%m/%Y}" for n, day in days))
            (data / f"Hor{season}.txt").write_text('\n'.join(f"{n:02}"+(f"{day:%d/%m/%Y}20:45"*15) for n, day in days))
            (data / f"PRE{season}.txt").write_text('\n'.join(
                ("100 2 3 4 5 6 200,00 100,00 50,00 20,00 5,00 2,00".ljust(104)+"1"*14+"0" if n == 10 else str(n).ljust(119))+codes for n, _d in days))
        (data / "WEQUIPOS.TXT").write_text('\n'.join(f"{s}{i:02}-Equipo {s}{i}" for s in "AB" for i in range(15)))
        (cache / "porcentajes_26-27_J11.xml").write_bytes(percentages_xml(number=11))
        self.patches = [patch.object(app, "DATA", data), patch.object(app, "CACHE_DIR", cache),
                        patch.object(app, "STATE_DIR", self.directory), patch.object(app, "STATE_FILE", self.directory/"pronosticos.json"),
                        patch.object(app.messagebox, "showerror", side_effect=lambda *a, **k: self.fail(str(a))),
                        patch.object(app.messagebox, "showwarning", return_value=None)]
        for p in self.patches:
            p.start()
        self.ui = app.QuinielaApp()
        self.ui.update()

    def tearDown(self):
        if hasattr(self, "ui"):
            self.ui.close_app()
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_sections_layout_and_round_guards(self):
        self.assertEqual(self.ui.round_no, 11)
        for size in ("1024x678", "1320x790"):
            self.ui.geometry(size)
            self.ui.update()
            for name in self.ui.SECTIONS:
                self.ui.nav_buttons[name].invoke()
                self.ui.update()
                frame = self.ui.pages[name][0]
                self.assertTrue(frame.winfo_ismapped())
                self.assertLessEqual(frame.winfo_rootx()+frame.winfo_width(), self.ui.winfo_rootx()+self.ui.winfo_width())
            self.assertLessEqual(self.ui.status.winfo_rooty()+self.ui.status.winfo_height(), self.ui.winfo_rooty()+self.ui.winfo_height())
        self.ui.pick_buttons[(1, "X")].invoke()
        self.assertEqual(self.ui.predictions[self.ui._key(self.ui.matches[0])], "X")
        self.ui.move_round(-1)
        self.assertFalse(self.ui._editable())
        before = dict(self.ui.predictions)
        self.ui._toggle_pick_by_number(1, "2")
        self.assertEqual(self.ui.predictions, before)
        self.ui.go_current_round()
        self.assertEqual(self.ui.predictions[self.ui._key(self.ui.matches[0])], "X")
        self.ui.move_round(1)
        self.assertFalse(self.ui._editable())
        self.assertIsNone(self.ui.current_development_columns)
        self.ui.go_current_round()
        self.ui.browse_season.set("25-26")
        self.ui.select_season()
        self.assertFalse(self.ui._editable())

    def test_source_separation_generation_budget_and_restore(self):
        self.assertEqual(self.ui.matches[0].probabilities, (40, 30, 30))
        self.assertEqual(self.ui.matches[0].public_percentages, (50, 30, 20))
        self.ui.probability_source.set("Porcentajes jugados")
        self.ui.change_probability_source()
        self.assertEqual(self.ui.matches[0].probabilities, (50, 30, 20))
        self.ui.open_system()
        self.ui.update()
        generated = list(self.ui.current_development_columns)
        self.assertEqual(len(generated), 10)
        self.assertEqual(self.ui.original_development_columns, generated)
        for d in list(self.ui.winfo_children()):
            if isinstance(d, app.tk.Toplevel):
                d.destroy()
        self.ui.open_budget_optimizer()
        self.ui.update()
        dialog = next(d for d in self.ui.winfo_children() if isinstance(d, app.tk.Toplevel))
        amount = next(w for w in self.walk(dialog) if isinstance(w, app.ttk.Entry))
        calculate = next(w for w in self.walk(dialog) if isinstance(w, app.ttk.Button) and str(w.cget("text")) == "Calcular")
        amount.delete(0, "end")
        amount.insert(0, "1,50")
        calculate.invoke()
        self.ui.update()
        self.assertEqual(len(self.ui.current_development_columns), 2)
        amount.delete(0, "end")
        amount.insert(0, "7,50")
        calculate.invoke()
        self.ui.update()
        self.assertEqual(len(self.ui.current_development_columns), 10)
        dialog.destroy()
        plan = self.ui.budget_plans(1.5, self.ui.original_development_columns)[0]
        self.ui.apply_development_to_main(columns=plan.columns, preserve_origin=True)
        self.assertEqual(len(self.ui.current_development_columns), 2)
        self.assertEqual(self.ui.original_development_columns, generated)
        self.ui.move_round(-1)
        self.ui.go_current_round()
        self.assertEqual(len(self.ui.current_development_columns), 2)
        self.ui.restore_original()
        self.assertEqual(self.ui.current_development_columns, generated)
        self.ui._set_pleno_goal("home", "M")
        self.ui._set_pleno_goal("away", "1")
        self.assertTrue(all(len(line) == 16 for line in app.quinielista_text(generated, "M-1").splitlines()))
        self.ui.close_app()
        self.ui = app.QuinielaApp()
        self.assertEqual(self.ui.current_development_columns, generated)
        self.assertEqual(self.ui.pleno_home.get(), "M")

    @staticmethod
    def walk(widget):
        for child in widget.winfo_children():
            yield child
            yield from GuiTests.walk(child)

    def test_advanced_preserves_manual_base_and_generation_buttons(self):
        self.ui.use_suggestions()
        self.ui._toggle_pick_by_number(1, "X")
        self.ui.open_advanced()
        self.ui.update()
        dialog = next(d for d in self.ui.winfo_children() if isinstance(d, app.tk.Toplevel))
        scales = [w for w in self.walk(dialog) if isinstance(w, app.tk.Scale)]
        self.assertEqual(len(scales), 2)
        # Abrir el editor no activa filtros ni cambia la base guardada.
        generate = next(w for w in self.walk(dialog) if isinstance(w, app.ttk.Button) and "Crear desarrollo" in str(w.cget("text")))
        generate.invoke()
        self.ui.update()
        self.assertEqual(set(self.ui.current_development_columns), {"1"*14, "X"+"1"*13})
        scales[0].set(5)
        scales[1].set(0)
        self.ui.update()
        generate.invoke()
        self.ui.update()
        self.assertTrue(self.ui.current_development_columns)
        self.assertEqual(self.ui.original_development_columns, self.ui.current_development_columns)
        for w in self.walk(dialog):
            if isinstance(w, app.ttk.Button) and w.winfo_ismapped():
                self.assertLessEqual(w.winfo_rooty()+w.winfo_height(), dialog.winfo_rooty()+dialog.winfo_height())
        original = list(self.ui.current_development_columns)
        self.ui.move_round(-1)
        generate.invoke()
        self.ui.go_current_round()
        self.assertEqual(self.ui.current_development_columns, original)
        dialog.destroy()

    def test_scrutator_does_not_fallback_to_wrong_round(self):
        import time
        with patch.object(app, "fetch_live_results", side_effect=ValueError("El proveedor no ofrece el directo")) as fetch:
            self.ui.open_prize_checker()
            dialog = next(d for d in self.ui.winfo_children() if isinstance(d, app.tk.Toplevel))
            deadline = time.monotonic()+2
            while fetch.call_count == 0 and time.monotonic() < deadline:
                self.ui.update()
                time.sleep(.01)
            self.ui.update()
            self.assertEqual(fetch.call_args_list, [unittest.mock.call("26-27", 11)])
            next(w for w in self.walk(dialog) if isinstance(w, app.ttk.Button) and str(w.cget("text")) == "Cerrar").invoke()

    def test_assigning_legacy_to_past_round_creates_readonly_archive(self):
        self.ui.store.set_meta("unassigned_legacy", ["X"*14])
        self.ui.move_round(-1)
        self.assertEqual(self.ui.round_no, 10)
        with patch.object(app.messagebox, "askokcancel", return_value=True):
            self.ui.assign_legacy()
        self.assertEqual(self.ui.current_development_columns, ["X"*14])
        self.assertFalse(self.ui._editable())
        self.assertIsNone(self.ui.store.get_meta("unassigned_legacy"))
        before = self.ui.system_payload()
        self.ui.clear_picks()
        self.assertEqual(before, self.ui.system_payload())


if __name__ == "__main__":
    unittest.main()
