# SSeguidos · v1.0.18

## Objetivo

RF-UX-014: rehacer SSeguidos para que solo muestre el método **Automática**,
con una distribución densa inspirada en WIN1X2, y corregir la pérdida de los
controles heredados que también impedía iniciar la vista Cuenta.

## Decisiones de interfaz

- SSeguidos es una única subpestaña **Automática**; Manual y Azar ya no se
  ofrecen como páginas visibles. Cuenta conserva sus páginas Manual, Azar y
  Automática.
- Temporadas, riesgo y cálculo quedan en la franja superior. El selector de
  temporadas y la zona de recomendación ocupan menos alto y ancho.
- Los paneles `1`, `X`, `2` y `V` se muestran juntos. Cada uno contiene el
  intervalo mínimo/máximo, las frecuencias empíricas dentro de cuadrados
  blancos/verdes y su tabla desplazable de figuras exactas.
- La tabla de figuras sigue usando la semántica existente: cuenta rachas
  máximas exactas sin solapamiento. El Pleno al 15 queda fuera.
- No se crea otro reductor. SSeguidos conserva el identificador de Racha y sus
  datos persistidos; la subpestaña global continúa desactivada por defecto.

## Corrección Qt

Los editores antiguos de racha se mantienen ocultos para que la restauración de
configuraciones guardadas pueda leerlos. Ahora viven ocultos bajo el panel
SSeguidos, no en la página Manual que se retiró. Así Qt no destruye
sus `QSpinBox` al liberar una página temporal, y la matriz de Cuenta queda como
un componente separado dentro de su propio panel.

La matriz de Cuenta se coloca dentro de la página del método seleccionado; al
cambiar entre Manual, Azar y Automática se traslada la misma matriz. Así queda
debajo de los controles y no al final del espacio vertical reservado a las
pestañas.

## Aceptación y pruebas

- Cuenta conserva sus tres métodos, valores históricos y filtro funcional.
- SSeguidos muestra exactamente una subpestaña, **Automática**.
- Los cuatro paneles son estrechos y permanecen dentro de la página automática.
- Las frecuencias se actualizan al cambiar temporadas; Calcular utiliza los
  perfiles conjuntos históricos y produce el mismo filtro Racha persistido.
- Activar/desactivar SSeguidos incluye/excluye sus reglas sin borrar valores.

Pruebas: `test_count_and_streak_mode_grids_apply_and_outer_squares_preserve_settings`,
`test_sseguidos_automatic_only_compact_panels_filter_and_share_racha_state`,
`test_sseguidos_minmax_choices_follow_current_base` y las pruebas de modo
Automático e histórico de `tests/studio/test_advanced_conditions_ui.py`.

## Límites

La distribución sigue siendo Qt nativo y adapta sus dimensiones al ancho de la
ventana. No se afirma equivalencia interna completa con WIN1X2: sus estadísticas
y reglas continúan definidas por el motor propio documentado en
`docs/planes/VARIANTES_RACHAS.md`.
