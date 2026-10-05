// npm install --no-save playwright; node android/tests/browser.test.cjs
// Simula solo el puente nativo. La interfaz, persistencia y motor son los reales.
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const assets = path.resolve(__dirname, "../app/src/main/assets");
const codes = Array.from(
  { length: 30 },
  (_, i) => "T" + String(i + 1).padStart(2, "0"),
).join("");
const pre = (n) =>
  (n === 10
    ? "10 1 2 3 4 5 6 100,00 50,00 10,00 5,00 2,00 1,00".padEnd(104) +
      "1".repeat(14) +
      "0"
    : String(n).padEnd(119)) + codes;
const fixture = {
  season: "26-27",
  "FEC26-27.TXT": "10:01/10/2026\n11:04/10/2026\n12:11/10/2026",
  "PRE26-27.TXT": [10, 11, 12].map(pre).join("\n"),
  "HOR26-27.TXT": [10, 11, 12]
    .map(
      (n) =>
        n +
        Array(15)
          .fill({ 10: "01", 11: "05", 12: "12" }[n] + "/10/202620:30")
          .join(""),
    )
    .join("\n"),
  "WEQUIPOS.TXT": Array.from(
    { length: 30 },
    (_, i) => "T" + String(i + 1).padStart(2, "0") + "-Equipo " + (i + 1),
  ).join("\n"),
};
fixture["FEC25-26.TXT"] = "10:01/10/2025";
fixture["PRE25-26.TXT"] = pre(10);
fixture["HOR25-26.TXT"] = "10" + Array(15).fill("01/10/202520:30").join("");
const pct =
  '<porcentajes temporada="2027" jornada="11">' +
  Array.from(
    { length: 14 },
    (_, i) =>
      `<partido num="${i + 1}" p_jugados_1="${50 + i * 0.7}" p_jugados_X="${30 - i * 0.3}" p_jugados_2="${20 - i * 0.4}"/>`,
  ).join("") +
  "</porcentajes>";
