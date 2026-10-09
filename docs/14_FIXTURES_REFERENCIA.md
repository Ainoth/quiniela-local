# 14 · Datos de prueba de referencia para Codex

Los ficheros de `fixtures/` son **sintéticos** y no corresponden a jornadas o cuotas reales.

## `seleccion_demo_v1.json`

Tiene una doble (`1X`) y un triple (`1X2`) entre los 14 encuentros; resto fijos. Tiene dos marcadores de P15 explícitos. Por tanto, genera `2×3×2=12` columnas únicas. Con `reglas_demo_v1.json` a 75 céntimos por columna, el coste total demo es `12×75=900` céntimos. Este resultado constituye un oráculo de aceptación del contador, exportador y motor de coste.

## `resultados_demo_v1.json`

Contiene resultados sintéticos completos. La combinación que elija el segundo signo del partido 2 (X), el primer signo del partido 5 (1) y marcador `(0,1)` coincide con los 14 resultados y el P15: tiene 14 aciertos más Pleno al 15. La misma columna con marcador `(1,1)` debe tener 14 aciertos, pero **sin** Pleno al 15. La columna que elija 1 en partido 2 tiene un acierto menos.

## Propiedades de ida/vuelta

Un importador debe conservar `draw_id`, `ruleset_id`, 14 máscaras, parejas P15 y precio demo. Un exportador no debe presentar estos datos como oficiales ni emitir supuestos QR de validación. Las fixtures deberán permanecer estables; al cambiar su semántica, crear un fichero versionado nuevo y tests de migración.
