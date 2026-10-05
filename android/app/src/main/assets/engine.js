"use strict";
(function (root) {
  const signs = ["1", "X", "2"];
  const roundEven = (x) => {
    const f = Math.floor(x),
      r = x - f;
    return r === 0.5 ? (f % 2 ? f + 1 : f) : Math.round(x);
  };
  function coverage(probabilities, level) {
    level = Math.max(0, Math.min(10, Math.round(level)));
    const order = probabilities.map((row) =>
      signs
        .slice()
        .sort((a, b) => row[signs.indexOf(b)] - row[signs.indexOf(a)]),
    );
    const uncertain = probabilities
      .map((r, i) => ({ i, gap: Math.max(...r) - Math.min(...r) }))
      .sort((a, b) => a.gap - b.gap);
    const picks = order.map((r) => r[0]),
      triples = Math.floor(level / 3);
    uncertain
      .slice(0, level)
      .forEach(
        ({ i }) =>
          (picks[i] = signs
            .filter((s) => order[i].slice(0, 2).includes(s))
            .join("")),
      );
    uncertain.slice(0, triples).forEach(({ i }) => (picks[i] = "1X2"));
    return { picks, triples, doubles: level - triples, fixed: 14 - level };
  }
  function quick(level) {
    const r = roundEven;
    return {
      v: [r(level * 0.5), r(14 - level * 0.6)],
      x: [r(level * 0.2), r(14 - level * 0.8)],
      t: [r(level * 0.1), r(14 - level * 0.9)],
      ints: [r(level * 0.5), r(13 - level * 0.3)],
      runs: {
        1: Math.max(4, 14 - level),
        X: Math.max(2, 12 - level),
        2: Math.max(2, 12 - level),
      },
      limit: Math.max(25, 200 - level * 15),
    };
  }
  function accepts(c, f) {
    const count = (s) => [...c].filter((x) => x === s).length,
      x = count("X"),
      t = count("2");
    const inRange = (value, range) =>
      !range || (value >= range[0] && value <= range[1]);
    if (!inRange(x + t, f.v) || !inRange(x, f.x) || !inRange(t, f.t))
      return false;
    let changes = 0;
    for (let i = 1; i < c.length; i++) changes += c[i] !== c[i - 1];
    if (!inRange(changes, f.ints)) return false;
    for (const s of signs) {
      let run = 0;
      for (const v of c) {
        run = v === s ? run + 1 : 0;
        if (run > (f.runs?.[s] ?? 14)) return false;
      }
    }
    if (f.distance) {
      let previous = -1;
      for (let i = 0; i < c.length; i++)
        if (c[i] === "X") {
          if (previous >= 0 && !inRange(i - previous, f.distance)) return false;
          previous = i;
        }
    }
    if (
      f.reference &&
      !inRange(
        [...c].filter((s, i) => s === f.reference[i]).length,
        f.repetitions,
      )
    )
      return false;
    return true;
  }
  function logProbability(c, p) {
    return [...c].reduce(
      (n, s, i) =>
        n + Math.log(Math.max((p[i]?.[signs.indexOf(s)] ?? 0) / 100, 1e-300)),
      0,
    );
  }
  function ranked(columns, p) {
    return columns
      .map((c) => ({ c, score: logProbability(c, p) }))
      .sort((a, b) => b.score - a.score);
  }
  function distance(a, b) {
    let n = 0;
    for (let i = 0; i < a.length; i++) n += a[i] !== b[i];
    return n;
  }
  async function reduce(columns, target, p, yieldFn = async () => {}) {
    if (target <= 0) return [];
    const unique = [...new Set(columns)];
    if (unique.length <= target) return unique;
    const list = ranked(unique, p);
    const chosen = [list[0].c],
      used = new Uint8Array(list.length),
      min = new Uint8Array(list.length).fill(14);
    used[0] = 1;
    while (chosen.length < target) {
      let best = -1;
      const last = chosen[chosen.length - 1];
      for (let i = 0; i < list.length; i++) {
        if (used[i]) continue;
        min[i] = Math.min(min[i], distance(list[i].c, last));
        if (best < 0 || min[i] > min[best]) best = i;
        if (i % 20000 === 19999) await yieldFn();
      }
      if (best < 0) break;
      chosen.push(list[best].c);
      used[best] = 1;
      if (chosen.length % 8 === 0) await yieldFn();
    }
    return chosen;
  }
  function scrutiny(line) {
    const result = line.slice(104, 118);
    if (!/^[1X2]{14}$/.test(result)) return null;
    const n = parseInt(line[118], 16),
      g = "012M",
      pleno = Number.isFinite(n) ? g[n >> 2] + g[n % 4] : "";
    const tokens = line.slice(2, 104).match(/\d[\d.]*,\d{2}|\d+/g) || [];
    return {
      result,
      pleno,
      prizes: [15, 14, 13, 12, 11, 10].map((cat, i) => ({
        cat,
        winners: +tokens[i] || 0,
        amount:
          +(tokens[i + 6] || "0").replace(/\./g, "").replace(",", ".") || 0,
      })),
    };
  }
  function currentRound(entries, hours, pre, now = new Date()) {
    const day = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const pending = entries.filter((e) => !scrutiny(pre(e.round)));
    // Mantener la jornada hasta el último día con partidos. Si termina sin escrutinio,
    // avanzar solo cuando comienza la siguiente jornada del calendario.
    const active = pending.find((e) => {
      const kick = hours(e.round).map(parseKickoff).filter(Boolean);
      const end = kick.length
        ? new Date(Math.max(...kick.map((d) => d.getTime())))
        : e.date;
      end.setHours(23, 59, 59, 999);
      return end >= now;
    });
    return (
      active?.round ||
      pending.find((e) => e.date >= day)?.round ||
      entries[entries.length - 1]?.round ||
      1
    );
  }
  function parseKickoff(text) {
    const m = text.match(/^(\d{2})\/(\d{2})\/(\d{4})\s*(\d{2}):(\d{2})/);
    return m ? new Date(+m[3], +m[2] - 1, +m[1], +m[4], +m[5]) : null;
  }
  function live(row) {
    const status = String(row.estado || "").trim(),
      final = /^(finalizado|final|terminado|finalizada)$/i.test(status),
      pending = /^(sin comenzar|pendiente|aplazado|suspendido)$/i.test(status);
    let sign = "",
      pleno = "",
      score = "—",
      done = final;
    const valid =
      (final || String(row.live) === "1") &&
      !pending &&
      [row.local_goles, row.visitante_goles].every((x) =>
        /^\d{1,2}$/.test(String(x)),
      );
    if (valid) {
      const h = +row.local_goles,
        a = +row.visitante_goles;
      score = h + " - " + a;
      sign = h > a ? "1" : h < a ? "2" : "X";
      pleno = [h, a].map((x) => (x >= 3 ? "M" : String(x))).join("");
    }
    if (String(row.sorteado) === "1") {
      const s = String(row.signo || "").toUpperCase(),
        p = String(row.signo_goles || "")
          .replace("-", "")
          .toUpperCase();
      if (signs.includes(s)) {
        sign = s;
        done = true;
      }
      if (/^[012M]{2}$/.test(p)) pleno = p;
    }
    return {
      ...row,
      final: done,
      score,
      sign,
      pleno,
      status:
        status +
        (pending ? " · " + (row.dia || "") + " " + (row.hora || "") : ""),
    };
  }
  root.QuinielaEngine = {
    coverage,
    quick,
    accepts,
    ranked,
    reduce,
    logProbability,
    scrutiny,
    currentRound,
    parseKickoff,
    live,
  };
  if (typeof module !== "undefined") module.exports = root.QuinielaEngine;
})(typeof globalThis !== "undefined" ? globalThis : this);
