# Entrega ejecutable v0.1 — revisión 0.1.5

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
5. En Escrutinio introduce 14 signos; usa `-` para pendientes. Marca definitivos
   solo con resultados completos. El Pleno requiere también 14 para su categoría.
6. Cierra y abre: jornada, sistema, base, selecciones y versiones siguen en SQLite.
7. Configuración → precio por apuesta cambia el precio de sistemas nuevos;
   los ya guardados conservan su coste. Elige8 se reserva como modalidad separada
   y se rechaza si se intenta utilizar en esta versión.
8. Descarga en la cabecera, importación de carpeta/ZIP/XML y copias SQLite antiguas
   conservan el flujo de [la integración v0.1.1](STUDIO_FUSION.md).

El fixture `fixtures/seleccion_demo_v1.json` se importa como JSON de proyecto
sintético: conserva draw_id, reglas y dos parejas de Pleno. Da **12 apuestas / 900
céntimos**. `resultados_demo_v1.json` verifica 14 + Pleno sin premio económico.

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

## Barra progresiva en Optimizar — 0.1.5

La barra 0–10 vuelve a estar visible en Optimizar y sigue disponible en Crear
Quiniela. Las dos muestran el mismo nivel. Moverla propone dobles/triples y
muestra apuestas y coste sin modificar la quiniela. Pulsa «Usar este nivel en
el boleto» para aplicarlo, y después «Generar» para crear las nuevas apuestas.
Respeta bloqueos y el precio guardado. No es una reducción con garantía.
