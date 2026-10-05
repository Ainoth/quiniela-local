// Sin dependencias. Contrasta el motor Android con el motor Python del escritorio.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const path = require("node:path");
const E = require("../app/src/main/assets/engine.js");
const root = path.resolve(__dirname, "../..");
function python(code, input) {
  return JSON.parse(
    execFileSync("python3", ["-c", code], {
      cwd: root,
      input: JSON.stringify(input),
      encoding: "utf8",
    }),
  );
}
const p = Array.from({ length: 14 }, (_, i) => [
  50 + i * 0.7,
  30 - i * 0.3,
  20 - i * 0.4,
]);
test("Cobertura: los 11 niveles, extremos y 3456 columnas en nivel 10", () => {
  for (let level = 0; level <= 10; level++) {
    const r = E.coverage(p, level);
    assert.equal(r.picks.length, 14);
    assert.equal(
      r.picks.filter((x) => x.length === 3).length,
      Math.floor(level / 3),
    );
    assert.equal(
      r.picks.filter((x) => x.length === 2).length,
      level - Math.floor(level / 3),
    );
    assert.equal(r.picks.filter((x) => x.length === 1).length, 14 - level);
  }
  assert.equal(
    E.coverage(p, 10).picks.reduce((n, s) => n * s.length, 1),
    3456,
  );
});
test("Ajustes rápidos: coincidencia con round() de Python en 0–10", () => {
  const expected = python(
    `import json
print(json.dumps([dict(v=[round(l*.5),round(14-l*.6)],x=[round(l*.2),round(14-l*.8)],t=[round(l*.1),round(14-l*.9)],ints=[round(l*.5),round(13-l*.3)],runs={'1':max(4,14-l),'X':max(2,12-l),'2':max(2,12-l)},limit=max(25,200-l*15)) for l in range(11)]))`,
    null,
  );
  for (let l = 0; l <= 10; l++) assert.deepEqual(E.quick(l), expected[l]);
});
test("Filtros y reducción equivalentes al motor de escritorio", async () => {
  const cols = [];
  for (let n = 0; n < 729; n++)
    cols.push(
      n
        .toString(3)
        .padStart(6, "0")
        .replace(/[012]/g, (x) => "1X2"[+x]) + "1X211X21",
    );
  const f = {
    ...E.quick(7),
    distance: [1, 5],
    reference: "1X211X211X211X",
    repetitions: [3, 11],
  };
  const expected = python(
    `import json,sys
from quiniela_engine import FilterConfig,reduce_columns
x=json.load(sys.stdin); f=x['f']; cfg=FilterConfig(variants=tuple(f['v']),x_count=tuple(f['x']),two_count=tuple(f['t']),max_runs=f['runs'],interruption_range=tuple(f['ints']),distance_ranges={'X':tuple(f['distance'])},reference=tuple(f['reference']),repetition_range=tuple(f['repetitions']))
c=[tuple(c) for c in x['cols'] if cfg.accepts(tuple(c))]; p=[[v/100 for v in r] for r in x['p']]
print(json.dumps({'filtered':[''.join(i) for i in c], 'reduced':[''.join(i) for i in reduce_columns(c,12,p)]}))`,
    { cols, f, p },
  );
  const accepted = cols.filter((c) => E.accepts(c, f));
  assert.ok(accepted.length > 12);
  assert.deepEqual(accepted, expected.filtered);
  assert.deepEqual(await E.reduce(accepted, 12, p), expected.reduced);
  assert.deepEqual(await E.reduce(cols, 0, p), []);
  assert.deepEqual(await E.reduce(cols.slice(0, 2), 5, p), cols.slice(0, 2));
});
test("No adelanta jornada por la fecha nominal mientras quedan partidos", () => {
  const entries = [
    { round: 10, date: new Date(2026, 8, 30) },
    { round: 11, date: new Date(2026, 9, 4) },
  ];
  assert.equal(
    E.currentRound(
      entries,
      (n) => [n === 10 ? "01/10/202620:45" : "05/10/202620:30"],
      () => "",
      new Date(2026, 9, 1, 16),
    ),
    10,
  );
  assert.equal(
    E.currentRound(
      entries,
      (n) => [n === 10 ? "01/10/202620:45" : "05/10/202620:30"],
      () => "",
      new Date(2026, 9, 5, 16),
    ),
    11,
  );
});
test("Marcadores pendientes, suspendidos y desconocidos no son empates", () => {
  for (const estado of [
    "Sin comenzar",
    "Suspendido",
    "Aplazado",
    "Desconocido",
  ])
    assert.equal(
      E.live({ estado, live: 0, local_goles: 0, visitante_goles: 0 }).sign,
      "",
    );
  assert.equal(
    E.live({
      estado: "En juego",
      live: 1,
      local_goles: null,
      visitante_goles: 0,
    }).sign,
    "",
  );
  const r = E.live({
    estado: "Finalizado",
    live: 0,
    local_goles: 4,
    visitante_goles: 1,
  });
  assert.equal(r.sign, "1");
  assert.equal(r.pleno, "M1");
  assert.equal(r.final, true);
  assert.equal(
    E.live({ estado: "Suspendido", sorteado: 1, signo: "2" }).sign,
    "2",
  );
});
test("Escrutinio hexadecimal, 14 signos y cantidades españolas", () => {
  const line =
    "10 1 2 3 4 5 6 100.000,00 50.000,00 100,50 10,00 5,00 1,00".padEnd(
      104,
      " ",
    ) +
    "1X2".repeat(4) +
    "11B";
  const s = E.scrutiny(line);
  assert.equal(s.pleno, "2M");
  assert.equal(s.prizes[0].amount, 100000);
  assert.equal(s.prizes[2].amount, 100.5);
  const fixed =
    "100 2 3 4 5 6 100.000,00 50.000,00 100,50 10,00 5,00 1,00".padEnd(104) +
    "1".repeat(14) +
    "0";
  assert.equal(E.scrutiny(fixed).prizes[0].amount, 100000);
  assert.equal(E.scrutiny(fixed).prizes[0].winners, 0);
  assert.equal(E.scrutiny(fixed).prizes[1].winners, 2);
  assert.equal(E.scrutiny("11".padEnd(209, " ")), null);
});
