# Plan: modos visuales de Cuenta y Racha

## Decisión de ubicación

Cuenta se amplía in situ: ya cuenta variantes (X+2), equis y doses mediante
`BasicFilters`, por lo que sus condiciones son el mismo dominio matemático que
la primera pantalla WIN1X2. Racha se amplía in situ: ya calcula la longitud
máxima consecutiva por signo. Cambio conserva su significado propio. No se
crean pestañas paralelas que dupliquen estas condiciones.

## Requisitos y aceptación

- RF-FIL-018: Cuenta ofrece Manual/Azar/Automática exclusivos; selección de
  cantidades V/X/2 conectada al filtro real y conserva valores al cambiar modo.
- RF-FIL-019: Racha ofrece Manual/Azar/Automática exclusivos; límites y figuras
  usan rachas máximas exactas y conteos de rachas máximas no solapadas.
- RF-UX-010: cuadros activables blancos/verdes, sin ticks, con estado accesible;
  la activación por pestaña excluye sus condiciones sin ocultar ni borrar ajustes.
- El azar es reproducible con semilla y se valida sobre las columnas disponibles.
- Automática solo consume jornadas históricas con resultados reales. Si el
  repositorio no contiene temporadas finalizadas, informa que faltan datos y no
  inventa estadísticas.
- Importación explícita desde CSV o JSON (`season`, `round`, `results14`), con
  validación estricta de los 14 signos, temporadas seleccionables y persistencia
  local. Los archivos marcados como demo se rechazan. El histórico incluido se
  carga automáticamente; `score_01`…`score_15` son campos opcionales validados
  contra los signos cuando se importan.
- El Pleno al 15 queda fuera de todos los conteos y rachas.

## Fases

1. Reutilizar las páginas Cuenta/Racha y añadir selector de método y activación.
2. Añadir reglas puras serializables para cantidades seleccionadas y figuras
   de rachas; mantener compatibilidad con filtros guardados.
3. Añadir cálculo azaroso reproducible sobre el desarrollo actual.
4. Incluir un histórico verificable, auto-cargarlo y enriquecerlo con marcadores
   publicados sin estimar jornadas no disponibles.
5. Pruebas de dominio, UI, persistencia, documentación y suite completa.

## Semántica provisional visible

Una racha es una secuencia máxima contigua del signo o clase indicada. Para V,
X y 2 forman una sola clase. La figura de longitud N cuenta rachas máximas de
longitud exactamente N; no cuenta ventanas solapadas dentro de una racha mayor.
Es semántica original/provisional mientras no se verifique una definición
normativa del formato clásico.
