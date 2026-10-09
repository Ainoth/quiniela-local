# Registro de validación v0.1.0

Validación local: 9–10 de octubre de 2026.

## Entorno comprobado

- Linux Mint 22.3 Zena; kernel 7.0.0-38-generic, glibc 2.39.
- Python 3.12.3; PySide6 6.12.0; pytest 9.1.1.
- CPU Intel Xeon Silver 4114 2.20 GHz; RAM disponible instalada ~125,49 GiB.
- Qt Fusion; arranque real con X11 y `libxcb-cursor0` extraída al entorno virtual.
- Sintaxis del código de Studio validada para Python 3.10 mediante AST.

## Pruebas

```bash
QT_QPA_PLATFORM=offscreen .venv-studio/bin/python -m pytest -q
python3 -m unittest -q
./run_studio.sh --data-dir /tmp/studio-native-ok --smoke-test
```

Resultado base: **35 pruebas Studio y 18 de regresión histórica**, todas correctas.
Las pruebas usan perfiles temporales y datos sintéticos, no los pronósticos reales.

El flujo Qt ejercita: creación → 6 apuestas/450 céntimos → selección por
150 céntimos → 2 apuestas → escrutinio → TXT completo. También bloqueos,
plantillas, navegación de jornadas, consulta protegida y selección conservada
ante refrescos idénticos. Se renderizó a 1024×768 y se verificaron siete páginas.
Pruebas Qt adicionales con escala 200 % en plataforma offscreen; no sustituyen
la validación manual de pantallas físicas ni Windows.

## Benchmark del motor

Comando reproducible:

```bash
PYTHONPATH=. .venv-studio/bin/python scripts/benchmark_studio.py
```

Caso: 10 triples + 4 fijos = **59.049 columnas**, Pleno M0.
Última medición: **0,7613 s**, pico de memoria Python mediante tracemalloc
**8,985 MiB**, cancelación **0,0261 s**. Las medidas se refieren al motor
acotado; no son una promesa universal, no incluyen todo Qt ni toda memoria
nativa y no acreditan todavía el rendimiento del motor masivo de fase 2.

## Artefactos

Generación:

```bash
.venv-studio/bin/python -m build --outdir artifacts/studio
```

- `quiniela_ai_studio-0.1.0-py3-none-any.whl`: paquete Python instalable.
- `quiniela_ai_studio-0.1.0.tar.gz`: fuente con lanzadores/documentación/pruebas.
- `artifacts/studio/benchmark-v0.1.json`: registro local de mediciones.
- Acceso directo local: `Quiniela AI Studio.desktop`; el anterior se conserva.

No se entrega un EXE autónomo ni se declara probado Windows. La fase de
publicación completa T17 necesita ejecución y paridad de PC en ambas plataformas.
No se modificó ningún archivo `android/` ni los APK existentes.

## Limitaciones que bloquean ampliar el alcance anunciado

Consultar `STUDIO_V0_1.md` para matriz T01–T17. Las pruebas de esta entrega no
certifican fases 2–4, modelos entrenados, reductor con garantía, simulación,
proveedores online ni la paridad completa de la versión anterior.

## Sincronización con GitHub — 10 de octubre de 2026

Integrada la entrega Tkinter de `origin/main` (`69597c0`) con la versión Qt
local, conservando ambos lanzadores. Incorporados los documentos originales
y fixtures del paquete documental; la matriz RF conserva su estado original
pendiente de auditoría, sin declarar cumplimiento nuevo.

Comprobaciones tras la integración:

- `QT_QPA_PLATFORM=offscreen .venv-studio/bin/python -m pytest -q`: 35 correctas.
- `RUN_PC_GUI_TESTS=1 python3 -m unittest discover -q`: 32 correctas.
- Arranque Qt real con perfil temporal y `--smoke-test`: salida 0.
- `git diff --check`: correcto; sin cambios en Android ni APK.
- Acceso de escritorio local `Quiniela AI Studio.desktop`: ejecutable, apunta
  a `run_studio.sh` y tiene `metadata::trusted=true`.

El ZIP documental se conserva localmente, fuera de los commits de esta entrega.
Windows sigue sin ejecución nativa acreditada.
