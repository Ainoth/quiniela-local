# 01 · Especificación funcional completa

**Producto:** Quiniela AI Studio · **Plataformas:** Linux Mint y Windows · **Idioma inicial:** español · **Diseño:** escritorio, local-first y extensible.

## 1. Objetivo y tipos de usuario

El usuario debe poder pasar de «quiero gastar como máximo X euros» a un conjunto de pronósticos, apuestas, costes y explicaciones, y finalmente comprobar aciertos y premios, con acceso opcional a métodos combinatorios expertos. Usuarios: principiante, experto en sistemas/reducidas y administrador de peñas. Evitar dependencia obligatoria de cuentas externas. El software nunca debe presentar una estimación como garantía de premio ni como beneficio seguro.

### Historias principales

- HU-01: como principiante, quiero una jornada lista para revisar, introducir presupuesto y obtener una propuesta explicada.
- HU-02: como usuario manual, quiero marcar fijos, dobles, triples y varias opciones del Pleno al 15.
- HU-03: como experto, quiero construir condiciones complejas, activar filtros y ver su efecto.
- HU-04: como usuario con presupuesto limitado, quiero reducir apuestas y conocer garantías **verificadas**.
- HU-05: como usuario analítico, quiero comparar probabilidades deportivas vs signos jugados y valorar riesgo/retorno.
- HU-06: como usuario que juega, quiero comprobar apuestas con resultados parciales o finales.
- HU-07: como usuario, quiero exportar y recuperar combinaciones sin pérdidas.
- HU-08: como organizador de una peña, quiero gestionar participaciones e informes, sin procesar pagos en v1.

## 2. Estados de funcionalidad

`REQUERIDO`: comportamiento especificado. `PROPUESTO`: algoritmo o UX original. `POR DEFINIR`: no hay definición suficiente para prometer equivalencia. `INTEGRACIÓN CONDICIONADA`: depende de autorización, documentación y pruebas externas.

## 3. Catálogo de requisitos por módulos

### M01 — Jornadas, partidos, fuentes, historial

- **RF-JOR-001** Crear, abrir, modificar y archivar temporadas, jornadas y sus 15 partidos.
- **RF-JOR-002** Validar orden 1..14 y partido 15; detectar duplicados y entradas incompletas.
- **RF-JOR-003** Registrar equipos, fecha/hora con zona horaria, competición y estado del evento.
- **RF-JOR-004** Capturar resultados manualmente y cargarlos desde proveedor autorizado, distinguiendo provisionales/finales.
- **RF-JOR-005** Guardar instantáneas de datos con proveedor, hora de captura, versión y calidad.
- **RF-JOR-006** Historial de temporadas, jornadas, recaudación, premios y acertantes cuando estén publicados.
- **RF-JOR-007** Política de caché, reintentos, actualización explícita y modo offline.
- **RF-JOR-008** Comparación y conciliación entre proveedores; nunca sobrescribir un dato manual sin informar.

### M02 — Constructor de quinielas y sistemas

- **RF-QUI-001** Editor de 14 casillas con subconjuntos no vacíos de `{1,X,2}`: fijo, doble, triple.
- **RF-QUI-002** Selector de Pleno al 15 con marcadores `{0,1,2,M}` por equipo; permitir múltiples resultados o uno fijo.
- **RF-QUI-003** Contador de fijos, dobles, triples y columnas, multiplicando por selecciones del Pleno al 15.
- **RF-QUI-004** Precio configurable/versionado, presupuesto y coste total en céntimos.
- **RF-QUI-005** Bloquear signos, deshacer/rehacer, duplicar sistema, plantillas, iniciar, vaciar y completar.
- **RF-QUI-006** Elegir jornadas, asociar sistemas a jornada y registrar objetivo/estrategia.
- **RF-QUI-007** Sistemas mixtos: combinar columnas concretas, bloques múltiples y reducciones sin duplicación involuntaria.
- **RF-QUI-008** Construcción manual desde fichero existente y edición segura de combinaciones importadas.
- **RF-QUI-009** Preparar modelo de Elige8 como modalidad independiente y opcional; requisitos de validación específicos en versión posterior.

### M03 — Generadores / asistente inteligente