const live = Array.from({ length: 15 }, (_, i) => ({
  orden: i + 1,
  temporada: 2027,
  jornada: 11,
  local: "Equipo " + (i * 2 + 1),
  visitante: "Equipo " + (i * 2 + 2),
  estado: i < 7 ? "Finalizado" : "Sin comenzar",
  local_goles: i < 7 ? 2 : 0,
  visitante_goles: 0,
  live: 0,
}));
(async () => {
  const server = http.createServer((req, res) => {
    const file = path.join(
      assets,
      req.url === "/" ? "index.html" : req.url.split("?")[0],
    );
    if (!file.startsWith(assets) || !fs.existsSync(file)) {
      res.writeHead(404);
      return res.end();
    }
    res.setHeader(
      "Content-Type",
      file.endsWith(".js")
        ? "text/javascript"
        : file.endsWith(".css")
          ? "text/css"
          : "text/html",
    );
    res.end(fs.readFileSync(file));
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: 384, height: 854 },
      isMobile: true,
      hasTouch: true,
    });
    const page = await context.newPage(),
      errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.clock.install({ time: new Date("2026-10-05T12:00:00") });
    await page.addInitScript(
      ({ fixture, pct, live }) => {
        window.nativeCalls = [];
        window.Android = {
          request(id, method, arg) {
            nativeCalls.push({ id, method, arg });
            setTimeout(
              () =>
                onNativeResponse(
                  id,
                  method === "winData"
                    ? JSON.stringify(fixture)
                    : arg.includes("porcentajes")
                      ? pct
                      : JSON.stringify(live),
                ),
              10,
            );
          },
          notify(message) {
            nativeCalls.push({ notify: message });
          },
          saveText(name, text) {
            nativeCalls.push({ name, text });
          },
          copyText(text) {
            nativeCalls.push({ copy: text });
          },
          pickTextFile() {},
          openUrl(url) {
            nativeCalls.push({ url });
          },
        };
      },
      { fixture, pct, live },
    );
    await page.goto("http://127.0.0.1:" + server.address().port);
    await page.evaluate(() => updateData());
    assert.equal(await page.evaluate(() => state.currentRound), 11);
    assert.equal(await page.evaluate(() => editable()), true);
    await page.evaluate(() => applyCoverage(10));
    assert.equal(await page.evaluate(() => baseSize()), 3456);
    await page.evaluate(() => {
      showPage("develop");
      el("quickLevel").value = "9";
      applyQuick(9);
    });
    assert.equal(await page.locator("#limit").inputValue(), "65");
    await page.evaluate(() => generateDevelopment());
    const generated = await page.evaluate(() => current().development);
    assert.ok(generated.length > 2 && generated.length <= 65);
    assert.deepEqual(
      await page.evaluate(() => current().picks),
      Array.from({ length: 14 }, (_, i) =>
        ["1", "X", "2"]
          .filter((s) => generated.some((c) => c[i] === s))
          .join(""),
      ),
    );
    await page.evaluate(() => {
      el("budget").value = "1.5";
      optimizeBudget();
    });
    const reduced = await page.evaluate(() => current().development);
    assert.equal(reduced.length, 2);
    assert.ok(reduced.every((c) => generated.includes(c)));
    await page.evaluate(() => {
      el("budget").value = "100";
      optimizeBudget();
    });
    const optimized = await page.evaluate(() => current().development);
    assert.deepEqual(optimized.slice().sort(), generated.slice().sort());
    await page.evaluate(() => {
      current().pleno = ["M", "1"];
      save();
      exportTxt();
    });
    await page.waitForFunction(() => nativeCalls.some((x) => x.name));
    const exported = await page.evaluate(() => nativeCalls.find((x) => x.name));
    assert.match(exported.name, /26-27_J11/);
    assert.ok(
      exported.text
        .trim()
        .split("\n")
        .every((c) => /^[1X2]{14}M1$/.test(c)),
    );
    await page.evaluate(() => selectRound(10));
    assert.equal(await page.evaluate(() => editable()), false);
    assert.equal(await page.evaluate(() => checkedBets().length), 0);
    assert.ok(await page.locator("#coverage").isDisabled());
    const before = await page.evaluate(() => JSON.stringify(current()));
    await page.evaluate(() => applyCoverage(10));
    assert.equal(await page.evaluate(() => JSON.stringify(current())), before);
    await page.evaluate(() => selectRound(12));
    assert.equal(await page.evaluate(() => editable()), false);
    assert.equal(await page.evaluate(() => current().development), null);
    await page.evaluate(() => goCurrentRound());
    assert.deepEqual(
      await page.evaluate(() => current().development),
      optimized,
    );
    assert.match(await page.locator("#roundMode").textContent(), /EN CURSO/);
    await page.evaluate(() => selectSeason("25-26"));
    assert.equal(await page.evaluate(() => editable()), false);
    assert.equal(await page.evaluate(() => current().development), null);
    assert.equal(await page.evaluate(() => state.currentRound), 11);
    await page.evaluate(() => updateData());
    assert.equal(await page.evaluate(() => state.season), "25-26");
    await page.evaluate(() => goCurrentRound());
    assert.deepEqual(
      await page.evaluate(() => current().development),
      optimized,
    );
    await page.evaluate(() => {
      onImportedText("1".repeat(14) + "00", "quiniela_26-27_J10.txt");
    });
    assert.equal(await page.evaluate(() => current().imported.length), 0);
    await page.evaluate(() => {
      showPage("results");
      useCurrentDevelopment();
    });
    await page.evaluate(() => refreshLive());
    assert.match(
      await page.locator("#hitsSummary").textContent(),
      /\/7 conocidos/,
    );
    await page.evaluate(() => {
      window.repaintCount = 0;
      new MutationObserver((ms) => (repaintCount += ms.length)).observe(
        el("liveMatches"),
        { subtree: true, childList: true },
      );
    });
    await page.evaluate(() => refreshLive(true));
    assert.equal(await page.evaluate(() => repaintCount), 0);
    for (const width of [360, 384, 412, 800]) {
      await page.setViewportSize({ width, height: 854 });
      for (const id of ["quiniela", "develop", "results"]) {
        await page.evaluate((id) => showPage(id), id);
        const overflow = await page.evaluate(() => ({
          width: innerWidth,
          body: document.documentElement.scrollWidth,
        }));
        assert.ok(
          overflow.body <= width,
          `Desbordamiento en ${id} a ${width}px: ${overflow.body}`,
        );
      }
    }
    await page.reload();
    assert.deepEqual(
      await page.evaluate(() => current().development),
      optimized,
    );
    assert.equal(await page.evaluate(() => state.winData.season), "26-27");
    assert.equal(await page.evaluate(() => state.round), 11);
    await page.evaluate(() => {
      selectRound(10);
      onImportedText("1".repeat(14) + "00", "quiniela_26-27_J10.txt");
      checkOfficial();
    });
    assert.match(await page.locator("#prizes").textContent(), /100.00/);
    assert.match(
      await page.locator("#prizes .big-result").textContent(),
      /150.00/,
    );
    assert.match(
      await page.locator("#hitsSummary").textContent(),
      /14\/14 conocidos/,
    );
    await page.waitForFunction(() => !busy);
    await page.evaluate(() => {
      goCurrentRound();
      showPage("quiniela");
      el("respectBase").checked = false;
      el("probableCount").value = "100";
    });
    await page.evaluate(() => generateProbable());
    assert.equal(await page.evaluate(() => current().development.length), 100);
    await page.evaluate(() => {
      current().imported = Array(205).fill("1".repeat(14) + "00");
      current().source = "imported";
      showPage("results");
      checkOfficial();
      evaluateLive();
      movePage("hits", 2);
    });
    assert.match(await page.locator("#hitsPager").textContent(), /3 \/ 3/);
    assert.equal(
      await page.locator("#hits .hit-row:not(.hit-head)").count(),
      5,
    );
    await page.evaluate(() => {
      current().development = Array(205).fill("1".repeat(14));
      showPage("develop");
      renderDevelopment();
      movePage("development", 2);
    });
    assert.equal(await page.locator("#columns .column").count(), 5);
    assert.match(
      await page.locator("#developmentPager").textContent(),
      /3 \/ 3/,
    );
    assert.deepEqual(errors, []);
    console.log(
      "OK: sliders, filtros, generación, sincronización, presupuesto, TXT, jornada aislada/solo lectura, directo, premios, persistencia y 12 layouts móviles",
    );
    if (process.env.SCREENSHOT_DIR) {
      await page.setViewportSize({ width: 384, height: 854 });
      await page.evaluate(() => {
        goCurrentRound();
        showPage("develop");
      });
      await page.screenshot({
        path: path.join(process.env.SCREENSHOT_DIR, "android-desarrollo.png"),
        fullPage: true,
      });
      await page.evaluate(() => showPage("quiniela"));
      await page.screenshot({
        path: path.join(process.env.SCREENSHOT_DIR, "android-quiniela.png"),
        fullPage: true,
      });
    }
    await page.evaluate(() => {
      localStorage.clear();
      localStorage.setItem(
        "quinielaState",
        JSON.stringify({
          season: "26-27",
          round: 10,
          matches: [],
          picks: Array(14).fill("1"),
          pleno: ["0", "0"],
          development: ["1".repeat(14)],
          imported: [],
        }),
      );
    });
    await page.reload();
    await page.evaluate(() => updateData());
    await page.evaluate(() => goCurrentRound());
    assert.equal(await page.evaluate(() => state.round), 11);
    assert.equal(await page.evaluate(() => current().development), null);
    assert.deepEqual(
      await page.evaluate(() => state.rounds["26-27:10"].development),
      ["1".repeat(14)],
    );
    console.log(
      "OK: migración de 1.0.0 conserva las apuestas en su jornada original",
    );
    if (process.env.WIN_ARCHIVE) {
      // Prueba opcional del formato real del proveedor, sin guardar sus datos en Git.
      const { execFileSync } = require("node:child_process"),
        data = { season: "26-27" };
      const entries = execFileSync("unzip", ["-Z1", process.env.WIN_ARCHIVE], {
        encoding: "utf8",
      })
        .trim()
        .split("\n");
      for (const file of entries) {
        const name = file.split("/").at(-1).toUpperCase();
        if (
          /^(?:(?:FEC|PRE|HOR|RS1|RS2)\d{2}-\d{2}\.TXT|WEQUIPOS\.TXT|ESTARESU\.TXT)$/.test(
            name,
          )
        )
          data[name] = new TextDecoder("windows-1252").decode(
            execFileSync("unzip", ["-p", process.env.WIN_ARCHIVE, file]),
          );
      }
      const xml = new TextDecoder("windows-1252").decode(
        execFileSync("curl", [
          "-fsSL",
          "https://www.quinielista.es/xml2/porcentajes_completo.asp?jornada=11",
        ]),
      );
      const real = await context.newPage();
      await real.clock.install({ time: new Date("2026-10-05T12:00:00") });
      await real.addInitScript(
        ({ data, xml }) => {
          localStorage.clear();
          window.Android = {
            request(id, method, arg) {
              setTimeout(
                () =>
                  onNativeResponse(
                    id,
                    method === "winData"
                      ? JSON.stringify(data)
                      : arg.includes("porcentajes")
                        ? xml
                        : "[]",
                  ),
                10,
              );
            },
            notify() {},
            saveText() {},
            copyText() {},
          };
        },
        { data, xml },
      );
      await real.goto("http://127.0.0.1:" + server.address().port);
      await real.evaluate(() => updateData());
      assert.equal(await real.evaluate(() => state.currentRound), 11);
      assert.match(
        await real.evaluate(() => state.matches[0].home),
        /Albacete/i,
      );
      await real.evaluate(() => selectRound(12));
      assert.match(await real.evaluate(() => state.matches[0].home), /Rayo/i);
      assert.equal(await real.evaluate(() => editable()), false);
      await real.evaluate(() => {
        goCurrentRound();
        applyCoverage(5);
        applyQuick(5);
      });
      await real.evaluate(() => generateDevelopment());
      assert.ok(await real.evaluate(() => current().development.length > 0));
      await real.evaluate(() => showHistory(0));
      assert.match(
        await real.locator("#historyContent").textContent(),
        /Temp\./,
      );
      await real.locator("#historyDialog button").click();
      await real.evaluate(() => selectSeason("25-26"));
      assert.equal(await real.evaluate(() => editable()), false);
      const previous = await real.evaluate(() => ({
        season: state.season,
        rounds: availableRounds().length,
        busy,
        keys: Object.keys(state.winData),
      }));
      assert.ok(previous.rounds > 40, JSON.stringify(previous));
      console.log(
        "OK: ZIP WIN1X2 real, porcentajes de jornada 11, navegación a 12 y 25-26, generación e histórico",
      );
      await real.close();
    }
  } finally {
    if (browser) await browser.close();
    server.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
