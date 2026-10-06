"use strict";
const E = QuinielaEngine,
  PRICE = 0.75,
  SIGNS = ["1", "X", "2"];
const PCT_URL =
  "https://www.quinielista.es/xml2/porcentajes_completo.asp?jornada=";
const LIVE_URL = "https://static.dataradar.es/marcador/json/partidos.json";
const PLAY_URL = "https://www.eduardolosilla.es/quiniela/archivos";
let state = {
  season: "",
  round: 0,
  currentRound: 0,
  matches: [],
  winData: null,
  rounds: {},
  updated: "",
};
let liveRows = [],
  liveTimer = null,
  busy = false,
  liveBusy = false,
  page = "quiniela",
  requestId = 0,
  developmentPage = 0,
  hitsPage = 0;
const requests = new Map();
function el(id) {
  return document.getElementById(id);
}
function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (x) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        x
      ],
  );
}
function toast(text) {
  Android.notify(text);
}
const yieldUI = () => new Promise((resolve) => setTimeout(resolve, 0));
function showLoading(text) {
  el("loadingText").textContent = text;
  el("loading").classList.remove("hidden");
  busy = true;
}
function hideLoading() {
  el("loading").classList.add("hidden");
  busy = false;
}
function localKey() {
  return state.season + ":" + state.round;
}
function emptyRound() {
  return {
    picks: Array(14).fill(""),
    pleno: ["", ""],
    development: null,
    original: null,
    imported: [],
    source: "development",
    probabilities: null,
    conditions: null,
    coverage: null,
    summary: null,
  };
}
function current() {
  return state.rounds[localKey()] || (state.rounds[localKey()] = emptyRound());
}
function save() {
  try {
    localStorage.setItem("quinielaStateV2", JSON.stringify(state));
  } catch (e) {
    toast("No se pudo guardar: " + e.message);
  }
}
function restore() {
  try {
    let saved = JSON.parse(localStorage.getItem("quinielaStateV2"));
    if (saved) {
      state = { ...state, ...saved };
      return;
    }
    const old = JSON.parse(localStorage.getItem("quinielaState"));
    if (old) {
      state.season = old.season;
      state.round = old.round;
      state.currentRound = old.round;
      state.matches = old.matches || [];
      state.rounds[localKey()] = {
        ...emptyRound(),
        picks: old.picks,
        pleno: old.pleno,
        development: old.development?.length ? old.development : null,
        original: old.development?.length ? old.development : null,
        imported: old.imported || [],
      };
      save();
    }
  } catch (e) {
    toast("No se pudo recuperar el estado guardado");
  }
}
function api(method, arg) {
  return new Promise((resolve, reject) => {
    const id = ++requestId;
    requests.set(id, { resolve, reject });
    Android.request(String(id), method, arg || "");
  });
}
window.onNativeResponse = (id, result) => {
  const req = requests.get(+id);
  if (!req) return;
  requests.delete(+id);
  result.startsWith("__ERROR__")
    ? req.reject(Error(result.slice(9)))
    : req.resolve(result);
};
function showPage(id) {
  page = id;
  document
    .querySelectorAll(".page")
    .forEach((x) => x.classList.toggle("active", x.id === id));
  document
    .querySelectorAll("nav button")
    .forEach((x) => x.classList.toggle("active", x.dataset.page === id));
  window.scrollTo(0, 0);
  if (id === "results") renderScrutiny();
  scheduleLive();
}
document
  .querySelectorAll("nav button")
  .forEach((b) => (b.onclick = () => showPage(b.dataset.page)));
document
  .querySelectorAll(".ticks")
  .forEach(
    (x) =>
      (x.innerHTML = Array.from(
        { length: 11 },
        (_, i) => "<span>" + i + "</span>",
      ).join("")),
  );
