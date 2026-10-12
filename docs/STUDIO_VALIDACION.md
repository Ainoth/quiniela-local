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

## Escritorio integrado v0.1.1 — 10/10/2026

- 69 pruebas Studio: importación carpeta/ZIP/red simulada, nombres y fuentes,
  XML cruzado/inválido/entidades, rollback, cancelación y cierre de Qt,
  migración con copia previa, recuperación SQLite idempotente, filtros contra
  oráculo exhaustivo, restauración de origen y conservación de cantidades.
- 32 pruebas de regresión Tkinter, incluidas las GUI con `RUN_PC_GUI_TESTS=1`.
- Ruff: chequeo completo de módulos/tests nuevos y chequeo F del conjunto Studio.
  El formato compacto histórico no se ha reescrito en esta integración.
- Arranque Qt real Linux/X11 y revisión visual de Inicio, Crear, Optimizar,
  Escrutinio y Configuración a 1024×768 con datos públicos, en perfil temporal.
- Descarga real: 80 jornadas WIN1X2 y fuente pública de `26-27/J12`, con
  identidad de los 15 equipos validada. `Andorra` / `ANDORRA FC` se registra
  como alias nominal explícito; no hay coincidencias difusas.
- Directo real: el proveedor no ofrece esa jornada en la consulta realizada.
  No se afirma éxito en vivo para ella. El flujo parcial/caché/errores se
  verifica con fixtures sintéticos; no se consulta otra jornada como fallback.
- Wheel y sdist v0.1.1 incluyen los adaptadores compartidos. Se comprueba la
  importación del wheel en un directorio separado y la inicialización de Qt.
- Acceso de escritorio existente apunta a `run_studio.sh`; no se sustituyen
  accesos de la versión anterior. Windows sigue sin prueba nativa.

## Revisión de aceptación 0.1.2 — 11/10/2026

- 81 pruebas Studio, con fixture original de 12 apuestas / 900 céntimos,
  round-trip, escrutinio, streaming con memoria acotada, reglas de precio,
  quiniela permanente, casillas de Pleno y recuperación de selección parcial.
- 32 pruebas históricas/Tkinter con GUI, correctas.
- Qt real X11 en perfil temporal y capturas revisadas a 1024×768: los 14
  partidos se muestran completos; exportación, Pleno y pie accesibles.
- Ruff: F en src/tests Studio y chequeo completo de los nuevos selección/tests.
- Benchmark: 59.049 apuestas en 0,7698 s, 8,985 MiB Python, cancelación 0,0258 s.
- Paquetes 0.1.2 y dependencias actualizados; comprobación del wheel separado.
- Linux verificado. Windows preparado pero sin ejecución nativa; Android intacto.

La arquitectura y experiencia visual se describen en `STUDIO_V01_ENTREGA.md`.
Los resultados no acreditan fases v0.2–v1.0, predicciones ni garantías.

## Corrección 0.1.3 — 11/10/2026

83 pruebas Studio: clics reales en casillas de filtro, activación independiente,
valores inactivos ignorados y referencia obligatoria sin modificar el sistema.
Captura Qt/X11 a 1024×768 revisada con datos sintéticos; panel con desplazamiento.
Los avisos de reductores e IA pendientes no representan su implementación.

## Corrección 0.1.4 — 11/10/2026

85 pruebas Studio correctas, incluidas validación no modal, desmarcado por clic
en el indicador, reset de filtros y progreso tras invalidar el desarrollo.

## Barra progresiva 0.1.5

86 pruebas Studio correctas. GUI: barra visible en Optimizar, sincronización
bidireccional, previsualización sin modificar apuestas, 3.456 combinaciones en
nivel 10 y bloqueo conservado. Se usa el algoritmo existente; no hay nuevo reductor.

## Ajustes rápidos 0.1.6

94 pruebas Studio: parámetros históricos de condiciones, niveles anidados con
oráculo independiente, límites nuevos inválidos y recuperación de 729 apuestas
con Plenos/cantidades al ampliar el nivel. No se evalúa ningún modelo predictivo.

## Optimizar reactivo 0.1.7

100 pruebas Studio correctas: actualización automática, cambios rápidos,
cancelación/cierre, presupuesto final, restauración de condiciones y resultado
vacío sin exportar columnas nuevas. Filtros y nuevas pruebas con Ruff completo;
conjunto src/tests con Ruff F. Sin cambios de esquema SQLite ni reglas de juego.

Regresión histórica: 32 pruebas con GUI correctas. Captura de Optimizar
reactivo Qt/X11 a 1200×820 revisada; paquete 0.1.7 aislado y arranque real
correctos. Windows sigue pendiente de ejecución nativa.

## Aciertos, Pleno múltiple y Reducidas 0.1.8 — 12/10/2026

- 120 pruebas Studio: matrices/cobertura exhaustiva, mapeo de dobles, extras,
  parejas múltiples/no cartesianas, coste, JSON/TXT/streaming y persistencia.
- Refresco automático con proveedor simulado, aciertos/fallos/P15, errores no
  modales, caché intacta con equipos incorrectos y cierre durante petición.
- Comparación partido a partido y selección mantenida al cambiar el ranking.
- 32 pruebas históricas con GUI correctas; Android permanece intacto.
- Qt real/X11: capturas sintéticas de Aciertos y Reducidas revisadas a 1200×820;
  Pleno visible en cabecera. Datos de ejemplo claramente señalizados.
- Proveedor real: devuelve los 15 partidos de la jornada seleccionada; identidad
  contrastada con el registro público de jornada mediante SQLite en modo ro.
  No se leen apuestas personales para esta comprobación ni se incluyen en Git.
- Catálogo fechado del artículo SELAE: BOE 2009 no vigente; diferencias con PDF
  posterior registradas. Mínimos de matrices verificados, sin afirmar sellado
  autorizado ni equivalencia completa con normativa/formatos actuales.
