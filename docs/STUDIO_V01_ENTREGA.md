# Entrega ejecutable v0.1 — revisión 0.1.9

11/10/2026. Esta revisión corrige la interfaz conforme a la preferencia del
usuario: conservar la experiencia de Quiniela Local y su descarga de datos.
Las fases posteriores no se declaran completadas.

## Instalación y ejecución

Linux Mint: Python 3.11 o posterior y soporte venv. Desde la carpeta del proyecto:

```bash
./run_studio.sh
```

El lanzador instala las dependencias en `.venv-studio` si faltan. La instalación
inicial necesita Internet; no hace descargas de jornadas al abrir la app.
En X11, el lanzador reutiliza el soporte local `libxcb-cursor0` documentado en
la guía inicial. Alternativamente instala esa biblioteca mediante el gestor
de paquetes de Mint.

Instalación manual:

```bash
python3 -m venv .venv-studio
.venv-studio/bin/python -m pip install -e '.[test]'
./run_studio.sh
```

Windows preparado, sin prueba nativa: instala Python >=3.11 y abre `run_studio.bat`.
O desde PowerShell:

```powershell
py -3 -m venv .venv-studio
.\.venv-studio\Scripts\python.exe -m pip install -e ".[test]"
.\.venv-studio\Scripts\python.exe -m quiniela_ai_studio
```

## Recorrido comprobable

1. Abre el acceso **Quiniela AI Studio**. En un perfil nuevo aparece una jornada
   **DEMO FICTICIA** sin conexión, con 15 partidos inventados e identificados.
2. Inicio → **Probar ejemplo de 6 apuestas**. Se guardan 6 apuestas por 450
   céntimos con la regla demo de 75 céntimos. No es una tarifa oficial verificada.
3. Los 14 partidos y Pleno quedan a la izquierda incluso al cambiar de sección.
   Los signos seleccionados se muestran por color. El Pleno tiene dos filas
   0/1/2/M; al elegir un solo lado, la selección parcial persiste.
4. Crear Quiniela muestra las primeras 100 filas. TXT/JSON conserva todas las
   apuestas exactas y las cantidades; no reconstruye una reducción desde la base.
5. En Aciertos, el marcador se actualiza automáticamente. Para probar la demo,
   activa resultados manuales; el Pleno requiere 14 aciertos y goles definitivos.
6. Cierra y abre: jornada, sistema, base, selecciones y versiones siguen en SQLite.
7. Configuración → precio por apuesta cambia el precio de sistemas nuevos;
   los ya guardados conservan su coste. Elige8 se reserva como modalidad separada
   y se rechaza si se intenta utilizar en esta versión.
8. Descarga en la cabecera, importación de carpeta/ZIP/XML y copias SQLite antiguas
   conservan el flujo de [la integración v0.1.1](STUDIO_FUSION.md).

El fixture `fixtures/seleccion_demo_v1.json` se importa como JSON de proyecto
sintético: conserva draw_id, reglas y dos parejas de Pleno. Da **12 apuestas / 900
céntimos**. `resultados_demo_v1.json` verifica 14 + Pleno sin premio económico.

## Dónde se generan y cómo guardar las apuestas — 0.1.9

1. **Quiniela normal:** elige los signos y los goles del Pleno en el boleto y
   pulsa **Generar**, abajo a la izquierda. Las apuestas se guardan en la app.
2. **Optimizada:** después de generar, cambia las condiciones en Optimizar y,
   si quieres, aplica el presupuesto. Las apuestas finales se guardan solas.
3. **Reducida:** **Crear copia reducida** ya genera y guarda las apuestas de
   esa copia. Conserva la original en Mis Sistemas.

Cuando las apuestas estén listas, pulsa **Guardar apuestas (TXT)** en la
cabecera desde cualquier pestaña. Elige la carpeta y el nombre del archivo.
El nombre sugerido incluye la jornada y la revisión. Una reducida u optimizada
se guarda con sus apuestas exactas: no pulses Generar para guardarla, porque
Generar desarrolla de nuevo todos los signos del boleto.

