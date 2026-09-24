#!/usr/bin/env python3
"""Quiniela Local: visor y editor local para los datos de WIN1X2."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import webbrowser
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("WIN1X2_DATA_DIR", ROOT / "Datosg")).expanduser().resolve()
STATE_FILE = Path(__file__).resolve().parent / "pronosticos.json"


@dataclass
class Match:
    number: int
    home_code: str
    away_code: str
    home: str
    away: str
    kickoff: str
    probabilities: tuple[float, float, float]
    detail: str

    @property
    def suggestion(self) -> str:
        return ("1", "X", "2")[self.probabilities.index(max(self.probabilities))]


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def season_files() -> tuple[Path, Path, str]:
    candidates = sorted(DATA.glob("FEC*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("No se encontró FEC*.txt en Datosg")
    dates = candidates[0]
    season = dates.stem[3:]
    schedule = next(iter(DATA.glob(f"Hor{season}.txt")), DATA / f"Hor{season}.txt")
    if not schedule.exists():
        schedule = next(iter(DATA.glob(f"HOR{season}.txt")), schedule)
    return dates, schedule, season


def load_team_names() -> dict[str, str]:
    names: dict[str, str] = {}
    sources = [DATA / "WEQUIPOS.TXT", *DATA.glob("EQ*.txt"), *DATA.glob("EQ*.TXT")]
    for path in sources:
        if not path.exists():
            continue
        for line in read_text(path).splitlines():
            if "-" not in line:
                continue
            code, name = line.split("-", 1)
            code = code.strip().upper()
            if len(code) == 3:
                names[code] = name.strip()
    return names


def parse_dates(path: Path) -> list[tuple[int, date]]:
    entries = []
    for line in read_text(path).splitlines():
        match = re.match(r"(\d{2}):(\d{2}/\d{2}/\d{4})", line)
        if match:
            entries.append((int(match.group(1)), datetime.strptime(match.group(2), "%d/%m/%Y").date()))
    return entries


def current_round(entries: list[tuple[int, date]], today: date | None = None) -> int:
    today = today or date.today()
    future = [(abs((day - today).days), round_no) for round_no, day in entries if day >= today]
    if future:
        return min(future)[1]
    return entries[-1][0]


def parse_round_teams(season: str, round_no: int) -> list[tuple[str, str]]:
    path = DATA / f"PRE{season}.txt"
    if not path.exists():
        matches = list(DATA.glob(f"Pre{season}.txt"))
        if not matches:
            raise FileNotFoundError(f"No se encontró PRE{season}.txt")
        path = matches[0]
    lines = read_text(path).splitlines()
    line = next((s for s in lines if int((re.match(r"\d+", s) or ["-1"])[0]) == round_no), None)
    if line is None or len(line) < 209:
        raise ValueError(f"La jornada {round_no} no está disponible en {path.name}")
    block = line[119:209]
    codes = [block[i : i + 3].upper() for i in range(0, 90, 3)]
    return list(zip(codes[::2], codes[1::2]))


def parse_kickoffs(path: Path, round_no: int) -> list[str]:
    line = next((s for s in read_text(path).splitlines() if s.startswith(f"{round_no:02d}")), "")
    payload = line[2:]
    return [payload[i : i + 15] for i in range(0, min(len(payload), 225), 15)]


def parse_results(path: Path, before_round: int) -> list[tuple[str, str, int, int]]:
    text = "".join(read_text(path).split())
    records = []
    for offset in range(0, len(text) - 15, 16):
        item = text[offset : offset + 16]
        if not re.fullmatch(r"\d{4}.{3}.{3}.{2}\d{4}", item):
            continue
        round_no = int(item[:2])
        if round_no >= before_round or not item[10:12].isdigit():
            continue
        records.append((item[4:7], item[7:10], int(item[10]), int(item[11])))
    return records


def build_form(season: str, before_round: int):
    games = []
    for division in (1, 2):
        path = DATA / f"RS{division}{season}.txt"
        if path.exists():
            games.extend(parse_results(path, before_round))
    history: dict[str, list[tuple[int, int, bool]]] = defaultdict(list)
    for home, away, gh, ga in games:
        history[home].append((gh, ga, True))
        history[away].append((ga, gh, False))
    return history


def probabilities(home: str, away: str, history) -> tuple[tuple[float, float, float], str]:
    def strength(code: str):
        recent = history.get(code, [])[-8:]
        if not recent:
            return 1.0, 1.0, 0, "sin historial"
        points = sum(3 if gf > ga else 1 if gf == ga else 0 for gf, ga, _ in recent)
        gf = sum(x[0] for x in recent)
        ga = sum(x[1] for x in recent)
        rating = (points + 3) / (len(recent) * 1.7 + 3) + (gf - ga) * 0.035
        return max(0.25, rating), points / (3 * len(recent)), len(recent), f"{points} pts en {len(recent)}"

    hs, hf, hn, hd = strength(home)
    aws, af, an, ad = strength(away)
    if hn == 0 and an == 0:
        probs = (0.40, 0.30, 0.30)
    else:
        delta = math.log((hs + 0.15) / (aws + 0.15)) + 0.24
        draw = max(0.22, 0.30 - abs(delta) * 0.055)
        remaining = 1 - draw
        home_share = 1 / (1 + math.exp(-1.25 * delta))
        probs = (remaining * home_share, draw, remaining * (1 - home_share))
    total = sum(probs)
    probs = tuple(round(p * 100 / total, 1) for p in probs)
    return probs, f"Local: {hd}; visitante: {ad}. Modelo simple de forma reciente + ventaja local."


def load_matches(today: date | None = None) -> tuple[str, int, list[Match]]:
    dates_file, schedule_file, season = season_files()
    round_no = current_round(parse_dates(dates_file), today)
    pairs = parse_round_teams(season, round_no)
    kickoffs = parse_kickoffs(schedule_file, round_no)
    names = load_team_names()
    history = build_form(season, round_no)
    matches = []
    for index, (home, away) in enumerate(pairs, 1):
        probs, detail = probabilities(home, away, history)
        kickoff = kickoffs[index - 1] if index <= len(kickoffs) else ""
        if len(kickoff) == 15:
            kickoff = f"{kickoff[:10]} {kickoff[10:]}"
        matches.append(Match(index, home, away, names.get(home, home), names.get(away, away), kickoff, probs, detail))
    return season, round_no, matches


class QuinielaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiniela Local")
        self.geometry("1080x690")
        self.minsize(850, 540)
        self.predictions: dict[str, str] = {}
        self.matches: list[Match] = []
        self._build_ui()
        self._load_state()
        self.refresh()

    def _build_ui(self):
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=29, font=("Sans", 10))
        style.configure("Treeview.Heading", font=("Sans", 10, "bold"))

        header = ttk.Frame(self, padding=(16, 14, 16, 8))
        header.pack(fill="x")
        ttk.Label(header, text="Quiniela Local", font=("Sans", 20, "bold")).pack(side="left")
        self.subtitle = ttk.Label(header, text="", font=("Sans", 11))
        self.subtitle.pack(side="left", padx=18)
        ttk.Button(header, text="Actualizar datos", command=self.refresh).pack(side="right")

        columns = ("n", "date", "home", "away", "p1", "px", "p2", "suggestion", "pick")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        labels = ("#", "Fecha y hora", "Local", "Visitante", "% 1", "% X", "% 2", "Sugerencia", "Mi signo")
        widths = (38, 135, 170, 170, 58, 58, 58, 83, 75)
        for column, label, width in zip(columns, labels, widths):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor="center" if column not in ("home", "away") else "w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self._show_detail)
        self.tree.bind("<Double-1>", lambda _event: self.set_pick(self._selected_suggestion()))

        controls = ttk.Frame(self, padding=(16, 8))
        controls.pack(fill="x")
        ttk.Label(controls, text="Signo del partido seleccionado:").pack(side="left")
        for sign in ("1", "X", "2"):
            ttk.Button(controls, text=sign, width=5, command=lambda s=sign: self.set_pick(s)).pack(side="left", padx=3)
        ttk.Button(controls, text="Usar sugerencias", command=self.use_suggestions).pack(side="left", padx=(18, 3))
        ttk.Button(controls, text="Limpiar", command=self.clear_picks).pack(side="left", padx=3)
        ttk.Button(controls, text="Abrir TULOTERO", command=self.open_tulotero).pack(side="right", padx=(3, 0))
        ttk.Button(controls, text="Copiar apuesta", command=self.copy_bet).pack(side="right", padx=3)
        ttk.Button(controls, text="Exportar…", command=self.export).pack(side="right")

        self.detail = ttk.Label(self, text="", padding=(16, 4, 16, 14), foreground="#444")
        self.detail.pack(fill="x")
        self.status = ttk.Label(self, text="", relief="sunken", padding=(8, 4))
        self.status.pack(fill="x", side="bottom")

    def _key(self, match: Match) -> str:
        return f"{self.season}-{self.round_no}-{match.number}"

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                self.predictions = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.predictions = {}

    def _save_state(self):
        STATE_FILE.write_text(json.dumps(self.predictions, ensure_ascii=False, indent=2), encoding="utf-8")

    def refresh(self):
        try:
            self.season, self.round_no, self.matches = load_matches()
        except Exception as exc:
            messagebox.showerror("No se pudieron leer los datos", str(exc))
            return
        self.subtitle.configure(text=f"Temporada {self.season} · Jornada {self.round_no}")
        for item in self.tree.get_children():
            self.tree.delete(item)
        for match in self.matches:
            p1, px, p2 = match.probabilities
            self.tree.insert("", "end", iid=str(match.number), values=(
                match.number, match.kickoff, match.home, match.away,
                f"{p1:.1f}", f"{px:.1f}", f"{p2:.1f}", match.suggestion,
                self.predictions.get(self._key(match), "—"),
            ))
        stamp = max((p.stat().st_mtime for p in DATA.iterdir() if p.is_file()), default=0)
        updated = datetime.fromtimestamp(stamp).strftime("%d/%m/%Y %H:%M")
        self.status.configure(text=f"15 partidos cargados · Datos WIN1X2 actualizados: {updated} · Guardado local automático")
        if self.matches:
            self.tree.selection_set("1")

    def selected(self) -> Match | None:
        selection = self.tree.selection()
        return self.matches[int(selection[0]) - 1] if selection else None

    def _selected_suggestion(self) -> str:
        match = self.selected()
        return match.suggestion if match else "1"

    def set_pick(self, sign: str):
        match = self.selected()
        if not match:
            return
        if match.number == 15:
            self.set_pleno(match)
            return
        self.predictions[self._key(match)] = sign
        self.tree.set(str(match.number), "pick", sign)
        self._save_state()
        next_number = match.number + 1
        if next_number <= len(self.matches):
            self.tree.selection_set(str(next_number))
            self.tree.see(str(next_number))

    def use_suggestions(self):
        for match in self.matches:
            value = "1-1" if match.number == 15 else match.suggestion
            self.predictions[self._key(match)] = value
            self.tree.set(str(match.number), "pick", value)
        self._save_state()

    def set_pleno(self, match: Match):
        dialog = tk.Toplevel(self)
        dialog.title("Pleno al 15")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=18)
        frame.pack()
        ttk.Label(frame, text=f"{match.home} – {match.away}", font=("Sans", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 12))
        ttk.Label(frame, text="Goles local").grid(row=1, column=0, padx=6)
        ttk.Label(frame, text="Goles visitante").grid(row=1, column=1, padx=6)
        current = self.predictions.get(self._key(match), "1-1").split("-")
        home_goals = tk.StringVar(value=current[0])
        away_goals = tk.StringVar(value=current[-1])
        ttk.Combobox(frame, textvariable=home_goals, values=("0", "1", "2", "M"), state="readonly", width=8).grid(row=2, column=0, padx=6, pady=6)
        ttk.Combobox(frame, textvariable=away_goals, values=("0", "1", "2", "M"), state="readonly", width=8).grid(row=2, column=1, padx=6, pady=6)

        def save():
            value = f"{home_goals.get()}-{away_goals.get()}"
            self.predictions[self._key(match)] = value
            self.tree.set(str(match.number), "pick", value)
            self._save_state()
            dialog.destroy()

        ttk.Button(frame, text="Guardar marcador", command=save).grid(row=3, column=0, columnspan=2, pady=(10, 0))
        dialog.wait_window()

    def clear_picks(self):
        for match in self.matches:
            self.predictions.pop(self._key(match), None)
            self.tree.set(str(match.number), "pick", "—")
        self._save_state()

    def _show_detail(self, _event=None):
        match = self.selected()
        if match:
            self.detail.configure(text=f"{match.home_code}–{match.away_code}: {match.detail}")

    def export(self):
        target = filedialog.asksaveasfilename(
            title="Exportar pronóstico", defaultextension=".txt",
            initialfile=f"quiniela_{self.season}_J{self.round_no:02d}.txt",
            filetypes=(("Texto", "*.txt"), ("Todos", "*.*")),
        )
        if not target:
            return
        lines = [f"QUINIELA · Temporada {self.season} · Jornada {self.round_no}", ""]
        for match in self.matches:
            sign = self.predictions.get(self._key(match), "—")
            lines.append(f"{match.number:>2}. {match.home} - {match.away}: {sign}")
        Path(target).write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.status.configure(text=f"Pronóstico exportado en {target}")

    def bet_text(self) -> str | None:
        values = [self.predictions.get(self._key(match), "") for match in self.matches]
        missing = [str(index + 1) for index, value in enumerate(values) if not value]
        if missing:
            messagebox.showwarning("Apuesta incompleta", "Faltan los partidos: " + ", ".join(missing))
            return None
        if any(value not in ("1", "X", "2") for value in values[:14]):
            messagebox.showwarning("Signos no válidos", "Los partidos 1 a 14 deben contener 1, X o 2.")
            return None
        if not re.fullmatch(r"[012M]-[012M]", values[14]):
            messagebox.showwarning("Pleno no válido", "El Pleno al 15 debe tener el formato 0/1/2/M–0/1/2/M.")
            return None
        return f"Jornada {self.round_no} ({self.season}) · 1-14: {''.join(values[:14])} · Pleno al 15: {values[14]}"

    def copy_bet(self) -> bool:
        text = self.bet_text()
        if not text:
            return False
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.status.configure(text="Apuesta copiada. Revisa todos los signos antes de confirmar cualquier compra.")
        return True

    def open_tulotero(self):
        if not self.copy_bet():
            return
        if messagebox.askokcancel(
            "Abrir TULOTERO",
            "Se abrirá la web oficial. La app no enviará ni comprará la apuesta automáticamente.\n\n"
            "Comprueba la jornada, los 14 signos, el Pleno al 15 y el importe antes de confirmar.",
        ):
            webbrowser.open("https://tulotero.es/quiniela/")


def check() -> int:
    season, round_no, matches = load_matches()
    print(f"Temporada {season}; jornada {round_no}; {len(matches)} partidos")
    for match in matches:
        print(f"{match.number:02d} {match.home} - {match.away} | {match.kickoff} | {match.probabilities} => {match.suggestion}")
    return 0 if len(matches) == 15 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="comprueba la lectura sin abrir la interfaz")
    args = parser.parse_args()
    raise SystemExit(check()) if args.check else QuinielaApp().mainloop()
