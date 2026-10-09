# 12 · Matriz de trazabilidad de requisitos

Esta tabla está generada inicialmente a partir de `01_ESPECIFICACION_FUNCIONAL.md`. Codex debe convertir los rangos de versión en una **versión precisa** al implementar cada requisito y sustituir PENDIENTE por IMPLEMENTADO solo tras superar las pruebas pertinentes.

| Requisito | Entrega prevista | Estado inicial | Descripción |
|---|---|---|---|
| `RF-JOR-001` | v0.1/v0.5 | PARCIAL | Crear, abrir, modificar y archivar temporadas, jornadas y sus 15 partidos. |
| `RF-JOR-002` | v0.1/v0.5 | PARCIAL | Validar orden 1..14 y partido 15; detectar duplicados y entradas incompletas. |
| `RF-JOR-003` | v0.1/v0.5 | PENDIENTE | Registrar equipos, fecha/hora con zona horaria, competición y estado del evento. |
| `RF-JOR-004` | v0.1/v0.5 | PENDIENTE | Capturar resultados manualmente y cargarlos desde proveedor autorizado, distinguiendo provisionales/finales. |
| `RF-JOR-005` | v0.1/v0.5 | PARCIAL | Guardar instantáneas de datos con proveedor, hora de captura, versión y calidad. |
| `RF-JOR-006` | v0.1/v0.5 | PENDIENTE | Historial de temporadas, jornadas, recaudación, premios y acertantes cuando estén publicados. |
| `RF-JOR-007` | v0.1/v0.5 | PARCIAL | Política de caché, reintentos, actualización explícita y modo offline. |
| `RF-JOR-008` | v0.1/v0.5 | PARCIAL | Comparación y conciliación entre proveedores; nunca sobrescribir un dato manual sin informar. |
| `RF-QUI-001` | v0.1/v0.8 | PENDIENTE | Editor de 14 casillas con subconjuntos no vacíos de `{1,X,2}`: fijo, doble, triple. |
| `RF-QUI-002` | v0.1/v0.8 | PENDIENTE | Selector de Pleno al 15 con marcadores `{0,1,2,M}` por equipo; permitir múltiples resultados o uno fijo. |
| `RF-QUI-003` | v0.1/v0.8 | PENDIENTE | Contador de fijos, dobles, triples y columnas, multiplicando por selecciones del Pleno al 15. |
| `RF-QUI-004` | v0.1/v0.8 | PENDIENTE | Precio configurable/versionado, presupuesto y coste total en céntimos. |
| `RF-QUI-005` | v0.1/v0.8 | PENDIENTE | Bloquear signos, deshacer/rehacer, duplicar sistema, plantillas, iniciar, vaciar y completar. |
| `RF-QUI-006` | v0.1/v0.8 | PENDIENTE | Elegir jornadas, asociar sistemas a jornada y registrar objetivo/estrategia. |
| `RF-QUI-007` | v0.1/v0.8 | PENDIENTE | Sistemas mixtos: combinar columnas concretas, bloques múltiples y reducciones sin duplicación involuntaria. |
| `RF-QUI-008` | v0.1/v0.8 | PENDIENTE | Construcción manual desde fichero existente y edición segura de combinaciones importadas. |
| `RF-QUI-009` | v0.1/v0.8 | PENDIENTE | Preparar modelo de Elige8 como modalidad independiente y opcional; requisitos de validación específicos en versión posterior. |
| `RF-GEN-001` | v0.4/v0.6 | PENDIENTE | Generar apuestas al azar con semilla reproducible y distribución configurable. |
| `RF-GEN-002` | v0.4/v0.6 | PENDIENTE | Generador ponderado por probabilidades por partido y Pleno al 15. |
| `RF-GEN-003` | v0.4/v0.6 | PENDIENTE | Generar signos, dobles y triples dada una cantidad o distribución de riesgo. |
| `RF-GEN-004` | v0.4/v0.6 | PENDIENTE | Sugerir propuestas dentro de presupuesto; no sobrepasarlo sin confirmación. |
| `RF-GEN-005` | v0.4/v0.6 | PENDIENTE | Respetar signos fijos y bloqueos manuales. |
| `RF-GEN-006` | v0.4/v0.6 | PENDIENTE | Generar columnas a distancia de Hamming especificada de una o varias referencias. |
| `RF-GEN-007` | v0.4/v0.6 | PENDIENTE | Generar N apuestas únicas o explicar si la demanda es imposible. |
| `RF-GEN-008` | v0.4/v0.6 | PENDIENTE | Asistente con dos modos: automático y experto, explicando reglas y fuentes usadas. |
| `RF-GEN-009` | v0.4/v0.6 | PENDIENTE | Predicción de signo y Pleno al 15 desde modelos registrados y evaluados, con fallback honesto (sin predicción) si faltan datos. |
| `RF-GEN-010` | v0.4/v0.6 | PENDIENTE | Estabilización de porcentajes: aproximar una distribución objetivo de signos en las columnas generadas, ciclos reproducibles y error final informado. |
| `RF-PRO-001` | v0.4 | PENDIENTE | Cargar P(1), P(X), P(2) por partido, con validación suma=1 dentro de tolerancia. |
| `RF-PRO-002` | v0.4 | PARCIAL | Capturar separadamente porcentajes de selección pública de SELAE y otras fuentes, con fecha y procedencia. |
| `RF-PRO-003` | v0.4 | PENDIENTE | Mostrar diferencias porcentuales entre probabilidad estimada y proporción jugada. |
| `RF-PRO-004` | v0.4 | PENDIENTE | Guardar distribución `4×4` para Pleno al 15 y verificar que suma 1. |
| `RF-PRO-005` | v0.4 | PENDIENTE | Ordenar columnas por probabilidad estimada; etiquetar supuesto de independencia cuando se use. |
| `RF-PRO-006` | v0.4 | PENDIENTE | Redondear SOLO para representación; no alterar cálculo interno. |
| `RF-PRO-007` | v0.4 | PENDIENTE | Columnas Base y sugerencias «más 1 / más X / más 2» ordenando probabilidades de signos. |
| `RF-PRO-008` | v0.4 | PARCIAL | Mostrar valores de fuente, instante y advertencia de datos incompletos u obsoletos. |
| `RF-FIL-001` | v0.2/v0.7 | PARCIAL | Motor de filtros composable, registro, validación, ejecutar por lotes y reportar descartes. |
| `RF-FIL-002` | v0.2/v0.7 | PARCIAL | Filtros de recuentos y secuencias (1, X, 2, variantes, signos seguidos, interrupciones). |
| `RF-FIL-003` | v0.2/v0.7 | PENDIENTE | Filtros de patrones: parejas, tríos, cuartetos, quintetos, sextetos, septetos y por partido. |
| `RF-FIL-004` | v0.2/v0.7 | PENDIENTE | Filtros de columnas base (CB), sumas de CB, CB relacionadas y grupos de CB. |
| `RF-FIL-005` | v0.2/v0.7 | PARCIAL | Filtros de diferencias, coincidencias, rangos, figuras X-2, dibujos de variantes. |
| `RF-FIL-006` | v0.2/v0.7 | PENDIENTE | Filtro de valoraciones (suma, productos/logaritmos con gestión numérica segura). |
| `RF-FIL-007` | v0.2/v0.7 | PENDIENTE | Filtro `IF THEN`, condiciones vinculadas y grupos generales. |
| `RF-FIL-008` | v0.2/v0.7 | PENDIENTE | Reservas: tolerancia controlada al incumplimiento de condiciones con reglas explícitas. |
| `RF-FIL-009` | v0.2/v0.7 | PENDIENTE | Activación independiente, orden, presets, clonación, import/export versionado de condiciones. |
| `RF-FIL-010` | v0.2/v0.7 | PENDIENTE | Estudio previo de cada filtro: límites posibles, distribución, efecto y recomendación **sin prometer resultados**. |
| `RF-FIL-011` | v0.2/v0.7 | PENDIENTE | Informe de fallo: qué condición descartó una columna/resultado ganador y por qué. |
| `RF-FIL-012` | v0.2/v0.7 | PENDIENTE | Guardar opcionalmente descartes por filtro, en modo streaming. |
| `RF-FIL-013` | v0.2/v0.7 | PENDIENTE | Filtros de rentabilidad y probabilidad solo cuando existan datos válidos. |
| `RF-RED-001` | v0.3/v0.7 | PENDIENTE | Reducir sobre conjunto base ya filtrado con presupuesto o número objetivo de columnas. |
| `RF-RED-002` | v0.3/v0.7 | PENDIENTE | Modos de optimización: cobertura, probabilidad o combinación ponderada; explicar los compromisos. |
| `RF-RED-003` | v0.3/v0.7 | PENDIENTE | Objetivos de 14 a 9 aciertos y objetivos de N premios si son matemáticamente interpretables. |
| `RF-RED-004` | v0.3/v0.7 | PENDIENTE | Generadores propios: voraz (greedy), mejora local, búsqueda con semillas y optimizadores opcionales. |
| `RF-RED-005` | v0.3/v0.7 | PENDIENTE | Separar apuestas candidatas internas (del sistema base) de candidatas externas (si se autoriza dominio mayor). |
| `RF-RED-006` | v0.3/v0.7 | PENDIENTE | Ajustar número exacto de columnas solo si el objetivo es factible; indicar limitaciones. |
| `RF-RED-007` | v0.3/v0.7 | PENDIENTE | Progreso, pausa segura, cancelación, recuperación de mejor solución y parámetros. |
| `RF-RED-008` | v0.3/v0.7 | PENDIENTE | Comparar porcentajes y cobertura antes/después; exportar informe verificable. |
| `RF-RED-009` | v0.3/v0.7 | PENDIENTE | No llamar REDWIN ni garantizar compatibilidad matemática sin especificaciones independientes. |
| `RF-GAR-001` | v0.3 | PENDIENTE | Medir cobertura de cada umbral 14..0 sobre dominio de resultados definido. |
| `RF-GAR-002` | v0.3 | PENDIENTE | Distinguir garantía absoluta condicional, porcentaje de escenarios cubiertos y probabilidad modelada de cobertura. |
| `RF-GAR-003` | v0.3 | PENDIENTE | Número mínimo de premios de cada categoría, cuando sea verificable para el dominio elegido. |
| `RF-GAR-004` | v0.3 | PENDIENTE | Evaluar resultados del Pleno al 15 por separado, vinculado al acierto de los primeros 14. |
| `RF-GAR-005` | v0.3 | PENDIENTE | Pruebas exhaustivas en dominios pequeños, validación externa/cotas en dominios grandes. |
| `RF-GAR-006` | v0.3 | PENDIENTE | Subir cobertura con heurística y comparar coste adicional. |
| `RF-REN-001` | v0.6 | PENDIENTE | Coeficiente original y documentado, sin afirmar equivalencia al CR propietario de Quiniwin. |
| `RF-REN-002` | v0.6 | PENDIENTE | Calcular probabilidad modelada, coste, premio estimado e incertidumbre individual de apuestas. |
| `RF-REN-003` | v0.6 | PENDIENTE | Estimar acertantes desde patrones públicos, recaudación y reglas versionadas; indicar hipótesis. |
| `RF-REN-004` | v0.6 | PENDIENTE | Valorar apuestas mediante beneficio esperado, riesgo y diversificación. |
| `RF-REN-005` | v0.6 | PENDIENTE | Ranking por rentabilidad / probabilidad; visualización por colores con leyenda accesible. |
| `RF-REN-006` | v0.6 | PENDIENTE | Estimar posibles premios con 3 o menos encuentros pendientes, sin mezclarlos con premios oficiales. |
| `RF-REN-007` | v0.6 | PENDIENTE | Calculadora de premios históricos y definitivos con datos oficiales validados. |
| `RF-REN-008` | v0.6 | PENDIENTE | Comparativa real vs simulada: coste, premios, beneficio neto y retorno acumulado. |
| `RF-ESC-001` | v0.1/v0.5 | PARCIAL | Escrutinio parcial y final de sistemas locales y ficheros externos. |
| `RF-ESC-002` | v0.1/v0.5 | PENDIENTE | Categorías de aciertos 14,13,12,11,10 y Pleno al 15 según reglas vigentes. |
| `RF-ESC-003` | v0.1/v0.5 | PENDIENTE | No conceder Pleno al 15 por acertar solo el marcador si faltan los 14. |
| `RF-ESC-004` | v0.1/v0.5 | PARCIAL | Filtrar solo partidos finalizados; mostrar intervalo de aciertos potenciales en parciales. |
| `RF-ESC-005` | v0.1/v0.5 | PENDIENTE | Procesar múltiples ficheros con progreso, cancelar y ranking. |
| `RF-ESC-006` | v0.1/v0.5 | PENDIENTE | Columnas ganadoras aleatorias solo en simulación, claramente identificada. |
| `RF-ESC-007` | v0.1/v0.5 | PENDIENTE | Informe detallado / resumido y desglose de apuestas sin premio. |
| `RF-ESC-008` | v0.1/v0.5 | PENDIENTE | Escrutinio independiente que permita cargar TXT/JSON propios y los formatos externos oficialmente documentados. |
| `RF-SIM-001` | v0.6 | PENDIENTE | Simular escenarios desde probabilidades explícitas, con semilla reproducible. |
| `RF-SIM-002` | v0.6 | PENDIENTE | Simulaciones uniformes y ponderadas; comparación con enumeración exacta en dominios pequeños. |
| `RF-SIM-003` | v0.6 | PENDIENTE | Distribución de aciertos, cobertura, volatilidad de premios estimados y resultados por estrategia. |
| `RF-SIM-004` | v0.6 | PENDIENTE | Comparar 2 o más sistemas con exactamente el mismo conjunto de resultados simulados. |
| `RF-SIM-005` | v0.6 | PENDIENTE | Backtesting cronológico sin usar datos posteriores a cada cierre de jornada. |
| `RF-SIM-006` | v0.6 | PENDIENTE | Reportar intervalos de confianza y limitaciones del modelo. |
| `RF-EST-001` | v0.4/v0.7 | PENDIENTE | Frecuencias y radiografías 1/X/2 de sistemas y columnas ganadoras. |
| `RF-EST-002` | v0.4/v0.7 | PENDIENTE | Análisis de patrones de tamaño 2 a 7, solapados o no, definidos matemáticamente. |
| `RF-EST-003` | v0.4/v0.7 | PENDIENTE | Figuras, dibujos, transiciones, interrupciones y secuencias por subconjuntos de partidos. |
| `RF-EST-004` | v0.4/v0.7 | PENDIENTE | Distancias de Hamming y distribución entre columnas. |
| `RF-EST-005` | v0.4/v0.7 | PENDIENTE | Gráficas por jornadas/temporadas, con periodo aplicable a todos los cálculos. |
| `RF-EST-006` | v0.4/v0.7 | PENDIENTE | Medir efectos de cada filtro y estudiar la conservación de resultados históricos. |
| `RF-ARC-001` | v0.1/v0.8 | PARCIAL | Import/export nativo versionado a JSON y texto simple, sin pérdida del Pleno al 15. |
| `RF-ARC-002` | v0.1/v0.8 | PENDIENTE | Soporte XML interno y compatibilidad externa mediante adaptadores de formato. |
| `RF-ARC-003` | v0.1/v0.8 | PENDIENTE | Unir, intersecar, restar, deduplicar y ordenar grandes conjuntos. |
| `RF-ARC-004` | v0.1/v0.8 | PENDIENTE | Dividir por número, tamaño y Pleno al 15; conservar manifiestos para recomponer. |
| `RF-ARC-005` | v0.1/v0.8 | PENDIENTE | Compactar/descompactar definiciones de fijos/dobles/triples cuando sea representable, sin inventar equivalencias. |
| `RF-ARC-006` | v0.1/v0.8 | PENDIENTE | Intercambiar signos/posiciones, generar sistemas aleatorios y por distancias. |
| `RF-ARC-007` | v0.1/v0.8 | PENDIENTE | Inferir **aproximadamente** restricciones de una combinación importada, indicando error. |
| `RF-ARC-008` | v0.1/v0.8 | PENDIENTE | Adaptadores AD243, ASD(JSON), ASCII heredado y `.NUM` solo después de reunir especificaciones y fixtures legales. |
| `RF-BOL-001` | v0.5/v0.9 | PENDIENTE | Mostrar apuestas y preparar PDF legible, con coste, jornada, plenos y total. |
| `RF-BOL-002` | v0.5/v0.9 | PENDIENTE | Diagramación de varias apuestas por página y salida de prueba. |
| `RF-BOL-003` | v0.5/v0.9 | PENDIENTE | QR de uso interno (para recuperar proyectos) separado de QR oficial de validación. |
| `RF-BOL-004` | v0.5/v0.9 | PENDIENTE | QR/ASD oficiales condicionados a formato publicado/permiso y pruebas de conformidad. |
| `RF-BOL-005` | v0.5/v0.9 | PENDIENTE | Envío a portales solo con integración autorizada, confirmación manual y recibo auditable. |
| `RF-BOL-006` | v0.5/v0.9 | PENDIENTE | No declarar «apuesta registrada» si únicamente se generó PDF o QR. |
| `RF-PEN-001` | v0.8 | PENDIENTE | Registrar peñas, integrantes, aportes y porcentajes de participación. |
| `RF-PEN-002` | v0.8 | PENDIENTE | Asociar apuestas/sistemas a peña y jornada. |
| `RF-PEN-003` | v0.8 | PENDIENTE | Calcular participaciones y repartos con aritmética decimal exacta y reglas explícitas. |
| `RF-PEN-004` | v0.8 | PENDIENTE | Informes de participantes, aportaciones y resultados; PDF imprimible. |
| `RF-PEN-005` | v0.8 | PENDIENTE | No gestionar cobros reales ni facturación regulada sin fase separada. |
| `RF-AUD-001` | v0.1/v0.9 | PARCIAL | Bitácora de cada acción: origen de datos, filtros, reducción, semilla, costes y resultados. |
| `RF-AUD-002` | v0.1/v0.9 | PARCIAL | Historial comparativo y posibilidad de reproducir un sistema desde parámetros versionados. |
| `RF-AUD-003` | v0.1/v0.9 | PENDIENTE | Informes de quiniela, filtros, apuestas eliminadas, garantías, escrutinio y desempeño. |
| `RF-AUD-004` | v0.1/v0.9 | PENDIENTE | Panel inicial: jornada vigente, actividad reciente y accesos útiles, sin saturación. |
| `RF-AUD-005` | v0.1/v0.9 | PENDIENTE | Preferencias de idioma, accesibilidad, tema, fuentes y límites de presupuesto. |
| `RF-AUD-006` | v0.1/v0.9 | PENDIENTE | Copia de seguridad, exportación de datos y restauración con confirmación. |
| `RF-AUD-007` | v0.1/v0.9 | PARCIAL | Diagnóstico entendible de importaciones fallidas, dependencia ausente y errores de datos. |
| `RF-AUD-008` | v0.1/v0.9 | PARCIAL | Instalación portable sin rutas de usuario incrustadas; registro de versión de datos y migraciones. |