Para otra quiniela, entra en **Mis Sistemas**, selecciona su fila y pulsa
**Guardar apuestas de la fila (TXT)**. No necesitas abrirla; el botón de la
cabecera siempre usa la quiniela que aparece como «Abierta».

Al guardar se muestran nombre, temporada, jornada, cantidad de apuestas,
Plenos presentes en el archivo, coste de referencia y ruta. Puedes abrir la
carpeta o pulsar **Abrir web para cargar el TXT**. La web se abre únicamente
por ese clic y el archivo no se sube automáticamente.

La [página de archivos de Quinielista](https://www.eduardolosilla.es/quiniela/archivos)
admite TXT y pide seleccionar archivo e indicar número de apuestas. Comprueba
que su temporada/jornada coincida con tu quiniela, elige el TXT e indica la
cantidad mostrada al guardar. Revisa importe y Pleno antes de confirmar en
la web. Su [muestra pública](https://www.eduardolosilla.es/assets/archivos/1x2.txt)
contiene 14 signos y dos goles por línea, como el contenido exportado por Studio.
Fuentes consultadas el 12/10/2026; no se ha realizado una carga o compra real.
Demo y jornadas de consulta permiten guardar archivos, pero desactivan el botón
de la web. El archivo TXT no incluye la jornada: debes comprobarla en la web.

**Guardar quiniela (JSON)** sirve para conservar el proyecto completo y volver
a abrirlo en Studio. TXT y JSON contienen todas las apuestas guardadas, aunque
la tabla solo muestre las primeras 100 filas. Cada pareja del Pleno y cada copia
cuentan como una línea del TXT; no vuelvas a multiplicar la cantidad mostrada.

## Desarrollo grande

Generar dentro de la aplicación conserva el límite explícito de 100.000 filas.
Para una base grande selecciona el Pleno y usa **Guardar todas las combinaciones**: TXT o JSON se escribe mediante un iterador, con progreso/cancelación,
sin crear millones de objetos en memoria. 14 triples son 4.782.969 columnas
por pareja de Pleno. No se exportan columnas nuevas desde un sistema reducido:
si hay apuestas exactas activas, se exportan exclusivamente esas apuestas.

La importación sigue limitada a 20 MiB y es materializada; este incremento no
anuncia un taller masivo de archivos. El archivo previo permanece intacto si
se cancela antes de publicar la exportación.

## Arquitectura y compatibilidad

- `src/quiniela_ai_studio/domain`: modelos, selección, reglas, combinatoria y filtros;
  sin Qt, disco ni red.
- `application`: servicios y versiones.
- `infrastructure`: SQLite, archivos, proveedores, demo e integración anterior.
- `ui`: ventana PySide6; señales y trabajadores de generación/E/S.
- `src/quiniela_studio`: aliases de compatibilidad para importaciones anteriores;
  el ejecutable principal utiliza `quiniela_ai_studio`.
- Directorios del usuario mediante platformdirs, conservando las rutas de datos
  anteriores. No hay migración destructiva de bases por cambiar el paquete.

## Aceptación y límites

Los cálculos, persistencia, cancelación, archivos y GUI se verifican con fixtures
sintéticos. La documentación de trazabilidad distingue cumplimiento parcial del
requisito completo y de las funcionalidades futuras.

```bash
./run_studio.sh --self-check
QT_QPA_PLATFORM=offscreen .venv-studio/bin/python -m pytest -q
RUN_PC_GUI_TESTS=1 python3 -m unittest discover -q
./run_studio.sh --data-dir /tmp/studio-v01-prueba --smoke-test
.venv-studio/bin/ruff check --select F src tests/studio
.venv-studio/bin/python -m build --outdir artifacts/studio-v01
```

Optimizar/Análisis conservan herramientas básicas ya comprobadas, con el resto
marcado pendiente. No hay rentabilidad, IA entrenada, garantías, Elige8 operativo,
sellado ni pagos. No se modifica Android. Windows necesita validación nativa antes
de anunciarse probado. La fase siguiente del plan original es v0.2, filtros;
no se incluye por cambiar la revisión de v0.1.

## Corrección 0.1.3: filtros y funciones pendientes

En Optimizar marca la casilla junto a cada filtro. La marca ✓ y los límites
habilitados indican su activación. Solo se aplican las condiciones marcadas,
combinadas con AND. Desmarcar una condición ignora sus valores aunque permanezcan
visibles. Coincidencias exige una referencia válida de 14 signos. El botón
muestra cuántos filtros aplicar; al terminar muestra apuestas antes/después.
En ventanas pequeñas desplaza el panel derecho para ver el botón.

Disponible: selección por presupuesto y siete condiciones básicas. Pendientes:
reductores de cobertura/greedy (v0.3), búsqueda local y reinicios (v0.7), y
IA predictiva calibrada con evaluación retrospectiva (v0.6). La app muestra
estos límites en Optimizar y Análisis. Las plantillas 0–10 no son reductores
con garantías. Esta corrección no entrega esas fases futuras.

## Corrección 0.1.4: base frente a desarrollo

«Base» cuenta combinaciones posibles; «apuestas guardadas» cuenta el desarrollo
generado/importado sobre el que trabajan los filtros. Cambiar signos o Pleno
invalida ese desarrollo y exige generar de nuevo; la barra pasa a cero con
«Sin desarrollo generado». El panel impide aplicar filtros sin apuestas y
explica el siguiente paso.

Los errores de filtros se muestran dentro del panel, sin bloquear las casillas.
Puedes desmarcar cualquier condición o pulsar «Desactivar todos los filtros»;
esto no borra apuestas ni restaura un desarrollo ya filtrado. Para recuperarlo
usa «Recuperar apuestas anteriores».

La revisión de lenguaje abarca las siete secciones. Inicio explica 1/X/2; Crear
distingue apuestas posibles y guardadas; Optimizar explica presupuesto y
condiciones; Análisis separa datos deportivos y elecciones de jugadores;
Escrutinio habla de resultados y premios; Mis Sistemas describe cómo se creó
cada quiniela; Configuración habla de precio, archivos y copias de seguridad.
Identificadores y detalles del historial están en ayuda, no en el flujo habitual.

## Optimizar — recorrido automático 0.1.7

1. Mueve la **barra propia de Optimizar**: 0 pone más condiciones y 10 conserva
   el máximo de apuestas originales. Las condiciones, apuestas y coste se
   actualizan automáticamente. La barra de Crear es independiente.
2. Si quieres, ajusta una condición a mano: el resultado también se recalcula.
   «Quitar todas las condiciones» recupera las apuestas originales.
3. **Al final**, introduce el presupuesto y pulsa **Aplicar presupuesto**.
   Se seleccionan únicamente apuestas del resultado ya filtrado hasta ese importe.

Se eliminan «Usar los ajustes de este nivel» y el botón de aplicar condiciones.
La pantalla muestra nivel, resultado, condiciones y presupuesto sin repetir
explicaciones. No es un reductor con garantías ni una predicción de IA.

El cálculo usa un trabajador cancelable y una pausa corta para agrupar cambios;
solo se acepta la última petición de la quiniela vigente. Las versiones se guardan
al terminar. Plenos, copias y precio congelado se conservan. Si ninguna apuesta
cumple las condiciones, se muestra 0 apuestas / 0 €; puedes ampliar el nivel
para recuperarlas. Un resultado vacío no se exporta como si fuera la base.
El presupuesto permanece deshabilitado mientras se recalcula o si no quedan
apuestas. Las condiciones guardadas se recuperan al abrir de nuevo la app.

## Aciertos, Pleno múltiple y Reducidas — 0.1.8

- **Aciertos**: tabla de los 15 partidos con marcador, resultado, tu signo y
  acierto/fallo. Selecciona una apuesta en la tabla inferior para compararla
  partido a partido. Aciertos y fallos en partidos en juego pueden cambiar.
- El marcador se consulta al abrir la sección y cada 60 s mientras está visible;
  puedes elegir 30 o 120 s o desactivar la actualización. Una petición cada vez.
  Los errores no abren ventanas: se conserva el último marcador y se reintenta.
  Si cierras con una petición en curso, termina/cancela con el timeout de red.
- La jornada y los equipos se validan. No se utiliza otra jornada como sustituta.
  Un proveedor sin datos para esa jornada no permite anunciar resultados en vivo.
- La demo usa **Introducir resultados a mano**: elige signos en los 14 partidos
  y goles del Pleno; la comparación se actualiza sola. «Definitivos» requiere
  todos los resultados. El Pleno solo se confirma con 14 aciertos y goles finales.
- En el boleto puedes marcar varios 0/1/2/M por equipo. Se juegan todas las parejas:
  local 0/1 y visitante 2/M produce 02, 0M, 12 y 1M. Una columna se convierte en
  4 apuestas; con precio de referencia de 75 céntimos, cuesta 3 €. Cambiar el
  Pleno requiere generar de nuevo. Se conserva la selección al cerrar.
- Generación, TXT/JSON, exportación directa y límites cuentan también las parejas
  del Pleno. Optimizar y las reducciones conservan Plenos y cantidades exactas.

**Reducidas**, opcional: activa la casilla, elige una de las seis tablas y marca
los partidos a reducir. Se propone una selección compatible y puedes cambiarla.
La app muestra apuestas/coste antes de crear una copia; la original sigue en
Mis Sistemas. Los otros dobles/triples se desarrollan al directo. Los filtros de
Optimizar no se aplican a esta copia desde el boleto. Límite de 100.000 apuestas.

### Procedencia y verificación de las tablas

El [artículo SELAE solicitado](https://www.loteriasyapuestas.es/es/paginas-informativas/quinielas-reducidas-maximiza-tus-posibilidades)
enlaza [BOE-A-2009-12204](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2009-12204).
Esta resolución ha dejado de estar vigente. Se usan sus matrices numéricas como
catálogo fechado del artículo, no como certificación de formato actual ni sellado.
Se observaron diferencias con el [PDF que actualmente enlaza normativa SELAE](https://www.loteriasyapuestas.es/f/loterias/documentos/normativa/Normativa%20de%20los%20juegos/Normas_de_la_Quiniela_y_Elige8_Octubre_2019.pdf);
no se anuncia equivalencia exacta con todas sus matrices. Este PDF permite varias
casillas de goles por equipo en el Pleno (18.2) y explica su multiplicación.

| Tabla del artículo | Dobles / triples seleccionados | Columnas de tabla | Mínimo de aciertos verificado* |
|---|---|---|---|
| 1 | 0 / 4 | 9 | 13 |
| 2 | 7 / 0 | 16 | 13 |
| 3 | 3 / 3 | 24 | 13 |
| 4 | 6 / 2 | 64 | 13 |
| 5 | 0 / 8 | 81 | 12 |
| 6 | 11 / 0 | 132 | 9 |

*Comprobación exhaustiva local sobre resultados contenidos en todos los signos
del boleto; fuera de esa base no se afirma garantía. No garantiza el Pleno ni
un premio monetario. La tabla 6 transcrita del BOE enlazado ofrece mínimo 9 en
esta verificación: no se le atribuye una garantía mayor. Los partidos adicionales
al directo y los Plenos multiplican las columnas y el coste.

La app prepara archivos locales: no valida, sella, envía ni paga apuestas.
