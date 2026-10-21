# SSeguidos · v1.0.17

## Decisión de arquitectura

La pestaña interna existente **Racha** ya implementa la misma condición que
describe el manual: longitudes máximas consecutivas de `1`, `X`, `2` y `V`,
modos Manual/Azar/Automática, frecuencias de figuras e histórico real. Crear un
segundo filtro tendría efectos duplicados y dos configuraciones que podrían
contradecirse. Por eso la interfaz la publica como **SSeguidos**, reutilizando
el índice, las reglas y el estado serializado de Racha para conservar los
sistemas guardados.

## Comportamiento

- La activación de la subpestaña permanece apagada por defecto y conserva los
  ajustes al desactivarse.
- En v1.0.17 los modos Manual, Azar y Automática son subpestañas mutuamente
  excluyentes. La interfaz vigente de v1.0.18 muestra únicamente Automática.
- Manual muestra cuatro paneles estrechos (`1`, `X`, `2`, `V`) con activación,
  mínimo, máximo y valores posibles de racha. El intervalo permitido se calcula
  desde los signos fijos/dobles/triples de la base y los valores imposibles se
  desactivan. Los recuentos históricos aparecen
  dentro de cada cuadrado blanco/verde. Cambiar mínimo/máximo selecciona el
  intervalo completo; la cuadrícula puede conservar una selección discontinua.
- Las figuras permiten limitar cuántas veces aparece una racha máxima exacta,
  sin solapar secuencias. `V` agrupa `X` y `2`. El pleno al 15 queda fuera.
- Azar usa una semilla reproducible y valores presentes en las apuestas de
  origen; no inventa frecuencias.
- Automática utiliza solo resultados finales del histórico integrado o
  importado, calcula perfiles conjuntos y muestra tamaño de muestra y cobertura
  descriptiva. No predice el siguiente resultado.

## Verificación

`test_sseguidos_minimum_maximum_panels_filter_and_share_racha_state` y
`test_sseguidos_minmax_choices_follow_current_base` comprueban
la etiqueta, los tres modos, el estado apagado inicial, la selección min/máx,
los límites derivados de la base, el filtrado real, la persistencia y la
compatibilidad con la regla `Racha`.
La suite `tests/studio/test_advanced_conditions_ui.py` cubre además los modos
aleatorio, histórico y la activación global de pestañas.