- **RF-GEN-001** Generar apuestas al azar con semilla reproducible y distribución configurable.
- **RF-GEN-002** Generador ponderado por probabilidades por partido y Pleno al 15.
- **RF-GEN-003** Generar signos, dobles y triples dada una cantidad o distribución de riesgo.
- **RF-GEN-004** Sugerir propuestas dentro de presupuesto; no sobrepasarlo sin confirmación.
- **RF-GEN-005** Respetar signos fijos y bloqueos manuales.
- **RF-GEN-006** Generar columnas a distancia de Hamming especificada de una o varias referencias.
- **RF-GEN-007** Generar N apuestas únicas o explicar si la demanda es imposible.
- **RF-GEN-008** Asistente con dos modos: automático y experto, explicando reglas y fuentes usadas.
- **RF-GEN-009** Predicción de signo y Pleno al 15 desde modelos registrados y evaluados, con fallback honesto (sin predicción) si faltan datos.
- **RF-GEN-010** Estabilización de porcentajes: aproximar una distribución objetivo de signos en las columnas generadas, ciclos reproducibles y error final informado.

### M04 — Probabilidad y porcentajes

- **RF-PRO-001** Cargar P(1), P(X), P(2) por partido, con validación suma=1 dentro de tolerancia.
- **RF-PRO-002** Capturar separadamente porcentajes de selección pública de SELAE y otras fuentes, con fecha y procedencia.
- **RF-PRO-003** Mostrar diferencias porcentuales entre probabilidad estimada y proporción jugada.
- **RF-PRO-004** Guardar distribución `4×4` para Pleno al 15 y verificar que suma 1.
- **RF-PRO-005** Ordenar columnas por probabilidad estimada; etiquetar supuesto de independencia cuando se use.
- **RF-PRO-006** Redondear SOLO para representación; no alterar cálculo interno.
- **RF-PRO-007** Columnas Base y sugerencias «más 1 / más X / más 2» ordenando probabilidades de signos.
- **RF-PRO-008** Mostrar valores de fuente, instante y advertencia de datos incompletos u obsoletos.

### M05 — Filtros y condiciones

- **RF-FIL-001** Motor de filtros composable, registro, validación, ejecutar por lotes y reportar descartes.
- **RF-FIL-002** Filtros de recuentos y secuencias (1, X, 2, variantes, signos seguidos, interrupciones).
- **RF-FIL-003** Filtros de patrones: parejas, tríos, cuartetos, quintetos, sextetos, septetos y por partido.
- **RF-FIL-004** Filtros de columnas base (CB), sumas de CB, CB relacionadas y grupos de CB.
- **RF-FIL-005** Filtros de diferencias, coincidencias, rangos, figuras X-2, dibujos de variantes.
- **RF-FIL-006** Filtro de valoraciones (suma, productos/logaritmos con gestión numérica segura).
- **RF-FIL-007** Filtro `IF THEN`, condiciones vinculadas y grupos generales.
- **RF-FIL-008** Reservas: tolerancia controlada al incumplimiento de condiciones con reglas explícitas.
- **RF-FIL-009** Activación independiente, orden, presets, clonación, import/export versionado de condiciones.
- **RF-FIL-010** Estudio previo de cada filtro: límites posibles, distribución, efecto y recomendación **sin prometer resultados**.
- **RF-FIL-011** Informe de fallo: qué condición descartó una columna/resultado ganador y por qué.
- **RF-FIL-012** Guardar opcionalmente descartes por filtro, en modo streaming.
- **RF-FIL-013** Filtros de rentabilidad y probabilidad solo cuando existan datos válidos.

### M06 — Reducción de combinaciones

- **RF-RED-001** Reducir sobre conjunto base ya filtrado con presupuesto o número objetivo de columnas.
- **RF-RED-002** Modos de optimización: cobertura, probabilidad o combinación ponderada; explicar los compromisos.
- **RF-RED-003** Objetivos de 14 a 9 aciertos y objetivos de N premios si son matemáticamente interpretables.
- **RF-RED-004** Generadores propios: voraz (greedy), mejora local, búsqueda con semillas y optimizadores opcionales.
- **RF-RED-005** Separar apuestas candidatas internas (del sistema base) de candidatas externas (si se autoriza dominio mayor).
- **RF-RED-006** Ajustar número exacto de columnas solo si el objetivo es factible; indicar limitaciones.
- **RF-RED-007** Progreso, pausa segura, cancelación, recuperación de mejor solución y parámetros.
- **RF-RED-008** Comparar porcentajes y cobertura antes/después; exportar informe verificable.
- **RF-RED-009** No llamar REDWIN ni garantizar compatibilidad matemática sin especificaciones independientes.