function editable() {
  return (
    state.round > 0 &&
    state.season === state.winData?.season &&
    state.round === state.currentRound &&
    !scrutiny()
  );
}
function requireEditable() {
  if (!editable())
    throw Error(
      "Esta jornada es de consulta. Pulsa «En curso» para editar la quiniela actual.",
    );
}
function parseDates(text) {
  return text
    .split(/\r?\n/)
    .map((line) => {
      const m = line.match(/^(\d{2}):(\d{2})\/(\d{2})\/(\d{4})/);
      return m
        ? { round: +m[1], date: new Date(+m[4], +m[3] - 1, +m[2]) }
        : null;
    })
    .filter(Boolean);
}
function roundLine(text, round) {
  return (
    (text || "")
      .split(/\r?\n/)
      // PRE reserva dos caracteres para la jornada; el siguiente ya es un
      // número de acertantes y puede estar pegado (p. ej. «100...» = J10, 0).
      .find(
        (line) =>
          /^\d{1,2}$/.test(line.slice(0, 2).trim()) &&
          +line.slice(0, 2) === round,
      ) || ""
  );
}
function parseHours(text, round) {
  const line =
    (text || "")
      .split(/\r?\n/)
      .find((x) => x.startsWith(String(round).padStart(2, "0"))) || "";
  return Array.from({ length: 15 }, (_, i) =>
    line.slice(2 + i * 15, 17 + i * 15),
  );
}
function parseNames(text = "") {
  const out = {};
  (text || "").split(/\r?\n/).forEach((line) => {
    const i = line.indexOf("-");
    if (i > 0)
      out[line.slice(0, i).trim().toUpperCase()] = line.slice(i + 1).trim();
  });
  return out;
}
function availableRounds(season = state.season) {
  return parseDates(state.winData?.["FEC" + season + ".TXT"] || "")
    .sort((a, b) => a.round - b.round)
    .filter(
      (e) =>
        roundLine(state.winData?.["PRE" + season + ".TXT"], e.round)
          .slice(119, 209)
          .trim().length === 90,
    );
}
function recalculateCurrent() {
  if (!state.winData) return;
  const season = state.winData.season;
  state.currentRound = E.currentRound(
    availableRounds(season),
    (r) => parseHours(state.winData["HOR" + season + ".TXT"], r),
    (r) => roundLine(state.winData["PRE" + season + ".TXT"], r),
  );
}
function loadRound() {
  if (!state.winData) return;
  const line = roundLine(
      state.winData["PRE" + state.season + ".TXT"],
      state.round,
    ),
    block = line.slice(119, 209),
    names = parseNames(state.winData["WEQUIPOS.TXT"]),
    kick = parseHours(
      state.winData["HOR" + state.season + ".TXT"],
      state.round,
    ),
    pct = current().probabilities;
  state.matches = Array.from({ length: 15 }, (_, i) => {
    const h = block.slice(i * 6, i * 6 + 3),
      a = block.slice(i * 6 + 3, i * 6 + 6);
    return {
      number: i + 1,
      home: names[h] || h,
      away: names[a] || a,
      codes: [h, a],
      kick: kick[i],
      prob: pct?.[i] || null,
    };
  });
  liveRows = [];
  developmentPage = 0;
  hitsPage = 0;
  el("resultStatus").textContent =
    "Temporada " +
    state.season +
    " · Jornada " +
    state.round +
    " · Sin consulta en directo";
}
function moveRound(delta) {
  if (busy) return;
  const rounds = availableRounds(),
    i = rounds.findIndex((x) => x.round === state.round);
  if (rounds[i + delta]) selectRound(rounds[i + delta].round);
}
function selectRound(round, persist = true) {
  if (busy) return;
  if (persist) persistConditions();
  state.round = round;
  loadRound();
  restoreConditions();
  save();
  renderAll();
  scheduleLive();
  if (page === "results") refreshLive();
}
function goCurrentRound() {
  if (busy) return;
  if (!state.winData) return toast("Descarga primero el calendario");
  persistConditions();
  state.season = state.winData.season;
  recalculateCurrent();
  selectRound(state.currentRound, false);
}
function selectSeason(season) {
  if (busy) {
    el("seasonSelect").value = state.season;
    return;
  }
  if (!availableRounds(season).length)
    return toast("No hay jornadas publicadas de esa temporada");
  persistConditions();
  state.season = season;
  selectRound(
    season === state.winData.season
      ? state.currentRound
      : availableRounds().at(-1).round,
    false,
  );
}
function parsePercentages(xml) {
  const header = xml.match(/<porcentajes\b[^>]*>/i)?.[0] || "",
    round = header.match(/\bjornada="(\d+)"/)?.[1],
    season = header.match(/\btemporada="(\d+)"/)?.[1];
  if (
    +round !== state.currentRound ||
    +season !== 2000 + +state.winData.season.slice(-2)
  )
    throw Error("Los porcentajes corresponden a otra temporada o jornada");
  const out = [];
  for (const tag of xml.matchAll(/<partido\b[^>]*>/gi)) {
    const a = {};
    for (const m of tag[0].matchAll(/([\w_]+)="([^"]*)"/g)) a[m[1]] = m[2];
    const n = +a.num,
      row = [+a.p_jugados_1, +a.p_jugados_X, +a.p_jugados_2];
    if (
      n >= 1 &&
      n <= 14 &&
      row.every((x) => Number.isFinite(x) && x >= 0) &&
      Math.abs(row.reduce((a, b) => a + b, 0) - 100) <= 1
    )
      out[n - 1] = row;
  }
  if (
    out.length !== 14 ||
    Array.from({ length: 14 }, (_, i) => out[i]).some((x) => !x)
  )
    throw Error("Los porcentajes recibidos no son válidos");
  return out;
}
async function updateData() {
  if (busy) return;
  showLoading("Descargando calendario, resultados y porcentajes…");
  try {
    persistConditions();
    const data = JSON.parse(await api("winData")),
      season = data.season;
    if (
      !data["FEC" + season + ".TXT"] ||
      !data["PRE" + season + ".TXT"] ||
      !data["HOR" + season + ".TXT"]
    )
      throw Error("Paquete de temporada incompleto");
    const wasCurrent =
      state.season === state.winData?.season &&
      state.round === state.currentRound;
    state.winData = data;
    recalculateCurrent();
    if (!availableRounds().some((x) => x.round === state.round) || wasCurrent) {
      state.season = season;
      state.round = state.currentRound;
    }
    let note = "";
    try {
      const pct = parsePercentages(
        await api("text", PCT_URL + state.currentRound),
      );
      const key = season + ":" + state.currentRound;
      state.rounds[key] ||= emptyRound();
      state.rounds[key].probabilities = pct;
    } catch (e) {
      const cached = state.rounds[season + ":" + state.currentRound]?.probabilities;
      note = cached
        ? " · No se pudieron renovar los porcentajes; se conservan los guardados de esta jornada: " + e.message
        : " · Porcentajes no disponibles: " + e.message;
    }
    state.updated = new Date().toLocaleString("es-ES");
    loadRound();
    restoreConditions();
    save();
    renderAll();
    el("updateStatus").textContent = "Actualizado " + state.updated + note;
    el("updateStatus").classList.toggle("error", !!note);
  } catch (e) {
    el("updateStatus").textContent = "No se pudo actualizar: " + e.message;
    el("updateStatus").classList.add("error");
  } finally {
    hideLoading();
  }
}
function probabilities() {
  if (
    state.matches.slice(0, 14).length !== 14 ||
    state.matches.slice(0, 14).some((m) => !m.prob)
  )
    throw Error(
      "Faltan porcentajes válidos. Pulsa «Actualizar datos» antes de usar el modelo.",
    );
  return state.matches.slice(0, 14).map((m) => m.prob);
}
function probability(c) {
  return Math.exp(
    E.logProbability(
      c,
      state.matches.slice(0, 14).map((m) => m.prob || [0, 0, 0]),
    ),
  );
}
function compactTime(text) {
  const d = E.parseKickoff(text || "");
  return d
    ? ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"][d.getDay()] +
        " " +
        String(d.getHours()).padStart(2, "0") +
        ":" +
        String(d.getMinutes()).padStart(2, "0")
    : "—";
}
function renderMatches() {
  const box = el("matches"),
    r = current(),
    s = scrutiny(),
    disabled = editable() ? "" : "disabled";
  box.innerHTML = "";
  state.matches.forEach((m, i) => {
    const selected = s ? (i < 14 ? s.result[i] : s.pleno) : null;
    if (i < 14) {
      const row = document.createElement("div");
      row.className = "match";
      row.innerHTML =
        '<span class="num">' +
        (i + 1) +
        '</span><span class="teams history" data-history="' +
        i +
        '">' +
        escapeHtml(m.home) +
        " - " +
        escapeHtml(m.away) +
        '</span><span class="meta">' +
        compactTime(m.kick) +
        '</span><span class="meta">' +
        (m.prob ? m.prob.map((x) => x.toFixed(0)).join("/") : "— / — / —") +
        '</span><span class="picks">' +
        SIGNS.map(
          (sign) =>
            "<button " +
            disabled +
            ' class="pick ' +
            ((selected || r.picks[i] || "").includes(sign) ? "on" : "") +
            '" data-i="' +
            i +
            '" data-s="' +
            sign +
            '">' +
            sign +
            "</button>",
        ).join("") +
        "</span>";
      box.appendChild(row);
    } else {
      const row = document.createElement("div");
      row.className = "pleno";
      row.innerHTML =
        '<span class="teams history" data-history="14">15. ' +
        escapeHtml(m.home) +
        "<br>" +
        escapeHtml(m.away) +
        "</span>" +
        [0, 1]
          .map((side) =>
            ["0", "1", "2", "M"]
              .map(
                (g) =>
                  "<button " +
                  disabled +
                  ' class="goal ' +
                  ((selected ? selected[side] : r.pleno[side]) === g
                    ? "on"
                    : "") +
                  '" data-side="' +
                  side +
                  '" data-g="' +
                  g +
                  '">' +
                  g +
                  "</button>",
              )
              .join(""),
          )
          .join("");
      box.appendChild(row);
    }
  });
  box
    .querySelectorAll(".pick")
    .forEach((b) => (b.onclick = () => togglePick(+b.dataset.i, b.dataset.s)));
  box.querySelectorAll(".goal").forEach(
    (b) =>
      (b.onclick = () => {
        try {
          requireEditable();
          r.pleno[+b.dataset.side] = b.dataset.g;
          save();
          renderMatches();
        } catch (e) {
          toast(e.message);
        }
      }),
  );
  box
    .querySelectorAll("[data-history]")
    .forEach((b) => (b.onclick = () => showHistory(+b.dataset.history)));
  updatePrice();
}
function invalidateDevelopment() {
  current().development = null;
  current().original = null;
  current().summary = null;
}
function togglePick(i, s) {
  try {
    requireEditable();
    const r = current(),
      p = r.picks[i] || "";
    r.picks[i] = SIGNS.filter((x) =>
      x === s ? !p.includes(x) : p.includes(x),
    ).join("");
    invalidateDevelopment();
    r.coverage = null;
    save();
    renderAll();
  } catch (e) {
    toast(e.message);
  }
}
function useSuggestions() {
  try {
    requireEditable();
    const p = probabilities();
    current().picks = p.map((row) => SIGNS[row.indexOf(Math.max(...row))]);
    invalidateDevelopment();
    save();
    renderAll();
  } catch (e) {
    toast(e.message);
  }
}
function clearPicks() {
  try {
    requireEditable();
    current().picks = Array(14).fill("");
    current().pleno = ["", ""];
    invalidateDevelopment();
    save();
    renderAll();
  } catch (e) {
    toast(e.message);
  }
}
function applyCoverage(value) {
  try {
    requireEditable();
    const level = +value,
      result = E.coverage(probabilities(), level),
      r = current();
    r.picks = result.picks;
    r.coverage = level;
    invalidateDevelopment();
    save();
    renderAll();
  } catch (e) {
    toast(e.message);
  }
}
function describeCoverage() {
  const r = current(),
    tr = r.picks.filter((x) => x.length === 3).length,
    db = r.picks.filter((x) => x.length === 2).length,
    fi = r.picks.filter((x) => x.length === 1).length;
  el("coverage").value = r.coverage ?? 0;
  el("coverageDescription").textContent =
    (r.coverage === null ? "Selección manual" : "Nivel " + r.coverage + "/10") +
    " · " +
    tr +
    " triples · " +
    db +
    " dobles · " +
    fi +
    " fijos";
}
function baseSize() {
  return current().picks.length === 14 && current().picks.every(Boolean)
    ? current().picks.reduce((n, x) => n * x.length, 1)
    : 0;
}
function updatePrice() {
  const r = current(),
    count = r.development !== null ? r.development.length : baseSize();
  el("price").textContent = count
    ? count.toLocaleString("es-ES") +
      " apuestas · " +
      (Math.max(2, count) * PRICE).toFixed(2) +
      " €" +
      (r.development !== null ? " · desarrollo calculado" : " · base completa")
    : r.development !== null
      ? "Desarrollo vacío: revisa las condiciones"
      : "Selecciona un signo en cada partido";
}
const conditionIds = [
  "varMin",
  "varMax",
  "xMin",
  "xMax",
  "twoMin",
  "twoMax",
  "run1",
  "runX",
  "run2",
  "intMin",
  "intMax",
  "distanceMin",
  "distanceMax",
  "reference",
  "repMin",
  "repMax",
  "limit",
  "budget",
  "quickLevel",
  "probableCount",
];
const defaults = [
  "0",
  "14",
  "0",
  "14",
  "0",
  "14",
  "14",
  "14",
  "14",
  "0",
  "13",
  "1",
  "14",
  "",
  "0",
  "14",
  "125",
  "15",
  "0",
  "10",
];
function persistConditions() {
  if (!state.round) return;
  current().conditions = Object.fromEntries(
    conditionIds.map((id) => [id, el(id).value]),
  );
}
function restoreConditions() {
  conditionIds.forEach(
    (id, i) => (el(id).value = current().conditions?.[id] ?? defaults[i]),
  );
  describeQuick();
}
function describeQuick() {
  el("quickDescription").textContent =
    "Nivel " +
    el("quickLevel").value +
    "/10 · variantes " +
    el("varMin").value +
    "–" +
    el("varMax").value +
    " · conserva hasta " +
    el("limit").value +
    " columnas";
}
function applyQuick(level) {
  try {
    requireEditable();
    const f = E.quick(+level);
    [
      ["var", f.v],
      ["x", f.x],
      ["two", f.t],
      ["int", f.ints],
    ].forEach(([id, r]) => {
      el(id + "Min").value = r[0];
      el(id + "Max").value = r[1];
    });
    SIGNS.forEach((s) => (el("run" + s).value = f.runs[s]));
    el("limit").value = f.limit;
    describeQuick();
    persistConditions();
    save();
  } catch (e) {
    toast(e.message);
  }
}
document.querySelectorAll(".form-grid input").forEach((x) => {
  x.setAttribute("data-edit", "");
  x.addEventListener("change", () => {
    persistConditions();
    describeQuick();
    save();
  });
});
function ranges() {
  const n = (id) => {
    const value = Number(el(id).value);
    if (el(id).value === "" || !Number.isFinite(value))
      throw Error("Introduce números válidos en las condiciones");
    return value;
  };
  const range = (prefix, low = 0, high = 14) => {
    const r = [n(prefix + "Min"), n(prefix + "Max")];
    if (
      r.some((x) => !Number.isInteger(x) || x < low || x > high) ||
      r[0] > r[1]
    )
      throw Error("Intervalo no válido: " + prefix);
    return r;
  };
  const ref = el("reference").value.trim().toUpperCase();
  if (ref && !/^[1X2]{14}$/.test(ref))
    throw Error("La columna de comparación necesita 14 signos 1, X o 2");
  const runs = { 1: n("run1"), X: n("runX"), 2: n("run2") };
  if (Object.values(runs).some((v) => !Number.isInteger(v) || v < 1 || v > 14))
    throw Error("Las rachas deben estar entre 1 y 14");
  const limit = n("limit");
  if (!Number.isInteger(limit) || limit < 1 || limit > 100000)
    throw Error("Columnas finales: entre 1 y 100.000");
  return {
    v: range("var"),
    x: range("x"),
    t: range("two"),
    ints: range("int", 0, 13),
    distance: range("distance", 1, 14),
    reference: ref,
    repetitions: range("rep"),
    runs,
    limit,
  };
}
async function makeColumns(filter = null, maxCandidates = 1000000) {
  const picks = current().picks;
  if (!baseSize()) throw Error("Selecciona al menos un signo por partido");
  if (baseSize() > maxCandidates)
    throw Error(
      "La base supera 1.000.000 de columnas. Reduce dobles o triples.",
    );
  let buffer = [""];
  for (const pick of picks) {
    const next = [];
    for (const c of buffer) for (const s of pick) next.push(c + s);
    buffer = next;
    await yieldUI();
  }
  if (filter) {
    const out = [];
    for (let i = 0; i < buffer.length; i++) {
      if (E.accepts(buffer[i], filter)) out.push(buffer[i]);
      if (i % 10000 === 0) await yieldUI();
    }
    return out;
  }
  return buffer;
}
function syncDevelopment(cols, summary) {
  const r = current();
  developmentPage = 0;
  hitsPage = 0;
  r.development = cols;
  r.summary = summary;
  if (cols.length)
    r.picks = Array.from({ length: 14 }, (_, i) =>
      SIGNS.filter((s) => cols.some((c) => c[i] === s)).join(""),
    );
  r.coverage = null;
  save();
  renderAll();
}
async function generateDevelopment() {
  if (busy) return;
  try {
    requireEditable();
    const p = probabilities(),
      f = ranges(),
      total = baseSize();
    persistConditions();
    showLoading("Generando y filtrando columnas…");
    await yieldUI();
    const filtered = await makeColumns(f);
    el("loadingText").textContent = "Reduciendo por probabilidad y diversidad…";
    const cols = await E.reduce(filtered, f.limit, p, yieldUI);
    current().original = cols.slice();
    syncDevelopment(cols, { base: total, filtered: filtered.length });
    toast(cols.length + " columnas enviadas a la quiniela principal");
  } catch (e) {
    toast(e.message);
  } finally {
    hideLoading();
  }
}
async function generateProbable() {
  if (busy) return;
  try {
    requireEditable();
    const p = probabilities(),
      target = Number(el("probableCount").value);
    if (!Number.isInteger(target) || target < 2 || target > 100)
      throw Error("Elige entre 2 y 100 columnas");
    showLoading("Calculando columnas más probables…");
    const orders = p.map((row, i) =>
      SIGNS.filter((s) =>
        (el("respectBase").checked
          ? current().picks[i] || "1X2"
          : "1X2"
        ).includes(s),
      ).sort((a, b) => row[SIGNS.indexOf(b)] - row[SIGNS.indexOf(a)]),
    );
    const initial = Array(14).fill(0),
      seen = new Set([initial.join(",")]),
      front = [initial],
      cols = [];
    while (front.length && cols.length < target) {
      front.sort(
        (a, b) =>
          E.logProbability(b.map((n, i) => orders[i][n]).join(""), p) -
          E.logProbability(a.map((n, i) => orders[i][n]).join(""), p),
      );
      const ix = front.shift();
      cols.push(ix.map((n, i) => orders[i][n]).join(""));
      for (let i = 0; i < 14; i++) {
        const next = ix.slice();
        next[i]++;
        const key = next.join(",");
        if (next[i] < orders[i].length && !seen.has(key)) {
          seen.add(key);
          front.push(next);
        }
      }
    }
    current().original = cols.slice();
    syncDevelopment(cols, { base: baseSize(), filtered: cols.length });
    showPage("develop");
  } catch (e) {
    toast(e.message);
  } finally {
    hideLoading();
  }
}
async function optimizeBudget() {
  if (busy) return;
  try {
    requireEditable();
    const r = current(),
      budget = Number(el("budget").value);
    if (!Number.isFinite(budget) || budget < 1.5)
      throw Error("El presupuesto mínimo es 1,50 €");
    if (!r.original?.length)
      throw Error(
        "Primero genera un desarrollo. El optimizador trabaja con esas columnas.",
      );
    const cols = E.ranked(r.original, probabilities())
      .slice(0, Math.floor(budget / PRICE))
      .map((x) => x.c);
    syncDevelopment(cols, {
      base: r.original.length,
      filtered: r.original.length,
    });
    showPage("develop");
  } catch (e) {
    toast(e.message);
  }
}
function renderDevelopment() {
  const r = current(),
    cols = r.development || [];
  if (r.development === null) {
    el("devSummary").textContent =
      "Todavía no hay un desarrollo en esta jornada.";
    el("columns").innerHTML = "";
    el("developmentPager").innerHTML = "";
    return;
  }
  const average = (sign) =>
    cols.length
      ? cols.reduce(
          (sum, c) => sum + [...c].filter((s) => sign.includes(s)).length,
          0,
        ) / cols.length
      : 0;
  el("devSummary").textContent =
    (r.summary?.base ?? baseSize()) +
    " de base · " +
    (r.summary?.filtered ?? cols.length) +
    " tras filtros · " +
    cols.length +
    " finales · " +
    ((cols.length ? Math.max(2, cols.length) : 0) * PRICE).toFixed(2) +
    " € · variantes medias " +
    average("X2").toFixed(2) +
    " · X " +
    average("X").toFixed(2) +
    " · 2 " +
    average("2").toFixed(2) +
    " · probabilidad total " +
    (cols.reduce((s, c) => s + probability(c), 0) * 100).toFixed(7) +
    " %";
  developmentPage = Math.min(
    developmentPage,
    Math.max(0, Math.ceil(cols.length / 100) - 1),
  );
  el("columns").innerHTML = E.ranked(
    cols,
    state.matches.slice(0, 14).map((m) => m.prob || [0, 0, 0]),
  )
    .slice(developmentPage * 100, (developmentPage + 1) * 100)
    .map(
      (x, i) =>
        '<div class="column"><b>' +
        String(developmentPage * 100 + i + 1) +
        ". " +
        x.c +
        "</b><span>" +
        (Math.exp(x.score) * 100).toFixed(7) +
        " %</span></div>",
    )
    .join("");
  renderPager("developmentPager", developmentPage, cols.length, "development");
}
function renderPager(id, index, count, kind) {
  const total = Math.max(1, Math.ceil(count / 100));
  updateHtml(
    id,
    count > 100
      ? "<button " +
          (index === 0 ? "disabled" : "") +
          " onclick=\"movePage('" +
          kind +
          "',-1)\">‹ Anterior</button><small>Página " +
          (index + 1) +
          " / " +
          total +
          " · " +
          count +
          " columnas</small><button " +
          (index >= total - 1 ? "disabled" : "") +
          " onclick=\"movePage('" +
          kind +
          "',1)\">Siguiente ›</button>"
      : "",
  );
}
function movePage(kind, delta) {
  if (kind === "development") {
    developmentPage = Math.max(0, developmentPage + delta);
    renderDevelopment();
    el("devSummary").scrollIntoView({ block: "start" });
  } else {
    hitsPage = Math.max(0, hitsPage + delta);
    evaluateLive();
    el("hitsSummary").scrollIntoView({ block: "start" });
  }
}
async function betText() {
  const r = current();
  let cols =
    r.development === null ? await makeColumns(null, 100000) : r.development;
  if (!cols.length) throw Error("El desarrollo está vacío");
  if (!r.pleno.every(Boolean))
    throw Error("Completa el Pleno al 15 antes de exportar");
  return cols.map((c) => c + r.pleno.join("")).join("\n") + "\n";
}
async function exportTxt() {
  if (busy) return;
  try {
    showLoading("Preparando TXT…");
    const text = await betText();
    Android.saveText(
      "quiniela_" +
        state.season +
        "_J" +
        String(state.round).padStart(2, "0") +
        "_" +
        text.trim().split("\n").length +
        "apuestas.txt",
      text,
    );
  } catch (e) {
    toast(e.message);
  } finally {
    hideLoading();
  }
}
async function copyBets() {
  try {
    Android.copyText(await betText());
  } catch (e) {
    toast(e.message);
  }
}
function openPlaySite() {
  Android.openUrl(PLAY_URL);
}
window.onImportedText = (text, name) => {
  const bets = text
    .split(/\r?\n/)
    .map((x) => x.trim().toUpperCase().replace(/\s/g, ""))
    .filter(Boolean);
  if (!bets.length || bets.some((x) => !/^([1X2]{14})([012M]{2})?$/.test(x)))
    return toast("TXT no válido: una apuesta de 14 o 16 signos por línea");
  const m = (name || "").match(/(\d{2}-\d{2})_J(\d+)/i);
  if (m && (m[1] !== state.season || +m[2] !== state.round)) {
    toast(
      "El archivo indica temporada " +
        m[1] +
        ", jornada " +
        m[2] +
        ". Selecciona esa jornada y vuelve a cargarlo.",
    );
    return;
  }
  current().imported = bets;
  current().importedName = name || "TXT";
  current().source = "imported";
  save();
  renderAll();
  showPage("results");
  checkOfficial();
  refreshLive();
};
function switchSource(source) {
  current().source = source;
  hitsPage = 0;
  save();
  renderAll();
  if (liveRows.length) evaluateLive();
  renderScrutiny();
}
function useCurrentDevelopment() {
  switchSource("development");
  if (!current().development?.length)
    toast("Esta jornada no tiene un desarrollo guardado");
}
function checkedBets() {
  const r = current();
  return r.source === "imported"
    ? r.imported
    : r.development?.map(
        (c) => c + (r.pleno.every(Boolean) ? r.pleno.join("") : ""),
      ) || [];
}
function scrutiny() {
  return E.scrutiny(
    roundLine(state.winData?.["PRE" + state.season + ".TXT"], state.round),
  );
}
function checkOfficial() {
  renderScrutiny();
  const s = scrutiny();
  if (s) {
    liveRows = state.matches.map((m, i) => ({
      orden: i + 1,
      local: m.home,
      visitante: m.away,
      score: "—",
      sign: i < 14 ? s.result[i] : "",
      pleno: i === 14 ? s.pleno : "",
      final: true,
      status: "Escrutinio descargado",
    }));
    renderLive();
    evaluateLive();
    el("resultStatus").textContent =
      "Temporada " +
      state.season +
      " · Jornada " +
      state.round +
      " · Resultado definitivo descargado";
    el("resultStatus").classList.remove("error");
  } else
    el("resultStatus").textContent =
      "Jornada " +
      state.round +
      ": escrutinio todavía pendiente. Actualiza los datos para volver a comprobar.";
}
async function refreshLive(automatic = false) {
  if (busy || liveBusy || !state.round) return;
  const key = localKey();
  if (!automatic)
    el("resultStatus").textContent = "Consultando jornada " + state.round + "…";
  liveBusy = true;
  try {
    const raw = await api("text", LIVE_URL + "?r=" + Date.now());
    if (key !== localKey()) return;
    const year = 2000 + +state.season.slice(-2),
      rows = JSON.parse(raw)
        .filter((r) => +r.temporada === year && +r.jornada === state.round)
        .sort((a, b) => +a.orden - +b.orden);
    if (rows.length !== 15 || rows.some((r, i) => +r.orden !== i + 1))
      throw Error("El proveedor no publica el directo de esta jornada");
    liveRows = rows.map(E.live);
    renderLive();
    evaluateLive();
    renderScrutiny();
    el("resultStatus").textContent =
      "Temporada " +
      state.season +
      " · Jornada " +
      state.round +
      " · " +
      liveRows.filter((x) => x.final).length +
      "/15 finalizados · Consulta " +
      new Date().toLocaleTimeString();
    el("resultStatus").classList.remove("error");
  } catch (e) {
    if (key !== localKey()) return;
    if (scrutiny()) checkOfficial();
    else {
      el("resultStatus").textContent =
        e.message + " · Los datos anteriores conservan su hora de consulta.";
      el("resultStatus").classList.add("error");
    }
  } finally {
    liveBusy = false;
    if (key !== localKey() && page === "results") refreshLive();
    else scheduleLive();
  }
}
function scheduleLive() {
  clearTimeout(liveTimer);
  if (page === "results" && el("autoLive").checked && !document.hidden)
    liveTimer = setTimeout(() => refreshLive(true), 60000);
}
document.addEventListener("visibilitychange", scheduleLive);
function updateHtml(id, html) {
  if (el(id).innerHTML !== html) el(id).innerHTML = html;
}
function renderLive() {
  updateHtml(
    "liveMatches",
    liveRows
      .map(
        (r, i) =>
          '<div class="live-row ' +
          (r.final ? "final" : "") +
          '"><b>' +
          (i + 1) +
          "</b><span>" +
          escapeHtml(r.local) +
          " - " +
          escapeHtml(r.visitante) +
          '</span><span class="score">' +
          escapeHtml(r.score) +
          '</span><span class="sign">' +
          escapeHtml(i === 14 ? r.pleno || "—" : r.sign || "—") +
          '</span><small class="state">' +
          escapeHtml(r.status) +
          "</small></div>",
      )
      .join(""),
  );
}
function evaluateLive() {
  const bets = checkedBets();
  if (!bets.length) {
    el("hitsSummary").textContent =
      "Sin apuestas guardadas para temporada " +
      state.season +
      ", jornada " +
      state.round;
    el("hits").innerHTML = "";
    el("hitsPager").innerHTML = "";
    return;
  }
  const known = liveRows.slice(0, 14).filter((x) => x.sign),
    final = known.filter((x) => x.final),
    p15 = liveRows[14],
    items = bets
      .map((b) => {
        const hits = known.filter((x) => b[x.orden - 1] === x.sign).length,
          miss = final.filter((x) => b[x.orden - 1] !== x.sign).length,
          p =
            b.length < 16
              ? "Sin P15"
              : !p15?.pleno
                ? "Pendiente"
                : (b.slice(14) === p15.pleno ? "Sí" : "No") +
                  (p15.final ? "" : " (prov.)");
        return { b, hits, fixed: final.length - miss, max: 14 - miss, p };
      })
      .sort((a, b) => b.hits - a.hits || b.max - a.max);
  el("hitsSummary").textContent =
    bets.length +
    " apuestas · mejor " +
    items[0].hits +
    "/" +
    known.length +
    " conocidos · " +
    items[0].fixed +
    " confirmados · máximo " +
    items[0].max;
  hitsPage = Math.min(hitsPage, Math.max(0, Math.ceil(items.length / 100) - 1));
  updateHtml(
    "hits",
    '<div class="hit-row hit-head"><span>Columna / confirmados</span><span>Ahora</span><span>Máx. / Pleno</span></div>' +
      items
        .slice(hitsPage * 100, (hitsPage + 1) * 100)
        .map(
          (x) =>
            '<div class="hit-row"><b>' +
            x.b +
            "<br><small>" +
            x.fixed +
            " confirmados</small></b><span>" +
            x.hits +
            "</span><span>" +
            x.max +
            " / " +
            x.p +
            "</span></div>",
        )
        .join(""),
  );
  renderPager("hitsPager", hitsPage, items.length, "hits");
}
function renderScrutiny() {
  const s = scrutiny(),
    bets = checkedBets();
  if (!s) {
    el("prizes").textContent =
      "Escrutinio de jornada " +
      state.round +
      " todavía no publicado en los datos descargados.";
    return;
  }
  const counts = {};
  bets.forEach((b) => {
    const h = [...s.result].filter((x, i) => b[i] === x).length,
      plenoHit = h === 14 && b.slice(14) === s.pleno;
    counts[h] = (counts[h] || 0) + 1;
    if (plenoHit) counts[15] = (counts[15] || 0) + 1;
  });
  let total = 0;
  el("prizes").innerHTML =
    '<div class="notice">Jornada ' +
    state.round +
    " · " +
    s.result +
    " · Pleno " +
    s.pleno.split("").join("-") +
    '</div><div class="prize-row hit-head"><b>Categoría</b><span>Tuyas / oficiales</span><span>€/apuesta</span><span>Premio</span></div>' +
    s.prizes
      .map((p) => {
        const mine = counts[p.cat] || 0,
          sub = mine * p.amount;
        total += sub;
        return (
          '<div class="prize-row"><b>' +
          (p.cat === 15 ? "Pleno 15" : p.cat) +
          "</b><span>" +
          mine +
          " / " +
          p.winners +
          "</span><span>" +
          p.amount.toFixed(2) +
          "</span><strong>" +
          sub.toFixed(2) +
          "</strong></div>"
        );
      })
      .join("") +
    '<div class="big-result">Premio calculado ' +
    total.toFixed(2) +
    " €</div>";
}
function showHistory(index) {
  const m = state.matches[index];
  if (!m) return;
  el("historyTitle").textContent = m.home + " – " + m.away;
  const text = state.winData?.["ESTARESU.TXT"] || "",
    names = parseNames(state.winData?.["WEQUIPOS.TXT"]);
  const domestic = new Set();
  for (const code of ["RS1", "RS2"]) {
    const raw = state.winData?.[code + state.season + ".TXT"] || "";
    for (const r of raw.matchAll(
      /\d{4}([A-Z0-9]{3})([A-Z0-9]{3})(?:\d{2}| {2})\d{4}/g,
    )) {
      domestic.add(r[1]);
      domestic.add(r[2]);
    }
  }
  const covered = state.matches
    .slice(0, 14)
    .flatMap((match) => match.codes || [])
    .filter((code) => domestic.has(code)).length;
  if (!text || covered < 8 || !m.codes?.every((c) => domestic.has(c))) {
    el("historyContent").textContent =
      "No hay un histórico local fiable para estos equipos. Los códigos de selecciones internacionales pueden coincidir con los de clubes.";
  } else {
    el("historyContent").innerHTML = m.codes
      .map((code, side) => {
        const games = [];
        for (const g of text.matchAll(
          /([A-Z0-9]{3})([A-Z0-9]{3})(\d{2})(\d)(\d)/g,
        )) {
          if (g[1] === code || g[2] === code) {
            const home = g[1] === code;
            games.push(
              '<div class="column">' +
                escapeHtml(names[home ? g[2] : g[1]] || (home ? g[2] : g[1])) +
                " · " +
                (home ? "Local" : "Visitante") +
                " · " +
                (home ? g[4] + "-" + g[5] : g[5] + "-" + g[4]) +
                " · Temp. " +
                g[3] +
                "</div>",
            );
          }
        }
        return (
          "<h3>" +
          escapeHtml(side ? m.away : m.home) +
          "</h3>" +
          games.slice(-40).reverse().join("")
        );
      })
      .join("");
  }
  el("historyDialog").showModal();
}
function renderAll() {
  const r = current(),
    rounds = availableRounds(),
    i = rounds.findIndex((x) => x.round === state.round);
  const seasons = Object.keys(state.winData || {})
    .filter((k) => /^FEC\d{2}-\d{2}\.TXT$/.test(k))
    .map((k) => k.slice(3, 8))
    .sort()
    .reverse();
  if (!seasons.length && state.season) seasons.push(state.season);
  el("seasonSelect").disabled = !state.winData;
  el("seasonSelect").innerHTML = seasons
    .map(
      (s) =>
        "<option " +
        (s === state.season ? "selected" : "") +
        ">" +
        s +
        "</option>",
    )
    .join("");
  el("seasonLabel").textContent = state.season
    ? "Temporada " + state.season + " · Jornada " + state.round
    : "Aplicación autónoma";
  el("roundTitle").textContent =
    "Temporada " + (state.season || "—") + " · Jornada " + (state.round || "—");
  el("roundMode").textContent = !state.winData
    ? "ACTUALIZA DATOS · calendario pendiente de descargar"
    : editable()
    ? "EN CURSO · edición habilitada"
    : state.season !== state.winData?.season
      ? "TEMPORADA ANTERIOR · consulta"
      : state.round < state.currentRound
        ? "JORNADA ANTERIOR · consulta"
        : state.round > state.currentRound
          ? "PRÓXIMA JORNADA · consulta"
          : "JORNADA FINALIZADA · consulta";
  el("previousRound").disabled = i <= 0;
  el("nextRound").disabled = i < 0 || i >= rounds.length - 1;
  el("nextRound").title = el("nextRound").disabled
    ? "No hay otra jornada publicada por el proveedor"
    : "Jornada siguiente";
  document
    .querySelectorAll("[data-edit]")
    .forEach((x) => (x.disabled = !editable()));
  renderMatches();
  describeCoverage();
  describeQuick();
  renderDevelopment();
  el("betSource").textContent =
    (r.source === "imported"
      ? "TXT: " + (r.importedName || "archivo")
      : "Desarrollo guardado") +
    " · Temporada " +
    state.season +
    " · Jornada " +
    state.round +
    " · " +
    checkedBets().length +
    " apuestas";
  renderLive();
  evaluateLive();
  renderScrutiny();
  if (state.updated)
    el("updateStatus").textContent = "Datos guardados · " + state.updated;
}
restore();
recalculateCurrent();
loadRound();
restoreConditions();
renderAll();
