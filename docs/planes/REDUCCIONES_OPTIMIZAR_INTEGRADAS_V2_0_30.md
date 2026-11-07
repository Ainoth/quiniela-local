# Reducciones integradas y Optimizar · v2.0.30

## Objetivo

Garantizar que Optimizar trabaje siempre con las apuestas admitidas por todas
las reducciones activas, verificar las figuras FSSeguidos/Distancias en el
mismo flujo combinado, mantener visible la navegación de Reducciones y ordenar
la presentación de sus controles históricos.

## Subtareas

- [x] Eliminar el filtro rápido duplicado de candidatas en Optimizar; conservar
  los límites y el presupuesto del optimizador, aplicados después de Reducciones.
- [x] Usar siempre el conjunto filtrado al optimizar y probar varias pestañas
  activas simultáneamente.
- [x] Comprobar la matemática de las figuras exactas de rachas e interrupciones
  contra ejemplos del manual WIN1X2 y corregir errores reproducibles.
- [x] Mantener fijas las pestañas de Reducciones y desplazar solo el contenido
  de la subpestaña activa.
- [x] Sustituir la cuadrícula de temporadas por una lista vertical compacta con
  búsqueda y presets, preservando casillas y selección persistente.
- [x] Retirar la línea inferior redundante y mostrar estados/progreso en la
  franja naranja existente.
- [x] Homogeneizar estados seleccionados de casillas a azul en Reducciones.
- [x] Actualizar changelog y trazabilidad, ejecutar pruebas focalizadas.

## Criterios de aceptación

1. Una apuesta debe superar todas las reducciones activas (intersección AND).
2. Optimizar no incorpora candidatas descartadas ni ofrece un segundo filtro
   para preparar apuestas.
3. FSSeguidos y Distancias aceptan figuras calculadas por rachas máximas y
   transiciones consecutivas respectivamente, y se combinan con Cuenta.
4. La barra de pestañas queda visible al desplazarse por una reducción larga.
5. Las temporadas conservan casillas, búsqueda y selección por lotes con una
   distribución vertical legible.
6. Los mensajes de estado no duplican una segunda barra bajo la franja naranja.

## Referencias contrastadas

- [Manual WIN1X2 2006–07](https://www.win1x2.com/manual/win1x2.pdf): define
  figuras como rachas máximas ordenadas (ejemplos `3-2-1-1`) y las
  interrupciones sobre las trece transiciones entre los catorce partidos.
- [Megaquin: Distancias](https://www.megaquin1x2.com/condiciones/distancias.php):
  usa el mismo nombre para otro reductor, basado en la distancia entre apuestas
  seleccionadas. No se adopta esa definición para esta pestaña del proyecto;
  el comportamiento propio queda descrito en `docs/03_REGLAS_Y_FORMULAS.md`.

Las fórmulas del proyecto permanecen definidas por sus reglas y ejemplos de
referencia; no se afirma equivalencia interna con software de terceros.
