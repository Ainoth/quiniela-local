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

## Guardado guiado 0.1.9 — 12/10/2026

- 137 pruebas Studio correctas; 32 pruebas históricas con GUI correctas.
- Exportación de fila distinta de la quiniela abierta, TXT/JSON exactos,
  reducción con Plenos múltiples, cantidades repetidas, coste congelado,
  cancelación y bloqueo durante condiciones pendientes.
- El diálogo no abre carpeta ni web al construirse/mostrarse. Los clics de sus
  botones se comprueban con mocks; demo/pasada/futura no habilitan la web.
- Solo se anuncian Plenos realmente presentes en las apuestas exportadas.
  Streaming comunica su cantidad real sin modificar el borrador original.
- Ruff completo en diálogo y pruebas nuevas; Ruff F en src/tests y diff limpio.
- Arranque Qt/X11 con perfil temporal y self-check correctos. Wheel y sdist
  0.1.9 construidos; importación de la wheel aislada incluye el nuevo diálogo.
- Capturas Qt/X11 revisadas: Mis Sistemas a 1200×820 y confirmación a 660×420,
  sin recortes de controles. Ejemplo ficticio de 162 apuestas reducido a 18,
  dos Plenos, TXT de 18 líneas y coste de referencia de 13,50 €.
- Página y muestra del proveedor contrastadas sin cargar archivos ni efectuar
  compras. Abrir la web no constituye validación, envío ni pago desde Studio.
- Windows sigue preparado y sin prueba nativa; no cambia el esquema SQLite.

## Continuación v1.0.0 en casa — 13/10/2026

- `./run_studio.sh --self-check` y `--smoke-test`: correctos en Linux; el
  segundo abre/cierra Qt en X11. Instalación editable local: versión 1.0.0.
- `.venv-studio/bin/python -m pytest -q`: **219 pruebas superadas en 74,51 s**.
- `RUN_PC_GUI_TESTS=1 python3 -m unittest discover -q`: **32 pruebas históricas
  superadas**. Android permanece sin cambios.
- Ruff E9/F/I en servicios, modelos, cartera, ventana, diálogos y pruebas
  modificadas: correcto. No se afirma limpieza completa de estilo heredado.
- Capturas Qt/offscreen de Optimizar, propuesta y parámetros avanzados revisadas
  a 1024×768. Detectado y corregido el recorte de avanzados: tamaño mínimo
  vertical de 909 a 729 píxeles; botones de presupuesto/cancelación accesibles.
- Regresiones: referencias con idéntica cantidad aun con mínimos por Pleno;
  inicio/éxito/cancelación/fallo correlacionados; cancelar no aplica selecciones;
  edición/restauración retiran garantías obsoletas sin borrar el histórico;
  ranking logarítmico de probabilidades y marginales del Pleno extremadamente
  pequeñas; datos desbordados producen error de dominio, no OverflowError.
- Wheel 1.0.0 construida con aislamiento de dependencias de compilación,
  importada directamente desde el archivo fuera del código fuente; comprobado
  el caso de 72 columnas/5 € y los nuevos módulos. El primer intento sin
  aislamiento falló por ausencia de setuptools en el entorno; el build aislado
  lo resuelve sin añadir dependencias de cálculo a la aplicación.

### Referencia cuantitativa sintética

`scripts/benchmark_portfolio.py`, Python 3.12.3/Linux x86_64, probabilidades demo
50/30/20, 9 fijos + 3 dobles + 2 triples, Pleno M0, semilla 123. Ambas carteras:
6 apuestas, 4,50 €, remanente 0,50 €. Universos y probabilidades idénticos.

| Métrica | Referencia v0.1.13 | Automático v1.0.0 |
|---|---:|---:|
| Cobertura uniforme 13+ | 36,11 % | 63,89 % |
| Cobertura ponderada 13+ | 62,99 % | 79,92 % |
| Cobertura ponderada 12+ | 89,45 % | 99,44 % |
| Distancia media de Hamming | 1,667 | 3,133 |
| Masa absoluta estimada de 14 | 0,02441 % | 0,01172 % |
| Mínimo dentro de los 72 resultados | 10 | 11 |

La mejora de cobertura sacrifica masa de 14. Verificación exacta sobre esta base
sintética; selección heurística, **sin óptimo global ni premio económico
garantizado**. Última medición con tracemalloc: 0,513 s y pico de 64.211 bytes
atribuible al cálculo; no es un límite de rendimiento universal.

Cambios principales: `application/services.py`, `domain/models.py`,
`domain/portfolio.py`, `ui/window.py`, `ui/portfolio_dialogs.py` y sus regresiones
`test_portfolio.py` / `test_v1_gui.py`; plan, manual, requisitos, trazabilidad,
registro de cambios y nota de continuidad actualizados.

Límites que permanecen: tiempo configurado acota la búsqueda, no toda la
verificación posterior; muestreo no certifica garantías; valor esperado
desactivado sin datos económicos fiables; TXT/CSV agrupados propios, no un
formato de importación TuLotero documentado. Windows nativo y validación/pago
externos no probados. Siguiente fase: pruebas de escala/UX y validación nativa
Windows, manteniendo separadas estimación probabilística y garantía combinatoria.

## Corrección v1.0.2 — 14/10/2026

- RF-UX-005: icono original incluido en `ui/assets` mediante package-data.
  Verificación Qt/X11 con perfil temporal: `WM_CLASS` es `quiniela-ai-studio`,
  `_NET_WM_ICON` contiene 256×256 píxeles (lectura `xprop -len 1000000` para
  evitar truncar la propiedad) y un diálogo hereda el icono.
- Wheel/sdist construidas con entorno aislado de setuptools; importación desde
  la wheel en `/tmp`, fuera del código fuente: recurso PNG legible e icono válido.
  `--smoke-test` nativo de esa wheel correcto con perfil temporal.
- 11 pruebas de `test_startup.py` y `test_aciertos_layout.py` correctas;
  Ruff E9/F/I en código cambiado y `git diff --check` correctos. Acceso directo
  y entrada de menú locales asociados con `StartupWMClass=quiniela-ai-studio`,
  comprobados mediante `desktop-file-validate`.
- Windows: AppUserModelID preparado; sin validación nativa en esta entrega.
  Las ventanas ya abiertas necesitan reiniciarse para cargar el icono.

## Publicación v1.0.1 — 14/10/2026

- Versión de paquete, interfaz, README y manual: 1.0.1. El motor permanece
  `portfolio-1.0.0`; no se modifican reglas, esquema ni hashes anteriores.
- 228 pruebas Studio correctas; 2 omitidas por TXT personales opcionales ausentes.
  32 pruebas heredadas de escritorio correctas. Ruff E9/F/I en archivos de código
  y pruebas modificados; diff correcto.
- Arranque de elección probado por clic en Sí/No, normal/reducida, caché y errores
  de descarga. Conservación de apuestas/hashes previos comprobada.
- Boleto fijo, Aciertos completo y tabla clásica revisados visualmente con
  datos sintéticos explícitos; geometría comprobada a 1024×768, 1200×975 y
  1920×1080. Pleno múltiple y procedencia de porcentajes permanecen comprobados.
- Self-check y arranque Qt/X11 correctos con perfil temporal. Wheel/sdist 1.0.1
  construidas; importación y arranque Qt de la wheel fuera del código fuente
  verificados. Instalación editable y acceso de escritorio actualizados.
- Publicación limitada a código, documentación y pruebas. ZIP original, TXT
  personales, bases SQLite y apuestas del usuario permanecen fuera del commit.
  Windows nativo sigue pendiente, conforme al alcance de la base.