**Requisitos RF inventariados:** 118.

### Seguimiento obligatorio

Para cada versión indicar: requisito → módulos/clases → tests (identificadores `T-*`) → evidencia de verificación → estado. Las funcionalidades condicionadas a formato externo permanecen `BLOQUEADAS: falta norma/proveedor` hasta contar con prueba válida.

### Relación rápida de dependencias

| Módulo | Dependencias técnicas mínimas |
|---|---|
| Jornadas/constructor | `GameRuleset`, `Draw`, `Match`, `Selection` |
| Filtros | generador de `Column` + `Filter` + conjuntos de CB |
| Reducción | filtros, definición Ω, evaluador de distancias, verificador de garantías |
| Estadística | columnas, historial, vistas/agrupaciones |
| IA | historial fechado, probabilidad, evaluador temporal, registro de modelos |
| Rentabilidad | probabilidades + regla de premios + estimación de acertantes |
| Escrutinio | columnas + resultados + reglas de categorías |
| Exportación oficial | formato documentado + autorización + pruebas conformidad |
| Peñas | proyectos, costes/premios y datos personales privados |

## Evidencias del escritorio integrado v0.1.1

Los requisitos marcados PARCIAL se cubren solo en el alcance descrito en
[STUDIO_FUSION.md](STUDIO_FUSION.md); el contrato completo de cada fila sigue
siendo la referencia. Evidencias: `tests/studio/test_integration.py` (identidad,
caché, rollback, copias SQLite y migración), `test_filters_integration.py`
(oráculo exhaustivo, cantidades y origen) y `test_ui.py` (flujo Qt y cierre).
El plan está en [planes/FUSION_ESCRITORIO.md](planes/FUSION_ESCRITORIO.md).

Se mantienen pendientes el cierre autorizado, automatismos de red, formatos
externos, filtros expertos y la paridad completa. Los fixtures son sintéticos;
la comprobación manual de proveedores reales no añade datos personales al repo.
