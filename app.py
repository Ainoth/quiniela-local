#!/usr/bin/env python3
"""Quiniela Local: visor y editor local para los datos de WIN1X2."""

from __future__ import annotations

import argparse
import heapq
import json
import math
import os
import re
import threading
import webbrowser
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from quiniela_engine import (
    FilterConfig, analyze, development_size, filter_columns, generate_columns,
    rank_columns, reduce_columns,
)
from data_updater import fetch_percentages, read_percentages, update_win1x2_files


ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("WIN1X2_DATA_DIR", ROOT / "Datosg")).expanduser().resolve()
APP_DIR = Path(__file__).resolve().parent
STATE_FILE = APP_DIR / "pronosticos.json"
CACHE_DIR = APP_DIR / "cache"
WINDOW_ICON = APP_DIR / "assets" / "quiniela-local.png"
QUINIELISTA_UPLOAD_URL = "https://www.eduardolosilla.es/quiniela/archivos"
BET_PRICE = 0.75
OFFICIAL_REDUCTIONS = (
    ("Reducción 1", 0, 4, 9),
    ("Reducción 2", 7, 0, 16),
    ("Reducción 3", 3, 3, 24),
    ("Reducción 4", 6, 2, 64),
    ("Reducción 5", 0, 8, 81),
    ("Reducción 6", 11, 0, 132),
)


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


@dataclass
class Plan:
    name: str
    bets: int
    cost: float
    coverage: float
    selections: list[str]
    note: str
    columns: list[str] | None = None


def quinielista_text(columns, pleno: str) -> str:
    """Devuelve apuestas de 16 signos en el formato TXT de Quinielista."""
    suffix = ""
    cleaned_pleno = pleno.replace("-", "").upper().strip()
    if not re.fullmatch(r"[012M]{2}", cleaned_pleno):
        raise ValueError("Define el Pleno al 15 con dos signos: 0, 1, 2 o M.")
    suffix = cleaned_pleno

    lines = []
    for column in columns:
        compact = "".join(column).replace(" ", "").upper()
        if not re.fullmatch(r"[1X2]{14}", compact):
            raise ValueError("Cada columna debe contener exactamente 14 signos 1, X o 2.")
        lines.append(compact + suffix)
    if not lines:
        raise ValueError("No hay columnas para exportar.")
    return "\n".join(lines) + "\n"


def read_bet_file(path: Path) -> list[str]:
    """Lee un TXT de apuestas: 14 signos, o 14 signos más el Pleno al 15."""
    bets = [line.strip().upper().replace(" ", "") for line in read_text(path).splitlines() if line.strip()]
    if not bets or any(not re.fullmatch(r"[1X2]{14}(?:[012M]{2})?", bet) for bet in bets):
        raise ValueError("El archivo debe contener una apuesta de 14 o 16 signos por línea.")
    return bets


