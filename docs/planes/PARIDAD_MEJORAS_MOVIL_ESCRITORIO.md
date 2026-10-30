# Mejoras recientes de móvil en escritorio

## Objetivo

Trasladar a Quiniela AI Studio de escritorio las últimas mejoras de uso
solicitadas para móvil, adaptadas a la composición Qt ya existente.

## Alcance y aceptación

- Las cantidades de dobles y triples se ajustan con barras progresivas y
  botones Auto/Manual independientes. Un botón no modifica el modo del otro.
- Auto estima la cantidad a partir de las temporadas seleccionadas, los
  resultados finales disponibles y los porcentajes actuales de la jornada.
  El importe no interviene en la creación de la base.
- La automatización usa un objetivo de cobertura descriptivo del histórico,
  con límite técnico interno derivado del límite de generación y el Pleno; no
  pide al usuario un máximo de columnas.
- El número de partido ocupa una columna estrecha alineada a la izquierda;
  los porcentajes se muestran sin corchetes con letra algo mayor y filas más
  compactas.
- La acción principal de generación queda al final del área Normal y el
  resumen inferior existente permanece como única línea de coste y apuestas.

## Validación

Pruebas Qt sobre selección manual/automática, independencia de los dos modos,
recomendación con muestra histórica, límite de columnas, persistencia y orden
de controles; suite completa, `ruff` y comprobación visual en Linux.