### M07 — Garantías

- **RF-GAR-001** Medir cobertura de cada umbral 14..0 sobre dominio de resultados definido.
- **RF-GAR-002** Distinguir garantía absoluta condicional, porcentaje de escenarios cubiertos y probabilidad modelada de cobertura.
- **RF-GAR-003** Número mínimo de premios de cada categoría, cuando sea verificable para el dominio elegido.
- **RF-GAR-004** Evaluar resultados del Pleno al 15 por separado, vinculado al acierto de los primeros 14.
- **RF-GAR-005** Pruebas exhaustivas en dominios pequeños, validación externa/cotas en dominios grandes.
- **RF-GAR-006** Subir cobertura con heurística y comparar coste adicional.

### M08 — Rentabilidad, premios y estimaciones

- **RF-REN-001** Coeficiente original y documentado, sin afirmar equivalencia al CR propietario de Quiniwin.
- **RF-REN-002** Calcular probabilidad modelada, coste, premio estimado e incertidumbre individual de apuestas.
- **RF-REN-003** Estimar acertantes desde patrones públicos, recaudación y reglas versionadas; indicar hipótesis.
- **RF-REN-004** Valorar apuestas mediante beneficio esperado, riesgo y diversificación.
- **RF-REN-005** Ranking por rentabilidad / probabilidad; visualización por colores con leyenda accesible.
- **RF-REN-006** Estimar posibles premios con 3 o menos encuentros pendientes, sin mezclarlos con premios oficiales.
- **RF-REN-007** Calculadora de premios históricos y definitivos con datos oficiales validados.
- **RF-REN-008** Comparativa real vs simulada: coste, premios, beneficio neto y retorno acumulado.

### M09 — Escrutador / multiescrutador

- **RF-ESC-001** Escrutinio parcial y final de sistemas locales y ficheros externos.
- **RF-ESC-002** Categorías de aciertos 14,13,12,11,10 y Pleno al 15 según reglas vigentes.
- **RF-ESC-003** No conceder Pleno al 15 por acertar solo el marcador si faltan los 14.
- **RF-ESC-004** Filtrar solo partidos finalizados; mostrar intervalo de aciertos potenciales en parciales.
- **RF-ESC-005** Procesar múltiples ficheros con progreso, cancelar y ranking.
- **RF-ESC-006** Columnas ganadoras aleatorias solo en simulación, claramente identificada.
- **RF-ESC-007** Informe detallado / resumido y desglose de apuestas sin premio.
- **RF-ESC-008** Escrutinio independiente que permita cargar TXT/JSON propios y los formatos externos oficialmente documentados.

### M10 — Simulaciones

- **RF-SIM-001** Simular escenarios desde probabilidades explícitas, con semilla reproducible.
- **RF-SIM-002** Simulaciones uniformes y ponderadas; comparación con enumeración exacta en dominios pequeños.
- **RF-SIM-003** Distribución de aciertos, cobertura, volatilidad de premios estimados y resultados por estrategia.
- **RF-SIM-004** Comparar 2 o más sistemas con exactamente el mismo conjunto de resultados simulados.
- **RF-SIM-005** Backtesting cronológico sin usar datos posteriores a cada cierre de jornada.
- **RF-SIM-006** Reportar intervalos de confianza y limitaciones del modelo.

### M11 — Estadística avanzada

- **RF-EST-001** Frecuencias y radiografías 1/X/2 de sistemas y columnas ganadoras.
- **RF-EST-002** Análisis de patrones de tamaño 2 a 7, solapados o no, definidos matemáticamente.
- **RF-EST-003** Figuras, dibujos, transiciones, interrupciones y secuencias por subconjuntos de partidos.
- **RF-EST-004** Distancias de Hamming y distribución entre columnas.
- **RF-EST-005** Gráficas por jornadas/temporadas, con periodo aplicable a todos los cálculos.
- **RF-EST-006** Medir efectos de cada filtro y estudiar la conservación de resultados históricos.

### M12 — Taller de combinaciones y archivos