def decode_pleno(code: str) -> str:
    """Convierte la codificación hexadecimal 0..F de WIN1X2 a un Pleno 0/1/2/M."""
    goals = "012M"
    try:
        value = int(code, 16)
    except ValueError:
        return ""
    return goals[value // 4] + goals[value % 4] if 0 <= value < 16 else ""


def parse_scrutiny(path: Path, round_no: int):
    """Extrae resultado y premios de una jornada del fichero PRE de WIN1X2."""
    line = next(
        (item for item in read_text(path).splitlines() if re.match(r"\d+", item) and int(re.match(r"\d+", item).group()) == round_no),
        "",
    )
    # Los 15 caracteres inmediatamente anteriores al bloque de equipos (posición 119)
    # son los 14 signos y el código hexadecimal del Pleno.
    result = line[104:118].strip().upper() if len(line) >= 119 else ""
    if not re.fullmatch(r"[1X2]{14}", result):
        return None
    pleno = decode_pleno(line[118].upper())
    tokens = re.findall(r"\d[\d.]*,\d{2}|\d+", line[:104])
    counts = [int(token) for token in tokens[1:7]] if len(tokens) >= 7 else []
    amounts = [float(token.replace(".", "").replace(",", ".")) for token in tokens[7:13]] if len(tokens) >= 13 else []
    prizes = {}
    for category, winners, amount in zip((15, 14, 13, 12, 11, 10), counts, amounts):
        prizes[category] = (winners, amount)
    return {"result": result, "pleno": pleno, "prizes": prizes}


def evaluate_bets(bets: list[str], result: str, pleno: str) -> list[dict]:
    evaluations = []
    for bet in bets:
        hits = sum(sign == winner for sign, winner in zip(bet[:14], result))
        pleno_hit = len(bet) == 16 and bet[14:] == pleno
        category = 15 if hits == 14 and pleno_hit else hits
        evaluations.append({"bet": bet, "hits": hits, "pleno_hit": pleno_hit, "category": category})
    return evaluations


def best_multiple_structure(matches: list[Match], max_bets: int, exact_counts: tuple[int, int] | None = None):
    """Optimiza signos simples/dobles/triples por masa de probabilidad cubierta."""
    # Estado: (apuestas, dobles, triples) -> (log(cobertura), selecciones)
    states = {(1, 0, 0): (0.0, [])}
    for match in matches[:14]:
        ordered = sorted(zip(("1", "X", "2"), match.probabilities), key=lambda item: item[1], reverse=True)
        options = []
        for size in (1, 2, 3):
            signs = "".join(item[0] for item in ordered[:size])
            mass = sum(item[1] for item in ordered[:size]) / 100
            options.append((size, signs, mass))
        next_states = {}
        for (bets, doubles, triples), (score, picks) in states.items():
            for size, signs, mass in options:
                new_bets = bets * size
                if new_bets > max_bets:
                    continue
                key = (new_bets, doubles + (size == 2), triples + (size == 3))
                value = (score + math.log(max(mass, 1e-12)), picks + [signs])
                if key not in next_states or value[0] > next_states[key][0]:
                    next_states[key] = value
        states = next_states
    candidates = []
    for (bets, doubles, triples), (score, picks) in states.items():
        if exact_counts and (doubles, triples) != exact_counts:
            continue
        if not exact_counts and bets < 2:
            continue
        candidates.append((score, bets, doubles, triples, picks))
    return max(candidates, default=None, key=lambda item: item[0])


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
        # JJPP + local(3) + visitante(3) + goles(2) + año(4).
        # Los encuentros pendientes llevan dos espacios en el marcador.
        if not re.fullmatch(r"\d{4}[A-Z0-9]{6}(?:\d{2}| {2})\d{4}", item):
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


def historical_results(team_code: str, limit: int = 40) -> list[tuple[str, str, str, int, int]]:
    """Lee el archivo histórico de WIN1X2: temporada, rival, campo y marcador."""
    path = DATA / "estaresu.txt"
    if not path.exists():
        return []
    text = read_text(path).upper()
    games: list[tuple[str, str, str, int, int]] = []
    # Registros históricos: local(3), visitante(3), temporada(2), goles local y visitante.
    for match in re.finditer(r"([A-Z0-9]{3})([A-Z0-9]{3})(\d{2})(\d)(\d)", text):
        home, away, season, home_goals, away_goals = match.groups()
        if team_code == home:
            games.append((season, away, "Local", int(home_goals), int(away_goals)))
        elif team_code == away:
            games.append((season, home, "Visitante", int(away_goals), int(home_goals)))
    return games[-limit:][::-1]


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
    downloaded_percentages = read_percentages(season, round_no, CACHE_DIR)
    matches = []
    for index, (home, away) in enumerate(pairs, 1):
        internet_probs = downloaded_percentages[index - 1] if downloaded_percentages and index <= 14 else None
        if internet_probs and 99.0 <= sum(internet_probs) <= 101.0:
            probs = tuple(round(value, 2) for value in internet_probs)
            detail = "Porcentajes jugados de Quinielista descargados directamente de Internet."
        else:
            probs, detail = probabilities(home, away, history)
        kickoff = kickoffs[index - 1] if index <= len(kickoffs) else ""
        if len(kickoff) == 15:
            kickoff = f"{kickoff[:10]} {kickoff[10:]}"
        matches.append(Match(index, home, away, names.get(home, home), names.get(away, away), kickoff, probs, detail))
    return season, round_no, matches


def data_update_time(season: str) -> datetime:
    """Fecha más reciente de los ficheros de WIN1X2 usados por la aplicación."""
    patterns = (
        f"FEC{season}.txt", f"PRE{season}.txt", f"Hor{season}.txt",
        f"HOR{season}.txt", f"RS1{season}.txt", f"RS2{season}.txt",
        "WEQUIPOS.TXT",
    )
    files = [path for pattern in patterns for path in DATA.glob(pattern) if path.is_file()]
    if not files:
        raise FileNotFoundError(f"No hay datos utilizables en {DATA}")
    return datetime.fromtimestamp(max(path.stat().st_mtime for path in files))


def compact_kickoff(value: str) -> str:
    try:
        moment = datetime.strptime(value, "%d/%m/%Y %H:%M")
    except ValueError:
        return value
    days = ("LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM")
    return f"{days[moment.weekday()]} {moment:%H:%M}"


class QuinielaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiniela Local")
        self._window_icon = None
        if WINDOW_ICON.exists():
            try:
                self._window_icon = tk.PhotoImage(file=str(WINDOW_ICON))
                # True establece el mismo icono como predeterminado para los Toplevel.
                self.iconphoto(True, self._window_icon)
            except tk.TclError:
                self._window_icon = None
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{min(1320, screen_width - 40)}x{min(790, screen_height - 90)}")
        self.minsize(min(1050, screen_width - 40), min(650, screen_height - 90))
        self.configure(background="#06162c")
        self.predictions: dict[str, str] = {}
        self.matches: list[Match] = []
        self.current_development_columns: list[str] | None = None
        self.current_development_source = ""
        self._build_ui()
        self._load_state()
        self.refresh()

    def _fit_dialog(self, dialog: tk.Toplevel, width: int, height: int, min_width: int, min_height: int):
        """Ajusta un diálogo al escritorio dejando espacio para paneles y barra inferior."""
        available_width = max(520, dialog.winfo_screenwidth() - 40)
        available_height = max(420, dialog.winfo_screenheight() - 110)
        actual_width = min(width, available_width)
        actual_height = min(height, available_height)
        dialog.geometry(f"{actual_width}x{actual_height}")
        dialog.minsize(min(min_width, available_width), min(min_height, available_height))

    def _build_ui(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#071a33")
        style.configure("TLabel", background="#071a33", foreground="#eaf4ff", font=("Sans", 10))
        style.configure("Hero.TFrame", background="#0b315c")
        style.configure("Hero.TLabel", background="#172a46", foreground="white")
        style.configure("Hero.TLabel", background="#0b315c", foreground="white")
        style.configure("Muted.TLabel", background="#071a33", foreground="#8fb5d8")
        style.configure("Accent.TButton", font=("Sans", 10, "bold"), foreground="white", background="#078bd8", bordercolor="#35c8ff", padding=(14, 9))
        style.map("Accent.TButton", background=[("active", "#12a7f4")])
        style.configure("Soft.TButton", background="#123b65", foreground="#eaf6ff", bordercolor="#2d6b9e", padding=(11, 8))
        style.map("Soft.TButton", background=[("active", "#1a568c")])
        style.configure("TButton", background="#123b65", foreground="#f4f9ff", bordercolor="#2d6b9e", padding=(8, 6))
        style.map("TButton", background=[("active", "#1a568c")])
        style.configure("Treeview", rowheight=31, font=("Sans", 10), background="#0b2442", fieldbackground="#0b2442", foreground="#eef7ff", bordercolor="#2a5b88")
        style.configure("Treeview.Heading", font=("Sans", 10, "bold"), background="#123b65", foreground="#ffffff", bordercolor="#3976a9")
        style.map("Treeview", background=[("selected", "#087fbe")], foreground=[("selected", "white")])
        style.configure(
            "Compact.Treeview", rowheight=23, font=("DejaVu Sans Condensed", 9, "bold"),
            background="#f6f7fb", fieldbackground="#f6f7fb", foreground="#082b70",
            bordercolor="#53a8d2", relief="solid",
        )
        style.configure(
            "Compact.Treeview.Heading", font=("DejaVu Sans Condensed", 8, "bold"),
            background="#e8edf4", foreground="#30445c", bordercolor="#b8c8d8", padding=(1, 2),
        )
        style.map("Compact.Treeview", background=[("selected", "#ccecff")], foreground=[("selected", "#071a33")])
        style.configure(
            "CompactData.Treeview", rowheight=23, font=("DejaVu Sans", 7),
            background="#f6f7fb", fieldbackground="#f6f7fb", foreground="#20364f",
            bordercolor="#53a8d2", relief="solid",
        )
        style.configure(
            "CompactData.Treeview.Heading", font=("DejaVu Sans", 7, "bold"),
            background="#e8edf4", foreground="#30445c", bordercolor="#b8c8d8", padding=(1, 2),
        )
        style.map("CompactData.Treeview", background=[("selected", "#ccecff")], foreground=[("selected", "#071a33")])
        style.configure(
            "Pick.Treeview", rowheight=23, font=("DejaVu Sans", 11, "bold"),
            background="#fffafa", fieldbackground="#fffafa", foreground="#f07878",
            bordercolor="#ffaaaa", relief="solid",
        )
        style.configure(
            "Pick.Treeview.Heading", font=("DejaVu Sans", 9, "bold"),
            background="#fff0f0", foreground="#e06666", bordercolor="#ffaaaa", padding=(1, 1),
        )
        style.map("Pick.Treeview", background=[("selected", "#ffe0e0")], foreground=[("selected", "#d82828")])
        style.configure("Card.TLabelframe", background="#0c294b", bordercolor="#2a6698", relief="solid")
        style.configure("Card.TLabelframe.Label", background="#0c294b", foreground="#57d4ff", font=("Sans", 11, "bold"))
        style.configure("Card.TFrame", background="#0c294b")
        style.configure("Card.TLabel", background="#0c294b", foreground="#edf8ff")
        style.configure("Big.TLabel", background="#071a33", font=("Sans", 18, "bold"), foreground="#35c8ff")
        style.configure("TNotebook", background="#06162c", bordercolor="#2a6698", tabmargins=(2, 5, 2, 0))
        style.configure("TNotebook.Tab", background="#102f52", foreground="#c9e8ff", padding=(14, 8), font=("Sans", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#087fbe")], foreground=[("selected", "white")])
        style.configure("TEntry", fieldbackground="#eef7ff", foreground="#10243b")
        style.configure("TCombobox", fieldbackground="#eef7ff", foreground="#10243b", arrowcolor="#0b315c")
        style.configure("Workflow.TLabelframe", background="#081f3c", bordercolor="#1d5c8d", relief="solid")
        style.configure("Workflow.TLabelframe.Label", background="#081f3c", foreground="#35c8ff", font=("Sans", 13, "bold"))
        action_styles = {
            "Green.TButton": ("#18864b", "#35d27f", "#eafff3"),
            "Gold.TButton": ("#9a6a08", "#ffc83d", "#fff8d6"),
            "Orange.TButton": ("#a84c13", "#ff8a3d", "#fff1e7"),
            "Purple.TButton": ("#6543a5", "#a77cff", "#f3edff"),
            "Red.TButton": ("#9d2f3d", "#ff6678", "#fff0f2"),
        }
        for style_name, (background, border, foreground) in action_styles.items():
            style.configure(
                style_name, background=background, bordercolor=border, foreground=foreground,
                font=("DejaVu Sans", 10, "bold"), padding=(10, 7),
            )
            style.map(style_name, background=[("active", border)], foreground=[("active", "#071a33")])
        style.configure("Status.TLabel", background="#d89b12", foreground="#10213a", font=("DejaVu Sans", 9, "bold"), padding=(8, 5))
        style.configure("Section.TLabel", background="#071a33", foreground="#ffc83d", font=("DejaVu Sans Condensed", 14, "bold"))

        header = ttk.Frame(self, padding=(18, 14), style="Hero.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="⚽  QUINIELA", font=("DejaVu Sans Condensed", 23, "bold", "italic"), style="Hero.TLabel").pack(side="left")
        ttk.Label(header, text=" LOCAL", font=("DejaVu Sans Condensed", 23, "bold"), foreground="#49dbff", style="Hero.TLabel").pack(side="left")
        self.subtitle = ttk.Label(header, text="", font=("DejaVu Sans", 10, "bold"), foreground="#ffe066", style="Hero.TLabel")
        self.subtitle.pack(side="left", padx=18)
        self.update_data_button = ttk.Button(
            header, text="↻  Descargar datos", command=self.update_from_internet, style="Soft.TButton"
        )
        self.update_data_button.pack(side="right")
        ttk.Button(
            header, text="🌐 Subir TXT y jugar", command=self.open_quinielista, style="Gold.TButton"
        ).pack(side="right", padx=(10, 0))
        ttk.Button(header, text="✨ Crear desarrollo guiado", command=self.open_advanced, style="Accent.TButton").pack(side="right", padx=10)

        guide = ttk.Frame(self, padding=(18, 10))
        guide.pack(fill="x")
        ttk.Label(guide, text="① PARTIDOS", font=("DejaVu Sans", 10, "bold"), foreground="#49dbff").pack(side="left")
        ttk.Label(guide, text="→ ② SIGNOS", font=("DejaVu Sans", 10, "bold"), foreground="#75df91").pack(side="left", padx=16)
        ttk.Label(guide, text="→ ③ CONDICIONES", font=("DejaVu Sans", 10, "bold"), foreground="#ffe066").pack(side="left", padx=16)
        ttk.Label(guide, text="→ ④ REDUCCIÓN", font=("DejaVu Sans", 10, "bold"), foreground="#c69cff").pack(side="left", padx=16)
        ttk.Label(guide, text="→ ⑤ EXPORTAR", font=("DejaVu Sans", 10, "bold"), foreground="#ff8391").pack(side="left", padx=16)

        columns = ("n", "match")
        body = ttk.Frame(self, padding=(14, 4, 14, 4))
        body.pack(fill="both", expand=True)
        left_panel = ttk.Frame(body, width=465)
        left_panel.pack(side="left", fill="y")
        left_panel.pack_propagate(False)
        ttk.Label(left_panel, text="PARTIDOS DE LA JORNADA", style="Section.TLabel").pack(fill="x", pady=(0, 4))
        table_area = ttk.Frame(left_panel, height=346)
        table_area.pack(fill="x")
        table_area.pack_propagate(False)
        self.tree = ttk.Treeview(table_area, columns=columns, show="headings", selectmode="browse", style="Compact.Treeview")
        labels = ("", "Partido")
        widths = (24, 200)
        for column, label, width in zip(columns, labels, widths):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, minwidth=width, stretch=False, anchor="w" if column == "match" else "center")
        self.tree.pack(side="left", fill="both")
        data_columns = ("date", "prob")
        self.data_tree = ttk.Treeview(
            table_area, columns=data_columns, show="headings", selectmode="browse", style="CompactData.Treeview"
        )
        for column, label, width in zip(data_columns, ("Hora", "% 1 / X / 2"), (60, 78)):
            self.data_tree.heading(column, text=label)
            self.data_tree.column(column, width=width, minwidth=width, stretch=False, anchor="center")
        self.data_tree.pack(side="left", fill="both")
        picks = tk.Frame(table_area, background="#ffaaaa", width=96)
        picks.pack(side="left", fill="y", expand=True)
        picks.pack_propagate(False)
        pick_header = tk.Frame(picks, background="#fff0f0", height=22)
        pick_header.pack(fill="x")
        pick_header.pack_propagate(False)
        for column, sign in enumerate(("1", "X", "2")):
            tk.Label(
                pick_header, text=sign, width=3, background="#fff0f0", foreground="#e06666",
                font=("DejaVu Sans", 9, "bold"), relief="solid", bd=1,
            ).grid(row=0, column=column, sticky="nsew")
            pick_header.columnconfigure(column, weight=1)
        self.pick_buttons: dict[tuple[int, str], tk.Button] = {}
        for number in range(1, 15):
            row = tk.Frame(picks, background="#fffafa" if number % 2 else "#fff0f0", height=23)
            row.pack(fill="x")
            row.pack_propagate(False)
            for column, sign in enumerate(("1", "X", "2")):
                button = tk.Button(
                    row, text=sign, padx=0, pady=0, relief="solid", bd=1,
                    background="#fffafa" if number % 2 else "#fff0f0", foreground="#ef7777",
                    activebackground="#ffcaca", font=("DejaVu Sans", 9, "bold"),
                    command=lambda n=number, s=sign: self._toggle_pick_by_number(n, s),
                )
                button.grid(row=0, column=column, sticky="nsew")
                row.columnconfigure(column, weight=1)
                self.pick_buttons[(number, sign)] = button
        self.tree.bind("<<TreeviewSelect>>", self._show_detail)
        self.data_tree.bind("<<TreeviewSelect>>", self._sync_selection_from_data)
        self.tree.tag_configure("odd", background="#ffffff", foreground="#082b70")
        self.tree.tag_configure("even", background="#eef3f8", foreground="#082b70")
        self.data_tree.tag_configure("odd", background="#ffffff", foreground="#20364f")
        self.data_tree.tag_configure("even", background="#eef3f8", foreground="#20364f")

        self.pleno_home = tk.StringVar()
        self.pleno_away = tk.StringVar()
        pleno = tk.Frame(left_panel, background="#fffafa", highlightbackground="#ff9b9b", highlightthickness=1)
        pleno.pack(fill="x", pady=(3, 0))
        tk.Label(pleno, text="15", width=2, background="#fffafa", foreground="#e53945", font=("DejaVu Sans", 9)).grid(row=0, column=0, rowspan=2)
        self.pleno_home_name = tk.Label(pleno, text="Local", width=19, anchor="w", background="#fffafa", foreground="#082b70", font=("DejaVu Sans Condensed", 9, "bold"))
        self.pleno_home_name.grid(row=0, column=1, sticky="w")
        self.pleno_away_name = tk.Label(pleno, text="Visitante", width=19, anchor="w", background="#fffafa", foreground="#082b70", font=("DejaVu Sans Condensed", 9, "bold"))
        self.pleno_away_name.grid(row=1, column=1, sticky="w")
        tk.Label(pleno, text="P15", width=4, background="#df7b7b", foreground="white", font=("DejaVu Sans", 11, "bold")).grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(2, 3))
        self.pleno_buttons: dict[tuple[str, str], tk.Button] = {}
        for row, side in enumerate(("home", "away")):
            for offset, goals in enumerate(("0", "1", "2", "M")):
                button = tk.Button(
                    pleno, text=goals, width=2, padx=1, pady=0, relief="solid", bd=1,
                    background="#fffafa", foreground="#ef7777", activebackground="#ffcaca",
                    font=("DejaVu Sans", 9, "bold"),
                    command=lambda s=side, g=goals: self._set_pleno_goal(s, g),
                )
                button.grid(row=row, column=3 + offset, sticky="nsew")
                self.pleno_buttons[(side, goals)] = button

        self.main_price_label = ttk.Label(
            left_panel, text="", style="Card.TLabel", font=("DejaVu Sans", 10, "bold"),
            padding=(10, 9), anchor="center",
        )
        self.main_price_label.pack(fill="x", pady=(7, 0))

        workflow = ttk.LabelFrame(body, text="  PASOS DE TU QUINIELA  ", padding=14, style="Workflow.TLabelframe")
        workflow.pack(side="right", fill="both", expand=True, padx=(14, 0))
        ttk.Label(workflow, text="Sigue estos pasos en orden", font=("Sans", 11, "bold"), style="Card.TLabel").pack(anchor="w", pady=(0, 10))
        workflow_items = (
            ("↻", "Actualizar partidos", "Descarga jornada y porcentajes", self.update_from_internet, "Green.TButton", "#35d27f"),
            ("✓", "Marcar una quiniela", "Elige 1, X o 2 en la tabla", self.use_suggestions, "Gold.TButton", "#ffc83d"),
            ("⚙", "Crear desarrollo", "Dobles, triples y condiciones", self.open_advanced, "Orange.TButton", "#ff8a3d"),
            ("◆", "Optimizar presupuesto", "Busca la mejor cobertura", self.open_budget_optimizer, "Purple.TButton", "#a77cff"),
            ("★", "Comprobar premios", "Revisa aciertos del desarrollo o un TXT", self.open_prize_checker, "Green.TButton", "#75df91"),
            ("➜", "Exportar o copiar", "Guarda el resultado final", self.export, "Red.TButton", "#ff6678"),
        )
        for icon, title, description, command, button_style, color in workflow_items:
            card = ttk.Frame(workflow, padding=(8, 7), style="Card.TFrame")
            card.pack(fill="x", pady=4)
            ttk.Label(card, text=icon, font=("DejaVu Sans", 20, "bold"), foreground=color, style="Card.TLabel").pack(side="left", padx=(0, 8))
            text_frame = ttk.Frame(card, style="Card.TFrame")
            text_frame.pack(side="left", fill="x", expand=True)
            ttk.Button(text_frame, text=title, command=command, style=button_style).pack(fill="x")
            ttk.Label(text_frame, text=description, style="Card.TLabel", font=("DejaVu Sans", 8)).pack(anchor="w", pady=(2, 0))

        controls = ttk.Frame(self, padding=(16, 8))
        controls.pack(fill="x")
        ttk.Label(controls, text="Signo del partido seleccionado:").pack(side="left")
        for sign, sign_style in (("1", "Green.TButton"), ("X", "Gold.TButton"), ("2", "Red.TButton")):
            ttk.Button(controls, text=sign, width=5, style=sign_style, command=lambda s=sign: self.toggle_selected_pick(s)).pack(side="left", padx=3)
        ttk.Button(controls, text="Usar sugerencias", command=self.use_suggestions).pack(side="left", padx=(18, 3))
        ttk.Button(controls, text="Historial del partido", command=self.open_match_history, style="Gold.TButton").pack(side="left", padx=3)
        ttk.Button(controls, text="Optimizar presupuesto…", command=self.open_budget_optimizer).pack(side="left", padx=3)
        ttk.Button(controls, text="Columnas más probables…", command=self.open_system).pack(side="left", padx=3)
        ttk.Button(controls, text="Comprobar premios…", command=self.open_prize_checker, style="Green.TButton").pack(side="left", padx=3)
        ttk.Button(controls, text="Limpiar", command=self.clear_picks).pack(side="left", padx=3)
        ttk.Button(controls, text="Abrir TULOTERO", command=self.open_tulotero).pack(side="right", padx=(3, 0))
        ttk.Button(controls, text="Subir TXT y jugar", command=self.open_quinielista, style="Gold.TButton").pack(side="right", padx=3)
        ttk.Button(controls, text="Copiar apuesta", command=self.copy_bet).pack(side="right", padx=3)
        ttk.Button(controls, text="Exportar…", command=self.export).pack(side="right")

        self.detail = ttk.Label(self, text="", padding=(16, 4, 16, 14), foreground="#444")
        self.detail.pack(fill="x")
        self.status = ttk.Label(self, text="", style="Status.TLabel")
        self.status.pack(fill="x", side="bottom")

    def _key(self, match: Match) -> str:
        return f"{self.season}-{self.round_no}-{match.number}"

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                saved = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                if isinstance(saved, dict) and isinstance(saved.get("predictions"), dict):
                    self.predictions = saved["predictions"]
                    columns = saved.get("development_columns")
                    self.current_development_columns = columns if isinstance(columns, list) else None
                    self.current_development_source = str(saved.get("development_source", ""))
                else:
                    # Compatibilidad con el formato anterior, que era un diccionario plano.
                    self.predictions = saved if isinstance(saved, dict) else {}
            except (OSError, json.JSONDecodeError):
                self.predictions = {}

    def _save_state(self):
        payload = {
            "predictions": self.predictions,
            "development_columns": self.current_development_columns,
            "development_source": self.current_development_source,
        }
        STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def refresh(self):
        try:
            self.season, self.round_no, self.matches = load_matches()
        except Exception as exc:
            messagebox.showerror("No se pudieron leer los datos", str(exc))
            return
        self.subtitle.configure(text=f"Temporada {self.season} · Jornada {self.round_no}")
        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        for match in self.matches[:14]:
            p1, px, p2 = match.probabilities
            probability_text = f"{p1:.0f} / {px:.0f} / {p2:.0f}" if match.number <= 14 else "PLENO"
            saved_pick = self.predictions.get(self._key(match), "")
            tag = "even" if match.number % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=str(match.number), tags=(tag,), values=(
                match.number, f"{match.home}  –  {match.away}",
            ))
            self.data_tree.insert("", "end", iid=str(match.number), tags=(tag,), values=(
                compact_kickoff(match.kickoff), probability_text,
            ))
            self._render_match_pick(match.number, saved_pick)
        if len(self.matches) >= 15:
            pleno_match = self.matches[14]
            self.pleno_home_name.configure(text=pleno_match.home)
            self.pleno_away_name.configure(text=pleno_match.away)
            saved = self.predictions.get(self._key(pleno_match), "")
            parts = saved.split("-") if re.fullmatch(r"[012M]-[012M]", saved) else ("", "")
            self.pleno_home.set(parts[0])
            self.pleno_away.set(parts[1])
            self._render_pleno_buttons()
        self._update_main_price()
        updated = data_update_time(self.season).strftime("%d/%m/%Y %H:%M")
        regular_matches = self.matches[:14]
        internet = sum("Quinielista" in match.detail for match in regular_matches)
        neutral = sum("sin historial" in match.detail for match in regular_matches)
        if internet:
            source_note = f" · {internet}/14 porcentajes descargados de Quinielista"
        elif neutral:
            source_note = f" · AVISO: {neutral}/14 sin historial; estimación neutral"
        else:
            source_note = " · Modelo basado en historial local"
        self.status.configure(
            text=f"{len(self.matches)} partidos recargados desde {DATA} · Datos: {updated}{source_note}"
        )
        if self.matches:
            self._select_match("1")

    def update_from_internet(self):
        """Descarga datos y porcentajes sin ejecutar herramientas de WIN1X2."""
        self.update_data_button.configure(state="disabled", text="Descargando…")
        self.status.configure(text="Conectando con las fuentes de datos…")

        def worker():
            try:
                files = update_win1x2_files(DATA)
                dates_file, _schedule_file, season = season_files()
                round_no = current_round(parse_dates(dates_file))
                fetch_percentages(season, round_no, CACHE_DIR)
            except Exception as exc:
                self.after(0, lambda: finish_error(str(exc)))
            else:
                self.after(0, lambda: finish_ok(len(files), round_no))

        def finish_ok(file_count, round_no):
            self.update_data_button.configure(state="normal", text="↻  Descargar datos")
            self.refresh()
            self.status.configure(
                text=f"Actualización completada sin WebW1X2.exe · {file_count} archivos · porcentajes jornada {round_no}"
            )

        def finish_error(error):
            self.update_data_button.configure(state="normal", text="↻  Descargar datos")
            self.status.configure(text="No se pudo completar la actualización")
            messagebox.showerror("Error al descargar los datos", error, parent=self)

        threading.Thread(target=worker, daemon=True).start()

    def selected(self) -> Match | None:
        selection = self.tree.selection()
        return self.matches[int(selection[0]) - 1] if selection else None

    def open_match_history(self):
        match = self.selected()
        if not match:
            messagebox.showinfo("Selecciona un partido", "Selecciona primero un partido de la lista.", parent=self)
            return
        dialog = tk.Toplevel(self)
        dialog.title(f"Historial · {match.home} – {match.away}")
        self._fit_dialog(dialog, 820, 600, 680, 470)
        dialog.configure(background="#06162c")
        dialog.transient(self)

        hero = ttk.Frame(dialog, padding=(18, 14), style="Hero.TFrame")
        hero.pack(fill="x")
        ttk.Label(
            hero, text=f"{match.home}  —  {match.away}",
            font=("DejaVu Sans Condensed", 19, "bold"), foreground="#49dbff", style="Hero.TLabel",
        ).pack(anchor="w")
        ttk.Label(hero, text="Últimos resultados disponibles en el histórico local de WIN1X2", style="Hero.TLabel").pack(anchor="w")

        close_bar = ttk.Frame(dialog, padding=(12, 0, 12, 12))
        close_bar.pack(side="bottom", fill="x")
        ttk.Button(close_bar, text="Cerrar", command=dialog.destroy, style="Red.TButton").pack(side="right")

        tabs = ttk.Notebook(dialog)
        tabs.pack(fill="both", expand=True, padx=12, pady=12)
        names = load_team_names()
        current_history = build_form(self.season, self.round_no)
        regular_codes = {code for item in self.matches[:14] for code in (item.home_code, item.away_code)}
        domestic_coverage = sum(code in current_history for code in regular_codes)
        compatible_archive = domestic_coverage >= max(8, len(regular_codes) // 2)
        for team_code, team_name in ((match.home_code, match.home), (match.away_code, match.away)):
            page = ttk.Frame(tabs, padding=10)
            tabs.add(page, text=team_name)
            results = historical_results(team_code) if compatible_archive else []
            if not results:
                ttk.Label(
                    page,
                    text=(
                        "Esta jornada es internacional y el archivo local reutiliza códigos de clubes.\n"
                        "No se muestra ese histórico porque podría atribuir partidos al equipo equivocado."
                        if not compatible_archive else
                        f"No hay partidos históricos para {team_name} ({team_code}) en esta instalación."
                    ),
                    foreground="#ffe066", font=("DejaVu Sans", 11, "bold"),
                ).pack(anchor="w", pady=20)
                continue
            table = ttk.Treeview(page, columns=("season", "venue", "opponent", "score", "result"), show="headings")
            for column, title, width in (
                ("season", "Temp.", 70), ("venue", "Campo", 90), ("opponent", "Rival", 260),
                ("score", "Marcador", 90), ("result", "Resultado", 90),
            ):
                table.heading(column, text=title)
                table.column(column, width=width, anchor="w" if column == "opponent" else "center")
            table.pack(fill="both", expand=True)
            for index, (season, opponent, venue, goals_for, goals_against) in enumerate(results):
                outcome = "Victoria" if goals_for > goals_against else "Empate" if goals_for == goals_against else "Derrota"
                tag = "win" if outcome == "Victoria" else "draw" if outcome == "Empate" else "loss"
                table.insert("", "end", values=(season, venue, names.get(opponent, opponent), f"{goals_for}-{goals_against}", outcome), tags=(tag,))
            table.tag_configure("win", foreground="#75df91")
            table.tag_configure("draw", foreground="#ffe066")
            table.tag_configure("loss", foreground="#ff8391")

    def open_prize_checker(self):
        dialog = tk.Toplevel(self)
        dialog.title("Comprobar aciertos y premios")
        dialog.configure(background="#06162c")
        self._fit_dialog(dialog, 980, 700, 760, 540)
        dialog.transient(self)

        hero = ttk.Frame(dialog, padding=(18, 12), style="Hero.TFrame")
        hero.pack(fill="x")
        ttk.Label(hero, text="COMPRUEBA TUS APUESTAS", font=("DejaVu Sans Condensed", 20, "bold"), foreground="#75df91", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(hero, text="Usa el escrutinio descargado de WIN1X2; los importes aparecen cuando están disponibles.", style="Hero.TLabel").pack(anchor="w")

        bottom = ttk.Frame(dialog, padding=(12, 6, 12, 12))
        bottom.pack(side="bottom", fill="x")
        content = ttk.Frame(dialog, padding=12)
        content.pack(fill="both", expand=True)

        source = tk.StringVar(value="current")
        file_path = tk.StringVar()
        loaded_bets: list[str] = []
        controls = ttk.LabelFrame(content, text="  APUESTAS Y JORNADA  ", padding=10, style="Workflow.TLabelframe")
        controls.pack(fill="x")
        ttk.Radiobutton(controls, text="Desarrollo generado actualmente", variable=source, value="current").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(controls, text="Cargar fichero TXT exportado", variable=source, value="file").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(controls, textvariable=file_path, state="readonly", width=48).grid(row=1, column=1, sticky="ew", padx=8, pady=(6, 0))
        controls.columnconfigure(1, weight=1)

        def choose_file():
            target = filedialog.askopenfilename(parent=dialog, title="Seleccionar apuestas", filetypes=(("Apuestas TXT", "*.txt"), ("Todos", "*.*")))
            if not target:
                return
            try:
                bets = read_bet_file(Path(target))
            except (OSError, ValueError) as exc:
                messagebox.showerror("Archivo no válido", str(exc), parent=dialog)
                return
            loaded_bets[:] = bets
            file_path.set(target)
            source.set("file")
            source_label.configure(text=f"Archivo cargado: {len(bets):,} apuestas")

        ttk.Button(controls, text="Elegir TXT…", command=choose_file, style="Purple.TButton").grid(row=1, column=2, pady=(6, 0))
        ttk.Label(controls, text="Jornada:").grid(row=0, column=1, sticky="e", padx=(8, 2))
        round_var = tk.IntVar(value=self.round_no)
        ttk.Spinbox(controls, from_=1, to=99, textvariable=round_var, width=5).grid(row=0, column=2, sticky="w")

        source_label = ttk.Label(content, text="", style="Big.TLabel", padding=(0, 10))
        source_label.pack(fill="x")
        result_label = ttk.Label(content, text="Selecciona la fuente y pulsa Comprobar.", style="Card.TLabel", padding=10)
        result_label.pack(fill="x", pady=(0, 8))

        panes = ttk.Frame(content)
        panes.pack(fill="both", expand=True)
        distribution = ttk.Treeview(panes, columns=("category", "mine", "official", "prize", "total"), show="headings", height=7)
        for key, title, width in (
            ("category", "Categoría", 105), ("mine", "Tus apuestas", 100), ("official", "Acertantes oficiales", 135),
            ("prize", "Premio/apuesta", 120), ("total", "Premio calculado", 130),
        ):
            distribution.heading(key, text=title)
            distribution.column(key, width=width, anchor="center")
        distribution.pack(side="left", fill="both", expand=True)
        best = ttk.Treeview(panes, columns=("bet", "hits", "pleno"), show="headings", height=7)
        for key, title, width in (("bet", "Mejores columnas", 205), ("hits", "Aciertos", 70), ("pleno", "P15", 55)):
            best.heading(key, text=title)
            best.column(key, width=width, anchor="center")
        best.pack(side="left", fill="both", expand=True, padx=(8, 0))

        def current_bets():
            if not self.current_development_columns:
                raise ValueError("No hay un desarrollo generado. Usa «Crear desarrollo» o carga un TXT.")
            pleno = self.predictions.get(self._key(self.matches[14]), "")
            suffix = pleno.replace("-", "") if re.fullmatch(r"[012M]-[012M]", pleno) else ""
            return ["".join(column) + suffix for column in self.current_development_columns]

        def check_bets():
            try:
                selected_round = int(round_var.get())
                bets = current_bets() if source.get() == "current" else list(loaded_bets)
                if not bets:
                    raise ValueError("Selecciona primero un fichero TXT.")
            except (ValueError, tk.TclError) as exc:
                messagebox.showwarning("Faltan datos", str(exc), parent=dialog)
                return
            pre_path = next(iter(DATA.glob(f"PRE{self.season}.txt")), None) or next(iter(DATA.glob(f"Pre{self.season}.txt")), None)
            scrutiny = parse_scrutiny(pre_path, selected_round) if pre_path else None
            if not scrutiny:
                result_label.configure(text=f"Jornada {selected_round}: todavía no hay resultados completos en los datos descargados.", foreground="#ffe066")
                source_label.configure(text=f"{len(bets):,} apuestas listas para comprobar cuando termine la jornada")
                for tree in (distribution, best):
                    tree.delete(*tree.get_children())
                return
            evaluations = evaluate_bets(bets, scrutiny["result"], scrutiny["pleno"])
            counts = defaultdict(int)
            for item in evaluations:
                counts[item["category"]] += 1
            estimated_total = 0.0
            distribution.delete(*distribution.get_children())
            for category in (15, 14, 13, 12, 11, 10):
                official_winners, prize = scrutiny["prizes"].get(category, (0, 0.0))
                mine = counts[category]
                subtotal = mine * prize
                estimated_total += subtotal
                label = "14 + Pleno" if category == 15 else str(category)
                distribution.insert("", "end", values=(label, mine, official_winners, f"{prize:,.2f} €", f"{subtotal:,.2f} €"))
            best.delete(*best.get_children())
            ordered = sorted(evaluations, key=lambda item: (item["category"], item["hits"], item["pleno_hit"]), reverse=True)
            for item in ordered[:100]:
                best.insert("", "end", values=(item["bet"], item["hits"], "Sí" if item["pleno_hit"] else "No"))
            source_label.configure(text=f"{len(bets):,} apuestas · mejor resultado: {ordered[0]['category']} · premio calculado: {estimated_total:,.2f} €")
            result_label.configure(
                text=f"Jornada {selected_round} · Resultado: {scrutiny['result']} · Pleno: {scrutiny['pleno'][0]}-{scrutiny['pleno'][1]} · Datos locales descargados",
                foreground="#75df91",
            )

        ttk.Button(bottom, text="★ Comprobar", command=check_bets, style="Green.TButton").pack(side="left")
        ttk.Button(bottom, text="↻ Descargar datos", command=self.update_from_internet, style="Soft.TButton").pack(side="left", padx=6)
        ttk.Button(bottom, text="Cerrar", command=dialog.destroy, style="Red.TButton").pack(side="right")
        if self.current_development_columns:
            source_label.configure(text=f"Desarrollo actual: {len(self.current_development_columns):,} apuestas")
        else:
            source_label.configure(text="No hay desarrollo actual; puedes cargar un TXT exportado")


    def _selected_suggestion(self) -> str:
        match = self.selected()
        return match.suggestion if match else "1"

    def toggle_selected_pick(self, sign: str):
        match = self.selected()
        if match:
            self._toggle_pick_by_number(match.number, sign)

    def _toggle_pick_by_number(self, number: int, sign: str):
        self._select_match(str(number))
        match = self.matches[number - 1]
        key = self._key(match)
        selected = set(self.predictions.get(key, "")) & {"1", "X", "2"}
        if sign in selected:
            selected.remove(sign)
        else:
            selected.add(sign)
        value = "".join(item for item in ("1", "X", "2") if item in selected)
        if value:
            self.predictions[key] = value
        else:
            self.predictions.pop(key, None)
        self._render_match_pick(number, value)
        self.current_development_columns = None
        self.current_development_source = "edición manual"
        self._save_state()
        self._update_main_price()

    def _render_match_pick(self, number: int, selected: str):
        for sign in ("1", "X", "2"):
            button = self.pick_buttons[(number, sign)]
            active = sign in selected
            button.configure(
                text=sign,
                background="#e94d5c" if active else ("#fffafa" if number % 2 else "#fff0f0"),
                foreground="white" if active else "#ef7777",
                relief="sunken" if active else "solid",
            )

    def _select_match(self, item: str):
        self.tree.selection_set(item)
        self.data_tree.selection_set(item)
        self.tree.see(item)
        self.data_tree.see(item)

    def _sync_selection_from_data(self, _event=None):
        selection = self.data_tree.selection()
        if selection and self.tree.selection() != selection:
            self.tree.selection_set(selection[0])

    def _update_pick_cells(self, match: Match, value: str):
        if match.number == 15:
            parts = value.split("-") if re.fullmatch(r"[012M]-[012M]", value) else ("", "")
            self.pleno_home.set(parts[0])
            self.pleno_away.set(parts[1])
            self._render_pleno_buttons()
            return
        self._render_match_pick(match.number, value)

    def _render_pleno_buttons(self):
        selected = {"home": self.pleno_home.get(), "away": self.pleno_away.get()}
        for (side, goals), button in self.pleno_buttons.items():
            active = selected[side] == goals
            button.configure(
                text=goals,
                background="#e94d5c" if active else "#fffafa",
                foreground="white" if active else "#ef7777",
                relief="sunken" if active else "solid",
            )

    def _set_pleno_goal(self, side: str, goals: str):
        if not self.matches:
            return
        variable = self.pleno_home if side == "home" else self.pleno_away
        variable.set(goals)
        self._render_pleno_buttons()
        if self.pleno_home.get() and self.pleno_away.get():
            match = self.matches[14]
            self.predictions[self._key(match)] = f"{self.pleno_home.get()}-{self.pleno_away.get()}"
            self._save_state()

    def _update_main_price(self):
        if len(self.matches) < 14:
            return
        values = [self.predictions.get(self._key(match), "") for match in self.matches[:14]]
        missing = sum(not value for value in values)
        if missing:
            self.main_price_label.configure(
                text=f"Completa {missing} partido{'s' if missing != 1 else ''} para calcular el precio",
                foreground="#ffe066",
            )
            return
        complete_columns = math.prod(len(set(value) & {"1", "X", "2"}) for value in values)
        columns = len(self.current_development_columns) if self.current_development_columns is not None else complete_columns
        charged_columns = max(2, columns)
        minimum_note = " · mínimo oficial: 2" if columns == 1 else ""
        source_note = f" · {self.current_development_source}" if self.current_development_source else ""
        base_note = f" · base completa {complete_columns:,}" if columns != complete_columns else ""
        self.main_price_label.configure(
            text=(f"{columns:,} columna{'s' if columns != 1 else ''}{minimum_note}  ·  "
                  f"PRECIO: {charged_columns * BET_PRICE:,.2f} €{base_note}{source_note}"),
            foreground="#75df91" if columns <= 100 else "#ffe066",
        )

    def apply_development_to_main(
        self, *, columns: list[str] | list[tuple[str, ...]] | None = None,
        selections: list[str] | None = None, source: str = "desarrollo",
    ):
        """Convierte cualquier resultado generado en la base visible principal."""
        if columns:
            normalized = [tuple(column) for column in columns]
            selections = [
                "".join(sign for sign in ("1", "X", "2") if any(column[index] == sign for column in normalized))
                for index in range(14)
            ]
        if not selections or len(selections) < 14:
            return
        self.current_development_columns = ["".join(column) for column in normalized] if columns else None
        self.current_development_source = source
        for match, value in zip(self.matches[:14], selections[:14]):
            normalized_value = "".join(sign for sign in ("1", "X", "2") if sign in value)
            if not normalized_value:
                continue
            self.predictions[self._key(match)] = normalized_value
            self._update_pick_cells(match, normalized_value)
        self._save_state()
        self._update_main_price()
        self.status.configure(text=f"Quiniela general actualizada desde {source}.")

    def set_pick(self, sign: str):
        match = self.selected()
        if not match:
            return
        if match.number == 15:
            self.set_pleno(match)
            return
        self.predictions[self._key(match)] = sign
        self._update_pick_cells(match, sign)
        self._save_state()
        next_number = match.number + 1
        if next_number <= min(14, len(self.matches)):
            self._select_match(str(next_number))

    def use_suggestions(self):
        self.current_development_columns = None
        self.current_development_source = "sugerencias"
        for match in self.matches:
            value = "1-1" if match.number == 15 else match.suggestion
            self.predictions[self._key(match)] = value
            self._update_pick_cells(match, value)
        self._save_state()
        self._update_main_price()

    def set_pleno(self, match: Match):
        dialog = tk.Toplevel(self)
        dialog.title("Pleno al 15")
        dialog.configure(background="#071a33")
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
            self._update_pick_cells(match, value)
            self._save_state()
            dialog.destroy()

        ttk.Button(frame, text="Guardar marcador", command=save).grid(row=3, column=0, columnspan=2, pady=(10, 0))
        dialog.wait_window()

    def clear_picks(self):
        self.current_development_columns = None
        self.current_development_source = ""
        for match in self.matches:
            self.predictions.pop(self._key(match), None)
            self._update_pick_cells(match, "")
        self._save_state()
        self._update_main_price()

    def _show_detail(self, _event=None):
        match = self.selected()
        if match:
            item = str(match.number)
            if self.data_tree.selection() != (item,):
                self.data_tree.selection_set(item)
                self.data_tree.see(item)
            self.detail.configure(text=f"{match.home_code}–{match.away_code}: {match.detail}")

    def export(self):
        if self.current_development_columns is not None:
            columns = self.current_development_columns
        else:
            base = [self.predictions.get(self._key(match), "") for match in self.matches[:14]]
            if any(not signs or not set(signs) <= {"1", "X", "2"} for signs in base):
                messagebox.showwarning(
                    "Pronóstico incompleto",
                    "Selecciona al menos un signo en cada partido antes de exportar.",
                    parent=self,
                )
                return
            total = math.prod(len(set(signs)) for signs in base)
            if total > 100_000:
                messagebox.showwarning(
                    "Demasiadas columnas",
                    f"La selección contiene {total:,} columnas. Crea o reduce el desarrollo antes de exportarlo.",
                    parent=self,
                )
                return
            columns = ["".join(column) for column in generate_columns([tuple(dict.fromkeys(signs)) for signs in base])]
        target = filedialog.asksaveasfilename(
            title="Exportar apuestas en TXT", defaultextension=".txt",
            initialfile=f"quiniela_{self.season}_J{self.round_no:02d}.txt",
            filetypes=(("TXT para Quinielista", "*.txt"), ("Todos", "*.*")),
        )
        if not target:
            return
        pleno = self.predictions.get(self._key(self.matches[14]), "")
        if not re.fullmatch(r"[012M]-[012M]", pleno):
            messagebox.showwarning("Falta el Pleno al 15", "Define el resultado del Pleno al 15 antes de exportar.", parent=self)
            return
        Path(target).write_text(quinielista_text(columns, pleno), encoding="utf-8")
        self.status.configure(text=f"TXT compatible exportado: {len(columns)} apuestas en {target}")

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

    def open_quinielista(self):
        """Abre la carga de archivos para validar y pagar las apuestas."""
        if messagebox.askokcancel(
            "Subir TXT y jugar",
            "Se abrirá la página de archivos de EduardoLosilla/Quinielista.\n\n"
            "1. Exporta primero el desarrollo como TXT.\n"
            "2. Inicia sesión y carga el archivo en la web.\n"
            "3. Indica el número de apuestas y pulsa «Enviar para jugar».\n"
            "4. Revisa jornada, columnas, Pleno e importe antes de pagar.\n\n"
            "La web es externa: esta aplicación no envía datos ni confirma pagos.",
            parent=self,
        ):
            webbrowser.open(QUINIELISTA_UPLOAD_URL)

    def probable_columns(self, count: int, base: list[str] | None = None) -> list[tuple[str, float]]:
        """Devuelve las N combinaciones 1X2 más probables sin enumerar 3^14."""
        ranked = []
        for index, match in enumerate(self.matches[:14]):
            admitted = set(base[index]) if base else {"1", "X", "2"}
            options = sorted(
                ((sign, probability) for sign, probability in zip(("1", "X", "2"), match.probabilities) if sign in admitted),
                key=lambda item: item[1], reverse=True,
            )
            if not options:
                return []
            ranked.append(options)

        start = tuple(0 for _ in ranked)

        def score(indices):
            # Logaritmos evitan pérdida de precisión al multiplicar 14 valores.
            return sum(math.log(max(ranked[i][index][1] / 100, 1e-12)) for i, index in enumerate(indices))

        heap = [(-score(start), start)]
        visited = {start}
        result = []
        while heap and len(result) < count:
            negative_score, indices = heapq.heappop(heap)
            signs = "".join(ranked[i][index][0] for i, index in enumerate(indices))
            result.append((signs, math.exp(-negative_score) * 100))
            for position in range(len(indices)):
                if indices[position] >= len(ranked[position]) - 1:
                    continue
                candidate = list(indices)
                candidate[position] += 1
                candidate_tuple = tuple(candidate)
                if candidate_tuple not in visited:
                    visited.add(candidate_tuple)
                    heapq.heappush(heap, (-score(candidate_tuple), candidate_tuple))
        return result

    def budget_plans(self, budget: float, source_columns: list[str] | None = None) -> list[Plan]:
        max_bets = max(0, int((budget + 1e-9) // BET_PRICE))
        if max_bets < 2:
            return []
        base = [self.predictions.get(self._key(match), "") for match in self.matches[:14]]
        if any(not value or not set(value) <= {"1", "X", "2"} for value in base):
            return []
        probabilities = tuple(tuple(value / 100 for value in match.probabilities) for match in self.matches[:14])

        if source_columns is not None:
            available = list(dict.fromkeys(source_columns))
            ranked = rank_columns([tuple(column) for column in available], probabilities)
            available_with_probability = [("".join(column), math.exp(score) * 100) for column, score in ranked]
            origin = f"el desarrollo calculado ({len(available):,} columnas)"
        else:
            total = math.prod(len(set(value)) for value in base)
            available_with_probability = self.probable_columns(min(total, max_bets, 1000), base)
            origin = f"la base actual ({total:,} combinaciones)"

        selected = available_with_probability[:min(max_bets, len(available_with_probability))]
        if not selected:
            return []
        plans = [Plan(
            "Optimización del desarrollo actual", len(selected), len(selected) * BET_PRICE,
            sum(probability for _signs, probability in selected), [],
            f"Solo utiliza columnas procedentes de {origin}, ordenadas por probabilidad.",
            [signs for signs, _probability in selected],
        )]

        if source_columns is not None and len(source_columns) <= max_bets:
            all_columns = list(dict.fromkeys(source_columns))
            plans.append(Plan(
                "Desarrollo calculado completo", len(all_columns), len(all_columns) * BET_PRICE,
                sum(probability for _signs, probability in available_with_probability), [],
                "Conserva exactamente todas las columnas generadas anteriormente.", all_columns,
            ))
        elif source_columns is None:
            total = math.prod(len(set(value)) for value in base)
            if total <= max_bets:
                mass = math.prod(
                    sum(match.probabilities[("1", "X", "2").index(sign)] / 100 for sign in allowed)
                    for match, allowed in zip(self.matches[:14], base)
                ) * 100
                plans.append(Plan(
                    "Base completa actual", total, total * BET_PRICE, mass, base,
                    "Desarrollo completo de los signos seleccionados en la quiniela principal.",
                ))
        return plans

    def plan_text(self, plan: Plan) -> str:
        pleno = self.predictions.get(self._key(self.matches[14]), "sin definir")
        lines = [
            f"QUINIELA {self.season} · JORNADA {self.round_no}",
            f"PLAN: {plan.name}",
            f"APUESTAS: {plan.bets} · COSTE: {plan.cost:.2f} € · COBERTURA ESTIMADA: {plan.coverage:.6f} %",
            f"PLENO AL 15: {pleno}",
            plan.note,
            "",
        ]
        if plan.columns:
            lines.extend(f"{index:>3}. {column}" for index, column in enumerate(plan.columns, 1))
        else:
            for match, signs in zip(self.matches[:14], plan.selections):
                kind = {1: "Fijo", 2: "Doble", 3: "Triple"}[len(signs)]
                lines.append(f"{match.number:>2}. {match.home} - {match.away}: {signs} ({kind})")
        return "\n".join(lines) + "\n"

    def open_budget_optimizer(self):
        if self.current_development_columns is None:
            messagebox.showwarning(
                "Primero crea el desarrollo",
                "El optimizador trabaja únicamente con las columnas obtenidas en «Crear desarrollo».\n\n"
                "Crea el desarrollo y vuelve a pulsar «Optimizar presupuesto».",
                parent=self,
            )
            return
        if not self.current_development_columns:
            messagebox.showwarning(
                "Desarrollo vacío",
                "Las condiciones eliminaron todas las columnas. Cambia los límites y vuelve a crear el desarrollo.",
                parent=self,
            )
            return
        base = [self.predictions.get(self._key(match), "") for match in self.matches[:14]]
        optimizer_source_columns = list(self.current_development_columns) if self.current_development_columns is not None else None
        dialog = tk.Toplevel(self)
        dialog.title("Optimizar por presupuesto")
        dialog.configure(background="#071a33")
        self._fit_dialog(dialog, 880, 650, 720, 520)
        dialog.transient(self)

        top = ttk.Frame(dialog, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="Presupuesto máximo (€):", font=("Sans", 11, "bold")).pack(side="left")
        budget_var = tk.StringVar(value="15,00")
        ttk.Entry(top, textvariable=budget_var, width=10).pack(side="left", padx=7)
        ttk.Label(top, text="Precio oficial usado: 0,75 € por apuesta", foreground="#444").pack(side="left", padx=8)
        origin_text = f"Desarrollo creado: {len(self.current_development_columns):,} columnas"
        ttk.Label(top, text=origin_text, foreground="#75df91", font=("DejaVu Sans", 9, "bold")).pack(side="right")

        buttons = ttk.Frame(dialog, padding=(12, 0, 12, 12))
        buttons.pack(side="bottom", fill="x")

        columns = ("recommended", "plan", "bets", "cost", "coverage")
        tree = ttk.Treeview(dialog, columns=columns, show="headings", height=8, selectmode="browse")
        for key, title, width in (
            ("recommended", "", 45), ("plan", "Estrategia", 220), ("bets", "Apuestas", 90),
            ("cost", "Coste", 100), ("coverage", "Cobertura estimada de 14", 190),
        ):
            tree.heading(key, text=title)
            tree.column(key, width=width, anchor="center" if key != "plan" else "w")
        tree.pack(fill="x", padx=12)

        detail = tk.Text(
            dialog, wrap="word", height=18, font=("Monospace", 9), padx=8, pady=8,
            background="#081f3c", foreground="#eaf6ff", insertbackground="white",
            selectbackground="#087fbe", relief="flat",
        )
        detail.pack(fill="both", expand=True, padx=12, pady=8)
        plans: list[Plan] = []

        def selected_plan():
            selection = tree.selection()
            return plans[int(selection[0])] if selection else None

        def show_detail(_event=None):
            plan = selected_plan()
            if not plan:
                return
            detail.configure(state="normal")
            detail.delete("1.0", "end")
            detail.insert("1.0", self.plan_text(plan))
            detail.configure(state="disabled")
            if plan.columns:
                self.apply_development_to_main(columns=plan.columns, source=f"«{plan.name}»")
            elif plan.selections:
                self.apply_development_to_main(selections=plan.selections, source=f"«{plan.name}»")

        def calculate():
            nonlocal plans
            try:
                budget = float(budget_var.get().replace(",", "."))
            except ValueError:
                messagebox.showwarning("Importe no válido", "Introduce un importe como 15,00.", parent=dialog)
                return
            plans = self.budget_plans(budget, optimizer_source_columns)
            for item in tree.get_children():
                tree.delete(item)
            detail.configure(state="normal")
            detail.delete("1.0", "end")
            detail.configure(state="disabled")
            if not plans:
                messagebox.showwarning("Presupuesto insuficiente", "El mínimo son 2 apuestas: 1,50 €.", parent=dialog)
                return
            for index, plan in enumerate(plans):
                tree.insert("", "end", iid=str(index), values=(
                    "★" if index == 0 else "", plan.name, plan.bets,
                    f"{plan.cost:.2f} €", f"{plan.coverage:.6f} %",
                ))
            tree.selection_set("0")
            show_detail()

        def copy_plan():
            plan = selected_plan()
            if plan:
                self.clipboard_clear()
                self.clipboard_append(self.plan_text(plan))
                self.update()
                self.status.configure(text=f"Plan «{plan.name}» copiado; revisa la apuesta antes de comprar.")

        def export_plan():
            plan = selected_plan()
            if not plan:
                return
            target = filedialog.asksaveasfilename(
                parent=dialog, title="Exportar plan", defaultextension=".txt",
                initialfile=f"plan_{self.season}_J{self.round_no:02d}_{plan.bets}apuestas.txt",
                filetypes=(("TXT para Quinielista", "*.txt"), ("Todos", "*.*")),
            )
            if target:
                columns = plan.columns or ["".join(column) for column in generate_columns([tuple(signs) for signs in plan.selections])]
                pleno = self.predictions.get(self._key(self.matches[14]), "")
                if not re.fullmatch(r"[012M]-[012M]", pleno):
                    messagebox.showwarning("Falta el Pleno al 15", "Define el Pleno al 15 antes de exportar.", parent=dialog)
                    return
                Path(target).write_text(quinielista_text(columns, pleno), encoding="utf-8")
                self.status.configure(text=f"Plan exportado como TXT compatible: {len(columns)} apuestas.")

        tree.bind("<<TreeviewSelect>>", show_detail)
        ttk.Button(buttons, text="Calcular", command=calculate).pack(side="left")
        ttk.Button(buttons, text="Copiar plan", command=copy_plan).pack(side="left", padx=5)
        ttk.Button(buttons, text="Exportar…", command=export_plan).pack(side="left")
        ttk.Button(buttons, text="🌐 Subir TXT y jugar", command=self.open_quinielista, style="Gold.TButton").pack(side="left", padx=5)
        ttk.Button(buttons, text="Cerrar", command=dialog.destroy).pack(side="right")
        ttk.Label(
            buttons,
            text="★ = mayor cobertura estimada según el modelo; no garantiza premio.",
            foreground="#8a4b00",
        ).pack(side="right", padx=16)
        calculate()

    def open_system(self):
        dialog = tk.Toplevel(self)
        dialog.title("Columnas más probables")
        dialog.configure(background="#071a33")
        self._fit_dialog(dialog, 670, 570, 560, 430)
        dialog.transient(self)

        top = ttk.Frame(dialog, padding=12)
        top.pack(fill="x")
        buttons = ttk.Frame(dialog, padding=(12, 0, 12, 12))
        buttons.pack(side="bottom", fill="x")
        ttk.Label(top, text="Número de columnas:").pack(side="left")
        amount = tk.IntVar(value=10)
        spin = ttk.Spinbox(top, from_=2, to=100, textvariable=amount, width=6)
        spin.pack(side="left", padx=6)
        ttk.Label(
            top,
            text="Ordenadas por probabilidad conjunta; cada fila es una apuesta de 14 signos.",
            foreground="#444",
        ).pack(side="left", padx=8)

        tree = ttk.Treeview(dialog, columns=("rank", "column", "prob"), show="headings")
        tree.heading("rank", text="#")
        tree.heading("column", text="Signos 1–14")
        tree.heading("prob", text="Probabilidad estimada")
        tree.column("rank", width=55, anchor="center")
        tree.column("column", width=260, anchor="center")
        tree.column("prob", width=160, anchor="e")
        tree.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        generated: list[tuple[str, float]] = []

        def generate():
            nonlocal generated
            try:
                requested = max(2, min(100, int(amount.get())))
            except (ValueError, tk.TclError):
                requested = 10
                amount.set(requested)
            generated = self.probable_columns(requested)
            for item in tree.get_children():
                tree.delete(item)
            for rank, (signs, probability) in enumerate(generated, 1):
                spaced = " ".join(signs)
                tree.insert("", "end", values=(rank, spaced, f"{probability:.6f} %"))
            self.apply_development_to_main(
                columns=[signs for signs, _probability in generated],
                source=f"{len(generated)} columnas más probables",
            )

        def system_text():
            pleno = self.predictions.get(self._key(self.matches[14]), "")
            return quinielista_text(
                [signs for signs, _probability in generated],
                pleno,
            )

        def copy_system():
            if not generated:
                generate()
            pleno = self.predictions.get(self._key(self.matches[14]), "")
            if not re.fullmatch(r"[012M]-[012M]", pleno):
                messagebox.showwarning("Falta el Pleno al 15", "Define el Pleno al 15 antes de copiar las apuestas.", parent=dialog)
                return
            self.clipboard_clear()
            self.clipboard_append(system_text())
            self.update()
            self.status.configure(text=f"Sistema de {len(generated)} columnas copiado al portapapeles.")

        def export_system():
            if not generated:
                generate()
            pleno = self.predictions.get(self._key(self.matches[14]), "")
            if not re.fullmatch(r"[012M]-[012M]", pleno):
                messagebox.showwarning("Falta el Pleno al 15", "Define el Pleno al 15 antes de exportar.", parent=dialog)
                return
            target = filedialog.asksaveasfilename(
                parent=dialog, title="Exportar sistema", defaultextension=".txt",
                initialfile=f"sistema_{self.season}_J{self.round_no:02d}_{len(generated)}columnas.txt",
                filetypes=(("TXT para Quinielista", "*.txt"), ("Todos", "*.*")),
            )
            if target:
                Path(target).write_text(system_text(), encoding="utf-8")
                self.status.configure(text=f"Sistema exportado en {target}")

        ttk.Button(buttons, text="Generar", command=generate).pack(side="left")
        ttk.Button(buttons, text="Copiar", command=copy_system).pack(side="left", padx=5)
        ttk.Button(buttons, text="Exportar…", command=export_system).pack(side="left")
        ttk.Button(buttons, text="🌐 Subir TXT y jugar", command=self.open_quinielista, style="Gold.TButton").pack(side="left", padx=5)
        ttk.Button(buttons, text="Cerrar", command=dialog.destroy).pack(side="right")
        generate()

    def open_advanced(self):
        """Editor de base, condiciones, reducción, análisis y exportación."""
        dialog = tk.Toplevel(self)
        dialog.title("Asistente para crear un desarrollo")
        self._fit_dialog(dialog, 1120, 800, 820, 600)
        dialog.configure(background="#06162c")
        dialog.transient(self)

        hero = ttk.Frame(dialog, padding=(20, 14), style="Hero.TFrame")
        hero.pack(fill="x")
        ttk.Label(hero, text="CREA TU JUGADA", font=("DejaVu Sans Condensed", 21, "bold", "italic"), foreground="#49dbff", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(
            hero, text="No necesitas conocer el sistema: elige una base, aplica límites sencillos y revisa el resultado.",
            style="Hero.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        # Se empaqueta antes que el contenido expansible para que nunca quede fuera de pantalla.
        buttons = ttk.Frame(dialog, padding=(10, 4, 10, 10))
        buttons.pack(side="bottom", fill="x")

        notebook = ttk.Notebook(dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        base_tab = ttk.Frame(notebook, padding=12)
        conditions_tab = ttk.Frame(notebook, padding=12)
        result_tab = ttk.Frame(notebook, padding=12)
        base_tab.columnconfigure(0, weight=1)
        result_tab.columnconfigure(0, weight=1)
        result_tab.rowconfigure(0, weight=1)
        notebook.add(base_tab, text="① Elige signos")
        notebook.add(conditions_tab, text="② Pon límites")
        notebook.add(result_tab, text="③ Revisa y exporta")

        ttk.Label(base_tab, text="¿QUÉ RESULTADOS QUIERES CUBRIR?", style="Section.TLabel").grid(
            row=0, column=0, columnspan=6, sticky="w", pady=(0, 10)
        )
        ttk.Label(
            base_tab,
            text="1, X o 2 es un resultado fijo · 1X, 12 o X2 cubren dos resultados · 1X2 los cubre todos.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, columnspan=6, sticky="w", pady=(0, 12))
        base_vars: list[tk.StringVar] = []
        base_buttons: dict[tuple[int, str], tk.Button] = {}
        for index, match in enumerate(self.matches[:14]):
            frame = ttk.Frame(base_tab)
            frame.grid(row=index + 2, column=0, columnspan=2, sticky="ew", padx=(8, 300), pady=2)
            frame.columnconfigure(0, weight=1)
            ttk.Label(frame, text=f"{index + 1:>2}. {match.home} – {match.away}").grid(row=0, column=0, sticky="w")
            saved_base = self.predictions.get(self._key(match), "")
            initial_base = saved_base if saved_base and set(saved_base) <= {"1", "X", "2"} else match.suggestion
            variable = tk.StringVar(value=initial_base)
            base_vars.append(variable)
            selector = tk.Frame(frame, background="#ffaaaa")
            selector.grid(row=0, column=1, sticky="e", padx=(12, 0))
            for button_column, sign in enumerate(("1", "X", "2")):
                button = tk.Button(
                    selector, text=sign, width=3, padx=1, pady=1, relief="solid", bd=1,
                    background="#fffafa", foreground="#ef7777", activebackground="#ffcaca",
                    font=("DejaVu Sans", 9, "bold"),
                    command=lambda i=index, s=sign: toggle_base_sign(i, s),
                )
                button.grid(row=0, column=button_column)
                base_buttons[(index, sign)] = button

        size_label = ttk.Label(base_tab, text="", style="Big.TLabel")
        size_label.grid(row=16, column=0, columnspan=2, sticky="w", pady=(10, 6))

        def render_base_buttons(index=None):
            indices = range(14) if index is None else (index,)
            for item_index in indices:
                selected = set(base_vars[item_index].get())
                for sign in ("1", "X", "2"):
                    active = sign in selected
                    base_buttons[(item_index, sign)].configure(
                        text=sign,
                        background="#e94d5c" if active else "#fffafa",
                        foreground="white" if active else "#ef7777",
                        relief="sunken" if active else "solid",
                    )

        def toggle_base_sign(index, sign):
            selected = set(base_vars[index].get())
            if sign in selected:
                if len(selected) == 1:
                    return
                selected.remove(sign)
            else:
                selected.add(sign)
            base_vars[index].set("".join(value for value in ("1", "X", "2") if value in selected))
            render_base_buttons(index)

        def update_base_size(*_args):
            try:
                size = development_size([tuple(variable.get()) for variable in base_vars])
                cost = max(2, size) * BET_PRICE
                size_label.configure(text=f"{size:,} columnas posibles  ·  coste completo aproximado: {cost:,.2f} €")
            except ValueError:
                size_label.configure(text="Selecciona al menos un signo en cada partido")
            render_base_buttons()

        def apply_base_level(raw_level):
            level = max(0, min(10, int(round(float(raw_level)))))
            ranked_matches = sorted(
                range(14), key=lambda i: max(self.matches[i].probabilities) - min(self.matches[i].probabilities)
            )
            triples = level // 3
            doubles = level
            for index, variable in enumerate(base_vars):
                order = sorted(zip(("1", "X", "2"), self.matches[index].probabilities), key=lambda item: item[1], reverse=True)
                variable.set(order[0][0])
            for index in ranked_matches[:doubles]:
                order = sorted(zip(("1", "X", "2"), self.matches[index].probabilities), key=lambda item: item[1], reverse=True)
                base_vars[index].set("".join(sign for sign, _ in order[:2]))
            for index in ranked_matches[:triples]:
                base_vars[index].set("1X2")
            update_base_size()
            coverage_description.configure(
                text=f"Nivel {level}/10 · {triples} triples · {max(0, doubles - triples)} dobles · {14 - doubles} fijos"
            )

        presets = ttk.LabelFrame(base_tab, text="Cobertura progresiva", padding=10, style="Card.TLabelframe")
        presets.grid(row=17, column=0, columnspan=2, sticky="ew", pady=6)
        coverage_scale = tk.Scale(
            presets, from_=0, to=10, orient="horizontal", resolution=1, showvalue=False,
            background="#0c294b", foreground="white", troughcolor="#123b65",
            activebackground="#ffc83d", highlightthickness=0, sliderrelief="raised",
            command=apply_base_level,
        )
        coverage_scale.pack(fill="x", padx=8)
        ticks = tk.Frame(presets, background="#0c294b")
        ticks.pack(fill="x", padx=9)
        for value in range(11):
            tk.Label(ticks, text=str(value), background="#0c294b", foreground="#8fcdf2", font=("DejaVu Sans", 8)).pack(side="left", expand=True)
        coverage_description = ttk.Label(presets, text="Nivel 5/10", style="Card.TLabel", font=("DejaVu Sans", 10, "bold"))
        coverage_description.pack(pady=(5, 0))
        coverage_scale.set(5)
        for variable in base_vars:
            variable.trace_add("write", update_base_size)
        render_base_buttons()
        update_base_size()

        ttk.Label(
            base_tab,
            text="0 mantiene todos los partidos fijos. Al avanzar hacia 10 se añaden progresivamente dobles y triples.",
            style="Muted.TLabel", wraplength=900,
        ).grid(row=18, column=0, columnspan=2, sticky="w", pady=(5, 0))

        ttk.Label(conditions_tab, text="ELIGE TUS CONDICIONES", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            conditions_tab, text="Puedes dejar los valores tal como están: así ningún filtro elimina columnas.", style="Muted.TLabel"
        ).pack(anchor="w", pady=(2, 12))
        fields = ttk.LabelFrame(conditions_tab, text="Distribución de signos", padding=14, style="Card.TLabelframe")
        fields.pack(side="left", anchor="n", fill="y", padx=(0, 14))
        specs = (
            ("Resultados que no son 1", "0", "14"), ("Cantidad de empates (X)", "0", "14"),
            ("Cantidad de victorias visitantes (2)", "0", "14"), ("Cambios entre signos", "0", "13"),
        )
        range_vars: list[tuple[tk.StringVar, tk.StringVar]] = []
        for row, (label, low, high) in enumerate(specs):
            ttk.Label(fields, text=label, width=24).grid(row=row, column=0, sticky="w", pady=4)
            minimum, maximum = tk.StringVar(value=low), tk.StringVar(value=high)
            range_vars.append((minimum, maximum))
            ttk.Entry(fields, textvariable=minimum, width=6).grid(row=row, column=1)
            ttk.Label(fields, text="a").grid(row=row, column=2, padx=6)
            ttk.Entry(fields, textvariable=maximum, width=6).grid(row=row, column=3)

        run_vars = {sign: tk.StringVar(value=str(default)) for sign, default in (("1", 14), ("X", 14), ("2", 14))}
        for offset, sign in enumerate(("1", "X", "2"), 4):
            ttk.Label(fields, text=f"Máximo de {sign} seguidos", width=24).grid(row=offset, column=0, sticky="w", pady=4)
            ttk.Entry(fields, textvariable=run_vars[sign], width=6).grid(row=offset, column=1)

        reduction_var = tk.StringVar(value="100")
        ttk.Label(fields, text="Columnas que quiero guardar", width=32).grid(row=7, column=0, sticky="w", pady=(16, 4))
        ttk.Entry(fields, textvariable=reduction_var, width=8).grid(row=7, column=1)

        distance_x_vars = (tk.StringVar(value="1"), tk.StringVar(value="14"))
        ttk.Label(fields, text="Separación entre empates (X)", width=32).grid(row=8, column=0, sticky="w", pady=(12, 4))
        ttk.Entry(fields, textvariable=distance_x_vars[0], width=6).grid(row=8, column=1)
        ttk.Label(fields, text="a").grid(row=8, column=2, padx=6)
        ttk.Entry(fields, textvariable=distance_x_vars[1], width=6).grid(row=8, column=3)

        reference_var = tk.StringVar()
        repetition_vars = (tk.StringVar(value="0"), tk.StringVar(value="14"))
        ttk.Label(fields, text="Comparar con columna", width=32).grid(row=9, column=0, sticky="w", pady=(12, 4))
        ttk.Entry(fields, textvariable=reference_var, width=24).grid(row=9, column=1, columnspan=3, sticky="ew")
        ttk.Label(fields, text="Coincidencias permitidas", width=32).grid(row=10, column=0, sticky="w", pady=4)
        ttk.Entry(fields, textvariable=repetition_vars[0], width=6).grid(row=10, column=1)
        ttk.Label(fields, text="a").grid(row=10, column=2, padx=6)
        ttk.Entry(fields, textvariable=repetition_vars[1], width=6).grid(row=10, column=3)

        help_card = ttk.LabelFrame(conditions_tab, text="¿Qué significa?", padding=16, style="Card.TLabelframe")
        help_card.pack(side="left", anchor="n", fill="both", expand=True)
        ttk.Label(
            help_card,
            text=("• Resultados que no son 1: suma de X y 2.\n\n"
                  "• Cambios entre signos: mide si la columna alterna mucho.\n\n"
                  "• Seguidos: evita rachas como 11111 o XXX.\n\n"
                  "• Separación entre X: controla la distancia entre empates.\n\n"
                  "• Comparar: pega 14 signos, por ejemplo 1X211X…, y limita cuántos se repiten.\n\n"
                  "• Columnas a guardar: selecciona las más probables intentando que sean diferentes."),
            style="Card.TLabel", justify="left", wraplength=390,
        ).pack(anchor="w")
        ttk.Label(help_card, text="AJUSTES RÁPIDOS", font=("Sans", 10, "bold"), style="Card.TLabel").pack(anchor="w", pady=(20, 8))

        def apply_condition_level(raw_level):
            level = max(0, min(10, int(round(float(raw_level)))))
            values = (
                (round(level * 0.5), max(round(14 - level * 0.6), round(level * 0.5))),
                (round(level * 0.2), max(round(14 - level * 0.8), round(level * 0.2))),
                (round(level * 0.1), max(round(14 - level * 0.9), round(level * 0.1))),
                (round(level * 0.5), max(round(13 - level * 0.3), round(level * 0.5))),
                (max(4, 14 - level), max(2, 12 - level), max(2, 12 - level)),
                max(25, 200 - level * 15),
            )
            for variables, limits in zip(range_vars, values[:4]):
                variables[0].set(str(limits[0])); variables[1].set(str(limits[1]))
            for sign, maximum in zip(("1", "X", "2"), values[4]):
                run_vars[sign].set(str(maximum))
            reduction_var.set(str(values[5]))
            condition_description.configure(
                text=f"Nivel {level}/10 · variantes {values[0][0]}–{values[0][1]} · conserva hasta {values[5]} columnas"
            )

        condition_scale = tk.Scale(
            help_card, from_=0, to=10, orient="horizontal", resolution=1, showvalue=False,
            background="#0c294b", foreground="white", troughcolor="#123b65",
            activebackground="#ff8a3d", highlightthickness=0, sliderrelief="raised",
            command=apply_condition_level,
        )
        condition_scale.pack(fill="x")
        condition_ticks = tk.Frame(help_card, background="#0c294b")
        condition_ticks.pack(fill="x")
        for value in range(11):
            tk.Label(condition_ticks, text=str(value), background="#0c294b", foreground="#8fcdf2", font=("DejaVu Sans", 8)).pack(side="left", expand=True)
        condition_description = ttk.Label(help_card, text="Nivel 5/10", style="Card.TLabel", wraplength=390)
        condition_description.pack(pady=(6, 0))
        condition_scale.set(5)

        columns_tree = ttk.Treeview(result_tab, columns=("n", "column", "prob"), show="headings")
        columns_tree.heading("n", text="#")
        columns_tree.heading("column", text="Columna")
        columns_tree.heading("prob", text="Probabilidad modelo")
        columns_tree.column("n", width=55, anchor="center")
        columns_tree.column("column", width=420, anchor="center")
        columns_tree.column("prob", width=180, anchor="e")
        columns_tree.grid(row=0, column=0, sticky="nsew")
        summary = ttk.Label(result_tab, text="Configura la base y pulsa Crear desarrollo.", padding=(0, 10), font=("Sans", 11, "bold"))
        summary.grid(row=1, column=0, sticky="ew")
        generated: list[tuple[str, ...]] = []

        def read_int(variable, label):
            try:
                return int(variable.get())
            except ValueError as exc:
                raise ValueError(f"{label}: introduce un número entero") from exc

        def generate():
            nonlocal generated
            try:
                base = [tuple(variable.get()) for variable in base_vars]
                total = development_size(base)
                if total > 1_000_000:
                    raise ValueError(
                        f"La base produce {total:,} columnas. Reduce algún triple/doble para quedar por debajo de 1.000.000."
                    )
                ranges = [(read_int(low, label), read_int(high, label)) for (low, high), (label, _, _) in zip(range_vars, specs)]
                config = FilterConfig(
                    variants=ranges[0], x_count=ranges[1], two_count=ranges[2],
                    interruption_range=ranges[3],
                    max_runs={sign: read_int(variable, f"Racha de {sign}") for sign, variable in run_vars.items()},
                    distance_ranges={"X": (
                        read_int(distance_x_vars[0], "Separación mínima de X"),
                        read_int(distance_x_vars[1], "Separación máxima de X"),
                    )},
                )
                reference = re.sub(r"[^1X2]", "", reference_var.get().upper())
                if reference:
                    if len(reference) != 14:
                        raise ValueError("La columna de comparación debe contener exactamente 14 signos")
                    config.reference = tuple(reference)
                    config.repetition_range = (
                        read_int(repetition_vars[0], "Coincidencias mínimas"),
                        read_int(repetition_vars[1], "Coincidencias máximas"),
                    )
                probabilities = tuple(tuple(value / 100 for value in match.probabilities) for match in self.matches[:14])
                filtered = list(filter_columns(generate_columns(base), config, probabilities))
                ranked = [column for column, _score in rank_columns(filtered, probabilities)]
                target = max(1, read_int(reduction_var, "Reducción"))
                generated = reduce_columns(ranked, target, probabilities)
            except ValueError as exc:
                messagebox.showwarning("Configuración no válida", str(exc), parent=dialog)
                return
            # El resultado reducido, no solo la base, pasa a la quiniela principal.
            self.apply_development_to_main(
                columns=generated, source=f"desarrollo reducido de {len(generated)} columnas",
            )
            for item in columns_tree.get_children():
                columns_tree.delete(item)
            stats = analyze(generated, probabilities)
            ranked_result = rank_columns(generated, probabilities)
            probability_by_column = {column: math.exp(score) * 100 for column, score in ranked_result}
            for index, column in enumerate(generated, 1):
                columns_tree.insert("", "end", values=(index, " ".join(column), f"{probability_by_column[column]:.8f} %"))
            summary.configure(text=(
                f"Base: {total:,} · Tras condiciones: {len(filtered):,} · Desarrollo final: {len(generated):,} · "
                f"Variantes medias: {stats.get('average_variants', 0):.2f} · Masa probabilística: {stats.get('probability_mass', 0) * 100:.6f} %"
            ))
            notebook.select(result_tab)

        def export_development():
            if not generated:
                messagebox.showwarning("Sin columnas", "Primero genera el desarrollo.", parent=dialog)
                return
            pleno = self.predictions.get(self._key(self.matches[14]), "")
            if not re.fullmatch(r"[012M]-[012M]", pleno):
                messagebox.showwarning("Falta el Pleno al 15", "Define el Pleno al 15 en la pantalla principal antes de exportar.", parent=dialog)
                return
            target = filedialog.asksaveasfilename(
                parent=dialog, title="Exportar desarrollo", defaultextension=".txt",
                initialfile=f"desarrollo_{self.season}_J{self.round_no:02d}_{len(generated)}columnas.txt",
                filetypes=(("TXT para Quinielista", "*.txt"), ("Todos", "*.*")),
            )
            if target:
                Path(target).write_text(
                    quinielista_text(generated, pleno),
                    encoding="utf-8",
                )
                self.status.configure(text=f"Desarrollo validado y exportado: {len(generated)} columnas en {target}")

        ttk.Button(buttons, text="▶  Crear desarrollo", command=generate, style="Green.TButton").pack(side="left")
        ttk.Button(buttons, text="Guardar archivo…", command=export_development, style="Purple.TButton").pack(side="left", padx=6)
        ttk.Button(buttons, text="🌐 Subir TXT y jugar", command=self.open_quinielista, style="Gold.TButton").pack(side="left")
        ttk.Button(buttons, text="Cerrar", command=dialog.destroy).pack(side="right")


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
    if args.check:
        raise SystemExit(check())
    QuinielaApp().mainloop()
