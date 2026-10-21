# Plan · Generadores gráficos en Crear quiniela → Normal

## Objetivo

Integrar en la pestaña Normal (sin crear aplicación ni rediseñar el resto) la matriz de porcentajes y rellenado probabilístico de la base, más el generador tabular de acciones, terminaciones y combinación de columnas. Mantener separadas las probabilidades deportivas, la popularidad y las ponderaciones estadísticas.

## Inspección y límites confirmados

- UI: `MainWindow.build_builder()` en `src/quiniela_ai_studio/ui/window.py`; el boleto fijo está en la columna izquierda y Normal en un panel derecho.
- Datos disponibles: instantáneas por jornada `sport` (mercado publicado) y `public` (porcentajes jugados); no hay tablas de clasificación, últimos cinco resultados, enfrentamientos históricos ni probabilidades WIN1X2/LAE.
- Persistencia: ajustes SQLite por clave y auditoría ya disponibles en `Repository`.
- El motor actual limita generación materializada a 100.000; la tabla de acciones necesita streaming para no alterar ese límite ni retener universos enormes.
- No se encontraron ficheros X2_2003/Covadonga en el repositorio ni formatos documentados para esos nombres. No se atribuirá compatibilidad a formatos propietarios.

## Fases

Estado: implementado v1.0.8 en la pestaña Normal, sujeto a las limitaciones de
fuentes descritas arriba; los feeds de clasificación, forma, historial, LAE,
Betfair independiente y WIN1X2 aún no están integrados.

1. Dominio puro: validar/normalizar snapshots abiertos CSV/TXT/JSON, seleccionar triples/dobles por pérdida exacta de masa, ranking exacto top-K por log-probabilidad, terminaciones 1-indexadas, rangos inclusivos, unión/intersección y conteo. Probar contra enumeración exhaustiva.
2. Persistencia y auditoría: perfiles de porcentaje por jornada y filas de acciones; guardar fuentes con identidad/procedencia; commit solo tras validación.
3. UI Base Automática: tabla editable de 14×3, tres ponderaciones con disponibilidad real, recálculo explícito, contadores T/D, +/−, guardar/cargar, rellenar base editable y mantener bloqueos.
4. UI Acciones: tabla compacta de cinco filas ampliables, tipos funcionales, terminaciones 0–9 toggles pequeños, fuente por fila, unión/intersección, explicación y gestor de fuentes.
5. Trabajo en segundo plano y salida: generación top-K cancelable con progreso, exportación atómica CSV/TXT/JSON, integración como importación de columnas al sistema existente; aviso antes de salida grande.
6. Docs, matriz de trazabilidad, changelog, suite completa, lint, smoke y revisión Qt a tamaños usuales.

## Criterios de aceptación

- En base: exactamente T triples, D dobles y 14−T−D fijos; rechazo de T+D>14; selección basada en pérdida de probabilidad (triple→doble→fijo), deterministicamente; cambios visibles en el boleto, sin generar sus columnas.
- Top-K: mismo resultado ordenado que enumeración exhaustiva para universos pequeños; desempate léxico `1 < X < 2`; rango Desde/Hasta inclusivo; posiciones y terminaciones desde 1.
- Combinación: concatenación preserva multiplicidad; unión opera por los 14 signos; intersección exacta entre acciones habilitadas.
- Fuentes: snapshots existentes y CSV/TXT/JSON abiertos con jornada/partido/identidad validables; no inventar LAE, clasificación, forma, historial o fuentes no disponibles.
- Persistencia por jornada, importación sin pérdida previa al fallar, logs explicables y UI Qt sin bloquear.

## Decisiones pendientes por datos externos

Los tres factores Clasificación, 5 últimas jornadas e Historial solo se activan cuando existe una fuente estructurada, fechada e identificada para los partidos de la jornada. Mientras tanto se muestran como no disponibles; el usuario puede editar/reemplazar los porcentajes manualmente. `sport` no se rebautiza como LAE y `public` no se interpreta como probabilidad deportiva.
