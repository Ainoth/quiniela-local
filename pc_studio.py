"""Secciones de escritorio; reutilizan los editores probados de la aplicación."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk


class StudioPages:
    SECTIONS = ("Inicio", "Crear Quiniela", "Optimizar", "Análisis", "Escrutinio", "Mis Sistemas", "Configuración")

    def _build_studio_pages(self, host):
        self.pages = {}
        self.nav_buttons = {}
        for index, title in enumerate(self.SECTIONS):
            button = ttk.Button(self.navigation, text=title, command=lambda t=title: self.show_section(t))
            button.grid(row=0, column=index, sticky="ew", padx=2)
            self.navigation.columnconfigure(index, weight=1)
            self.nav_buttons[title] = button
            outer = ttk.Frame(host)
            canvas = tk.Canvas(outer, background="#071a33", highlightthickness=0)
            scroll = ttk.Scrollbar(outer, command=canvas.yview)
            canvas.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            canvas.pack(fill="both", expand=True)
            content = ttk.Frame(canvas, padding=10)
            window = canvas.create_window(0, 0, window=content, anchor="nw")
            canvas.bind("<Configure>", lambda e, c=canvas, w=window: c.itemconfigure(w, width=e.width))
            content.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
            canvas.bind("<MouseWheel>", lambda e, c=canvas: c.yview_scroll(-1 if e.delta > 0 else 1, "units"))
            canvas.bind("<Button-4>", lambda e, c=canvas: c.yview_scroll(-1, "units"))
            canvas.bind("<Button-5>", lambda e, c=canvas: c.yview_scroll(1, "units"))
            self.pages[title] = (outer, content)
            ttk.Label(content, text=title.upper(), style="Section.TLabel").pack(anchor="w", pady=(0, 12))

        def note(page, text):
            label = ttk.Label(self.pages[page][1], text=text, wraplength=380, justify="left", style="Muted.TLabel")
            label.pack(fill="x", pady=(0, 12))
            return label

        def action(page, title, command, style="Accent.TButton"):
            button = ttk.Button(self.pages[page][1], text=title, command=command, style=style)
            button.pack(fill="x", pady=5)
            return button

        self.home_summary = note("Inicio", "Cargando jornada…")
        action("Inicio", "Crear quiniela automáticamente", self.open_system, "Green.TButton")
        action("Inicio", "Crear quiniela manualmente", lambda: self.show_section("Crear Quiniela"), "Gold.TButton")
        action("Inicio", "Consultar mis premios", self.open_prize_checker, "Purple.TButton")
        self.system_summary = note("Inicio", "")
        note("Crear Quiniela", "Marca fijos, dobles o triples en la lista de la izquierda y el Pleno 0/1/2/M. El desarrollo calculado se traslada siempre a esta quiniela.")
        action("Crear Quiniela", "Crear desarrollo · cobertura y filtros 0–10", self.open_advanced, "Green.TButton")
        action("Crear Quiniela", "Completar con sugerencias del modelo", self.use_suggestions, "Gold.TButton")
        action("Crear Quiniela", "Guardar una copia como sistema", self.save_named_system, "Purple.TButton")
        action("Crear Quiniela", "Exportar apuestas TXT", self.export, "Red.TButton")
        self.optimizer_summary = note("Optimizar", "")
        action("Optimizar", "Optimizar el presupuesto de este desarrollo", self.open_budget_optimizer, "Purple.TButton")
        action("Optimizar", "Restaurar desarrollo de origen", self.restore_original, "Gold.TButton")
        note("Optimizar", "Se seleccionan únicamente columnas del desarrollo original. La reducción disponible es heurística: no certifica garantías de 13 o 12 aciertos.")
        self.analysis_summary = note("Análisis", "")
        self.probability_table = ttk.Treeview(self.pages["Análisis"][1], columns=("match", "sport", "public"), show="headings", height=14)
        for column, title, width in (("match", "Nº", 30), ("sport", "Modelo 1 / X / 2", 150), ("public", "Público 1 / X / 2", 150)):
            self.probability_table.heading(column, text=title)
            self.probability_table.column(column, width=width, minwidth=width, stretch=True, anchor="center")
        self.probability_table.pack(fill="x")
        note("Análisis", "Modelo deportivo: heurística de forma reciente, todavía no calibrada. Público: porcentajes jugados, no probabilidades deportivas. Sin histórico, el 40/30/30 es un supuesto identificado, no un dato descargado.")
        action("Escrutinio", "Abrir resultados, aciertos y premios", self.open_prize_checker, "Green.TButton")
        note("Escrutinio", "Puedes comprobar el desarrollo activo o un TXT independiente. Se distingue el directo del escrutinio publicado; acertar 14 y Pleno acumula ambos conceptos de premio.")
        self.library = ttk.Treeview(self.pages["Mis Sistemas"][1], columns=("name", "round", "version"), show="headings", height=8)
        for column, title, width in (("name", "Sistema", 180), ("round", "Jornada", 85), ("version", "Versión", 55)):
            self.library.heading(column, text=title)
            self.library.column(column, width=width, minwidth=50, stretch=True)
        self.library.pack(fill="x")
        self.library.bind("<Double-1>", lambda e: self.open_saved_system())
        action("Mis Sistemas", "Abrir sistema seleccionado", self.open_saved_system)
        action("Mis Sistemas", "Guardar copia del sistema activo", self.save_named_system, "Purple.TButton")
        action("Mis Sistemas", "Importar TXT en la jornada seleccionada", self.import_system_txt, "Gold.TButton")
        action("Mis Sistemas", "Exportar sistema JSON con su jornada", self.export_system_json)
        action("Mis Sistemas", "Consultar versiones del seleccionado", self.show_saved_versions)
        self.legacy_button = action("Mis Sistemas", "Asignar desarrollo antiguo sin jornada", self.assign_legacy, "Orange.TButton")
        note("Mis Sistemas", "Cada cambio conserva una versión anterior. Los sistemas y copias personales se guardan solo en este PC y no se suben a GitHub.")
        note("Configuración", "Fuente para ordenar/generar columnas. Cambiarla no sustituye las apuestas ya calculadas; afecta al siguiente cálculo.")
        source = ttk.Combobox(self.pages["Configuración"][1], textvariable=self.probability_source,
                             values=("Modelo deportivo", "Porcentajes jugados"), state="readonly")
        source.pack(fill="x", pady=8)
        source.bind("<<ComboboxSelected>>", lambda e: self.change_probability_source())
        self.settings_summary = note("Configuración", "")
        action("Configuración", "Descargar partidos y porcentajes", self.update_from_internet, "Green.TButton")
        self.show_section("Inicio")

    def show_section(self, name):
        for title, (frame, _content) in self.pages.items():
            frame.pack_forget()
            self.nav_buttons[title].configure(style="Accent.TButton" if title == name else "Soft.TButton")
        self.pages[name][0].pack(fill="both", expand=True)
        if self.matches:
            self.update_studio_summary()

    def update_studio_summary(self):
        if not self.matches:
            return
        active = self.store.get(self.active_system_id) if self.active_system_id else None
        identity = f"{active['name']} · v{active['sequence']}" if active else "Borrador sin apuestas"
        cols = self.current_development_columns
        self.home_summary.configure(text=f"Temporada {self.season} · Jornada {self.round_no}\n{self.round_mode.get()}\nSistema: {identity}")
        total = len(cols) if cols is not None else None
        self.system_summary.configure(text=(f"{total:,} apuestas calculadas · {total*0.75:.2f} €" if total is not None else "Base manual: marca los signos o crea un desarrollo."))
        pending = self.store.get_meta("unassigned_legacy")
        if pending:
            self.system_summary.configure(text=f"Conservado un desarrollo antiguo de {len(pending):,} columnas, sin jornada identificada. Ve a «Mis Sistemas» para asignarlo; no se mezcla con esta quiniela.")
        origin = self.original_development_columns
        self.optimizer_summary.configure(text=f"Origen conservado: {len(origin):,} columnas.\nActivas: {len(cols or []):,}." if origin else "Primero crea un desarrollo. El optimizador utilizará sus columnas, no otras apuestas.")
        self.analysis_summary.configure(text="Fuente activa: " + self.probability_source.get())
        self.probability_table.delete(*self.probability_table.get_children())
        for m in self.matches[:14]:
            fmt = lambda row: " / ".join(f"{v:.1f}" for v in row) if row else "—"
            self.probability_table.insert("", "end", values=(m.number, fmt(m.sport_probabilities), fmt(m.public_percentages)))
        if cols:
            p = [tuple(v / 100 for v in m.probabilities) for m in self.matches[:14]]
            from quiniela_engine import analyze
            stats = analyze([tuple(c) for c in dict.fromkeys(cols)], p)
            kind = "popularidad" if self.probability_source.get() == "Porcentajes jugados" else "probabilidad de 14"
            self.analysis_summary.configure(text=f"Fuente activa: {self.probability_source.get()}\n{len(cols):,} apuestas · variantes medias {stats['average_variants']:.2f}\nMasa de {kind} bajo independencia: {stats['probability_mass']*100:.6f} %. No es rentabilidad ni garantía.")
        self.library.delete(*self.library.get_children())
        for row in self.store.list():
            self.library.insert("", "end", iid=str(row["id"]), values=(row["name"], f"{row['season']} J{row['round_no']}", row["sequence"]))
        self.legacy_button.configure(state="normal" if self.store.get_meta("unassigned_legacy") else "disabled")
        self.settings_summary.configure(text=f"Almacenamiento local: {self.store.path}\nSin servidor ni compras automáticas.\nEl modelo deportivo actual no es IA entrenada.")

    def save_named_system(self):
        name = simpledialog.askstring("Guardar sistema", "Nombre de la copia:", parent=self)
        if not name:
            return
        system_id = self.store.create(self.season, self.round_no, name, self.system_payload())
        self.store.activate(system_id)
        self.active_system_id = system_id
        self.update_studio_summary()
        self.status.configure(text=f"Sistema «{name}» guardado con su temporada y jornada.")

    def open_saved_system(self):
        selected = self.library.selection()
        if not selected:
            return
        row = self.store.get(int(selected[0]))
        self._save_state()
        self.store.activate(row["id"])
        self.refresh(row["season"], row["round_no"])
        self.show_section("Crear Quiniela")

    def show_saved_versions(self):
        selected = self.library.selection()
        if not selected:
            return
        row = self.store.get(int(selected[0]))
        versions = self.store.versions(row["id"])
        text = "\n".join(f"v{v['sequence']} · {v['created']}" for v in versions[:25])
        messagebox.showinfo("Versiones conservadas — " + row["name"], text, parent=self)
        number = simpledialog.askinteger("Recuperar una versión", "Número de versión para recuperar como copia (Cancelar para solo consultar):",
                                         minvalue=1, maxvalue=row["sequence"], parent=self)
        if number is not None:
            previous = self.store.get(row["id"], number)
            system_id = self.store.create(row["season"], row["round_no"], f"{row['name']} · copia v{number}", previous["payload"])
            self._save_state()
            self.store.activate(system_id)
            self.refresh(row["season"], row["round_no"])

    def export_system_json(self):
        target = filedialog.asksaveasfilename(parent=self, defaultextension=".json", initialfile=f"sistema_{self.season}_J{self.round_no:02d}.json")
        if target:
            value = {"format": "quiniela-pc", "version": 1, "season": self.season, "round": self.round_no, "system": self.system_payload()}
            Path(target).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")

    def import_system_txt(self):
        path = filedialog.askopenfilename(parent=self, filetypes=(("Apuestas TXT", "*.txt"),))
        if not path:
            return
        from app import read_bet_file
        try:
            bets = read_bet_file(Path(path))
            import re
            identity = re.search(r"(\d{2}-\d{2})_J(\d{1,2})", Path(path).name, re.I)
            if identity and (identity[1], int(identity[2])) != (self.season, self.round_no):
                raise ValueError("El nombre del TXT indica otra jornada. Navega a ella antes de importarlo.")
            suffixes = {b[14:] for b in bets}
            if len(suffixes) > 1:
                raise ValueError("Este TXT contiene varios Plenos. Puedes comprobarlo directamente en el escrutador; el editor actual admite uno por desarrollo.")
            if not messagebox.askokcancel("Jornada del TXT", f"Importar {len(bets)} apuestas en {self.season}, jornada {self.round_no}.\nSe conservarán los repetidos como apuestas distintas. ¿Es la jornada correcta?", parent=self):
                return
            suffix = next(iter(suffixes))
            columns = [b[:14] for b in bets]
            if self._editable():
                self.original_development_columns = columns
                self.apply_development_to_main(columns=columns, source="TXT importado")
                if suffix:
                    self.predictions[self._key(self.matches[14])] = "-".join(suffix)
                else:
                    self.predictions.pop(self._key(self.matches[14]), None)
                self._save_state()
            else:
                self.archive_columns(columns, "TXT importado para consulta", "-".join(suffix) if suffix else "")
            self.refresh(self.season, self.round_no)
        except (ValueError, OSError) as e:
            messagebox.showerror("No se pudo importar", str(e), parent=self)

    def assign_legacy(self):
        columns = self.store.get_meta("unassigned_legacy")
        if not columns:
            return
        if messagebox.askokcancel("Asignar desarrollo antiguo", f"El archivo antiguo no indica la jornada de estas {len(columns)} columnas.\n¿Confirmas que corresponden a {self.season}, jornada {self.round_no}?", parent=self):
            self.archive_columns(columns, "Desarrollo antiguo asignado", self.predictions.get(self._key(self.matches[14]), ""))
            self.store.set_meta("unassigned_legacy", None)
            self.refresh(self.season, self.round_no)
            self.update_studio_summary()

    def archive_columns(self, columns, name, pleno):
        """Asignar/importar es archivado, no edición de apuestas pasadas ni generación."""
        self._save_state()
        payload = self.system_payload()
        payload.update(columns=list(columns), original=list(columns), source=name, pleno=pleno,
                       pleno_selection=pleno.split("-") if pleno else ["", ""], generation=None,
                       picks=["".join(s for s in "1X2" if any(c[i] == s for c in columns)) for i in range(14)])
        sid = self.store.create(self.season, self.round_no, name, payload)
        self.store.activate(sid)

    def restore_original(self):
        if not self._require_editable() or not self.original_development_columns:
            return
        self.apply_development_to_main(columns=self.original_development_columns, source="Origen restaurado", preserve_origin=True)