- **RF-ARC-001** Import/export nativo versionado a JSON y texto simple, sin pérdida del Pleno al 15.
- **RF-ARC-002** Soporte XML interno y compatibilidad externa mediante adaptadores de formato.
- **RF-ARC-003** Unir, intersecar, restar, deduplicar y ordenar grandes conjuntos.
- **RF-ARC-004** Dividir por número, tamaño y Pleno al 15; conservar manifiestos para recomponer.
- **RF-ARC-005** Compactar/descompactar definiciones de fijos/dobles/triples cuando sea representable, sin inventar equivalencias.
- **RF-ARC-006** Intercambiar signos/posiciones, generar sistemas aleatorios y por distancias.
- **RF-ARC-007** Inferir **aproximadamente** restricciones de una combinación importada, indicando error.
- **RF-ARC-008** Adaptadores AD243, ASD(JSON), ASCII heredado y `.NUM` solo después de reunir especificaciones y fixtures legales.

### M13 — Boletos, PDF, QR y sellado

- **RF-BOL-001** Mostrar apuestas y preparar PDF legible, con coste, jornada, plenos y total.
- **RF-BOL-002** Diagramación de varias apuestas por página y salida de prueba.
- **RF-BOL-003** QR de uso interno (para recuperar proyectos) separado de QR oficial de validación.
- **RF-BOL-004** QR/ASD oficiales condicionados a formato publicado/permiso y pruebas de conformidad.
- **RF-BOL-005** Envío a portales solo con integración autorizada, confirmación manual y recibo auditable.
- **RF-BOL-006** No declarar «apuesta registrada» si únicamente se generó PDF o QR.

### M14 — Peñas y participaciones

- **RF-PEN-001** Registrar peñas, integrantes, aportes y porcentajes de participación.
- **RF-PEN-002** Asociar apuestas/sistemas a peña y jornada.
- **RF-PEN-003** Calcular participaciones y repartos con aritmética decimal exacta y reglas explícitas.
- **RF-PEN-004** Informes de participantes, aportaciones y resultados; PDF imprimible.
- **RF-PEN-005** No gestionar cobros reales ni facturación regulada sin fase separada.

### M15 — Informes, historial, configuración y auditoría

- **RF-AUD-001** Bitácora de cada acción: origen de datos, filtros, reducción, semilla, costes y resultados.
- **RF-AUD-002** Historial comparativo y posibilidad de reproducir un sistema desde parámetros versionados.
- **RF-AUD-003** Informes de quiniela, filtros, apuestas eliminadas, garantías, escrutinio y desempeño.
- **RF-AUD-004** Panel inicial: jornada vigente, actividad reciente y accesos útiles, sin saturación.
- **RF-AUD-005** Preferencias de idioma, accesibilidad, tema, fuentes y límites de presupuesto.
- **RF-AUD-006** Copia de seguridad, exportación de datos y restauración con confirmación.
- **RF-AUD-007** Diagnóstico entendible de importaciones fallidas, dependencia ausente y errores de datos.
- **RF-AUD-008** Instalación portable sin rutas de usuario incrustadas; registro de versión de datos y migraciones.

## 4. Requisitos no funcionales

- **RNF-01 Correctitud:** prioridad sobre velocidad; oráculos de referencia para todo el dominio matemático.
- **RNF-02 Rendimiento:** iteradores, procesamiento por lotes, no agotar RAM en 3^14 escenarios. Benchmarks documentados para cargas crecientes.
- **RNF-03 Resiliencia:** cálculos largos cancelables, escrituras atómicas, checkpoints en trabajos persistentes.
- **RNF-04 Seguridad:** local-first, mínimos permisos, autenticación si un conector la precisa, secretos fuera de repositorio.
- **RNF-05 Integridad:** IDs y hashes de contenido para reproducibilidad, esquema versionado y migraciones.
- **RNF-06 Usabilidad:** flujo guiado para principiante, opciones expertas desplegables, navegación por teclado.
- **RNF-07 Observabilidad:** logs técnicos separados del historial humano; sin filtración de tokens.
- **RNF-08 Compatibilidad:** Python >=3.11, Linux Mint y Windows, instalación reproducible.
- **RNF-09 Ética y transparencia:** mostrar incertidumbre, pérdidas, advertencia de que no hay garantía de premio, presupuestos máximos.
- **RNF-10 Extensibilidad:** motor de reglas, proveedores y formatos basados en interfaces versionadas.

## 5. Fuera de alcance de la primera entrega

No se implementan en v0.1: IA entrenada, REDWIN, CR propietario, integración con pago, envío de apuestas, QR SELAE, Elige8 completo, un motor de 40 filtros, peñas, ni escrutinio monetario en directo. Estos componentes siguen en el roadmap, con criterios de aceptación propios.
