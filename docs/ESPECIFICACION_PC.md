# Quiniela AI Studio — especificación de escritorio

Versión del documento: 1.0 · 9 de octubre de 2026.
Base auditada: `bb39166`, aplicación Python/Tkinter existente.
Estado: plano de desarrollo, **no declaración de funcionalidades implementadas**.
Ámbito: PC Linux y Windows. Android, sus recursos y APK quedan fuera de esta ampliación.

## 1. Objetivo y reglas de producto

Crear, analizar, generar, abaratar, comprobar y exportar quinielas sin necesitar
conocimientos de combinatoria. Se conserva la aplicación actual mientras se
construye y verifica la nueva arquitectura por versiones.

- Toda generación o reducción actualiza el sistema activo y su base visible.
  La unión de signos es una representación: no sustituye las columnas exactas.
- Optimizar presupuesto selecciona únicamente apuestas del desarrollo de origen.
  Una nueva generación debe ser una acción diferente y claramente identificada.
- Mostrar siempre temporada, jornada, sistema, fuente, hora de los datos y modo.
  Navegar entre jornadas no mezcla sistemas. Solo la jornada en curso es editable;
  las anteriores y futuras publicadas permiten consulta e importación para revisar.
- Los signos se seleccionan por color en recuadros 1/X/2, sin una cruz añadida.
  Pleno: dos filas de 0/1/2/M. Partidos en una única lista vertical compacta.
- Cobertura y ajustes rápidos mantienen barras 0–10 y valores explicados.
- Sin conexión funcionan los datos guardados, cálculos, sistemas y exportaciones.
  Las descargas y las webs externas sí requieren conexión, no un servidor propio.
- No hay pagos automáticos, custodia de credenciales ni apuestas enviadas sin
  acción expresa. Exportar o imprimir **no significa validar una apuesta**.
- No inventar fuentes, porcentajes, históricos, premios, entrenamiento o garantías.
  Un dato ausente se identifica como ausente; un modelo se identifica como modelo.
- Límites de presupuesto y advertencias no se incrementan automáticamente para
  perseguir pérdidas. Ofrecer modo de simulación sin gasto.

## 2. Inventario y alcance de los 15 módulos

«Parcial» significa que hay funcionalidad aprovechable, no que se cumple todo el
alcance nuevo. «Motor» significa cálculo existente sin pantalla completa.

| ID | Módulo | Base real de PC | Entrega requerida | Fase |
| --- | --- | --- | --- | --- |
| M01 | Jornadas y resultados | Parcial: ZIP WIN1X2, horarios, porcentajes, directo e histórico limitado | Navegación por temporada/jornada, caché versionada, procedencia, recaudación/acertantes, proveedores autorizados | 1 |
| M02 | Constructor | Parcial: múltiples, Pleno, persistencia y desarrollo sincronizado | Bloqueos, plantillas, sistemas separados por jornada, deshacer y edición protegida | 1 |
| M03 | Generador inteligente | Parcial: columnas probables y presupuesto; no IA entrenada | Asistente de presupuesto/riesgo 0–10, respeto de bloqueos, estrategias y explicaciones verificables | 1/3 |
| M04 | Probabilidades | Parcial: heurística y porcentajes en el mismo campo | Separar probabilidad deportiva y porcentaje jugado; comparar fuentes y modelos calibrados | 1/3 |
| M05 | Filtros | Interfaz básica; motor adicional de figuras/grupos/sumas | Modo sencillo/experto, catálogo formal, reservas, IF THEN e impacto de cada regla | 2/4 |
| M06 | Reductor | Heurística de probabilidad/diversidad Hamming | Cobertura objetivo 9–14, presupuesto, semilla, cancelación, mejor solución y comparación | 2 |
| M07 | Garantías | No implementado | Verificador independiente, dominio declarado, certificado exacto o muestreo explícito | 2 |
| M08 | Rentabilidad | No implementado; masa de probabilidad no es rentabilidad | Estimador económico versionado, valor esperado, incertidumbre, comparación público/modelo | 3 |
| M09 | Escrutador | Parcial: directo, TXT, aciertos y premios | Varios sistemas, categorías acumulables, escenarios con pocos pendientes, trazabilidad oficial | 1/3 |
| M10 | Simulaciones | No implementado | Monte Carlo reproducible, comparación pareada, intervalos y sensibilidad | 3 |
| M11 | Estadística | Parcial: medias de signos y masa probabilística | Frecuencias, patrones 2–7, distancias, evaluación histórica y filtros restrictivos | 2/3 |
| M12 | Archivos | Parcial: TXT de apuestas/importación y texto informativo | TXT/ASCII, JSON, XML, unión/intersección/resta/división y conversión; ASD condicionado | 1/4 |
| M13 | Boletos y salidas | Parcial: TXT y enlace externo de carga | Vista previa, PDF, Plenos por apuesta; QR solo con especificación validada | 4 |
| M14 | Peñas | No implementado | Participantes, aportaciones, participaciones y reparto exacto auditado | 4 |
| M15 | Informes e historial | Estado JSON, sin auditoría integral | Sistemas persistentes, versiones, decisiones, ejecuciones y resultados comparables | 1/4 |

### Hallazgos de la base que deben resolver las primeras entregas

1. `load_matches` utiliza `p_jugados_*` como `Match.probabilities`. No es una
   estimación deportiva independiente. El generador debe identificar qué utiliza.
2. La heurística actual emplea 40/30/30 sin histórico. Debe etiquetarse como
   supuesto sin calibración, nunca como porcentaje descargado ni observación.
3. `generate_columns` es iterador, pero la interfaz convierte el resultado filtrado
   en listas y lo ordena; además impone un límite de un millón. No es aún un
   procesamiento masivo por bloques ni una operación cancelable en segundo plano.
4. `reduce_columns` selecciona por diversidad; no prueba cobertura de 13, 12, etc.
5. `parse_scrutiny` busca la jornada con un prefijo numérico variable, aunque PRE
   utiliza dos caracteres fijos. Añadir registros con jornada pegada al primer
   número de acertantes antes de cambiar el lector.
6. La categoría única de `evaluate_bets` no expresa que una apuesta con 14 y Pleno
   puede participar en ambos conceptos. Revisar el cálculo agregado de premios.
7. Las columnas activas se guardan globalmente junto a pronósticos, no como
   sistemas inmutables identificados por temporada/jornada y versión.
8. El histórico por códigos no basta para prometer cobertura de todos los equipos.
   Comprobar identidad/competición antes de atribuir registros.

Estos son hallazgos de código, no cambios aplicados por este documento. Las
18 pruebas actuales pasan, pero no cubren por sí solas los nuevos requisitos.

## 3. Interfaz: siete secciones, un sistema activo

| Sección | Contenido y acciones |
| --- | --- |
| Inicio | Jornada vigente, estado de datos, últimos sistemas; Crear automáticamente, Crear manualmente, Consultar premios |
| Crear Quiniela | Lista compacta, Pleno, bloquear signos, fuentes, cobertura 0–10, precio; asistente Elegir → Condicionar → Revisar |
| Optimizar | Desarrollo de origen visible, presupuesto, reducción, cobertura objetivo, filtros, comparar/conservar soluciones |
| Análisis | Garantías, probabilidad, popularidad, rentabilidad, simulaciones y estadísticas |
| Escrutinio | Temporada/jornada, sistemas o TXT, directo, aciertos y premios definitivos/provisionales diferenciados |
| Mis Sistemas | Abrir, duplicar, versionar, importar/exportar, taller de archivos, peñas e informes |
| Configuración | Proveedores, permisos/licencias, modelos, reglas de precio/premios, límites, almacenamiento y copias |

La cabecera identifica sistema y jornada. El pie resume columnas realmente
jugadas, coste, Plenos pendientes y tipo de cobertura. No reconstruir el producto
cartesiano para cobrar/exportar un desarrollo reducido.

Modo sencillo: valores recomendados con explicación y barras 0–10; no activar
filtros ocultos. Modo experto: las mismas reglas, con parámetros completos.
Cada preajuste muestra todos los cambios que introduce y admite deshacer.

Diseño adaptable a 1024×768 y escalas de 100/125/150/200 %. Los botones de
acción siguen accesibles con scroll; nada queda fuera de pantalla. Tablas
virtualizadas/paginadas, selección y desplazamiento conservados al actualizar.
Solo cambian las celdas cuyos datos han cambiado: no borrar/recrear toda la tabla.
No depender solo del color: texto, contornos, leyendas y acceso por teclado.

## 4. Modelo de datos y arquitectura

### 4.1 Entidades persistentes

SQLite local con claves externas, migraciones numeradas, transacciones y copias.
No se necesita PostgreSQL para este producto monousuario.

- `Season`, `Round`: identificador, fechas/horarios, cierre, estado y reglas vigentes.
- `Team`, `Match`: identidad con espacio de nombres de proveedor y competición,
  orden 1–15, equipos, inicio, resultado y estado. No usar solo nombre/código corto.
- `Source`: tipo, proveedor, licencia/permisos conocidos, URL y versión de lector.
- `ProbabilitySnapshot`: partido, fuente, tipo `sport` o `public`, p1/px/p2,
  fecha de captura, vigencia, versión de modelo y procedencia. P15 usa 16 valores.
- `ModelVersion`: variables, entrenamiento, corte temporal, calibración y métricas.
- `System`, `SystemVersion`: jornada, nombre, base, bloqueos, reglas de filtros,
  origen, hash de columnas, Plenos, cantidades y estado (borrador/final/archivado).
- `Run`: parámetros, semilla, fuentes congeladas, estado, tiempos, versión de motor,
  progreso, mejores soluciones y motivo de cancelación/error.
- `Bet`: columna, Pleno y cantidad. Cantidad no se pierde al importar repetidos.
- `GuaranteeReport`, `SimulationReport`, `Evaluation`: método, dominio, resultado,
  intervalos/certificado y hashes de sistema, reglas, modelo y datos.
- `PrizeSnapshot`: resultado definitivo, categoría, acertantes, importe bruto,
  recaudación/bote cuando existan, fecha y origen.
- `Pool`, `Member`, `Contribution`, `Participation`, `Distribution`: peña y reparto.
- `AuditEvent`: operación, versión de entrada/salida, fecha y resumen; sin secretos.

Formato monetario: enteros en céntimos o `Decimal`, nunca acumulaciones `float`.
Fechas persistidas con zona/UTC y visualizadas en la zona elegida. Los porcentajes
se almacenan normalizados 0–1, no mezclados con valores 0–100.

### 4.2 Capas y contratos

```text
UI Qt → servicios de aplicación → dominio/motores → repositorios SQLite/archivos
                                   ↑
                        adaptadores de proveedores
```

El dominio no importa widgets, red ni globals de la interfaz. Los adaptadores
transforman datos externos en entidades validadas; no deciden pronósticos.
Servicios propuestos: `RoundService`, `SystemService`, `GenerationService`,
`FilterService`, `ReductionService`, `GuaranteeService`, `SimulationService`,
`EvaluationService`, `FileService`, `PoolService` y `ReportService`.

Todas las tareas costosas reciben entradas inmutables, semilla, cancelación y
callback de progreso. La UI solo recibe eventos; ninguna actualización de
widgets desde procesos/hilos de trabajo. Para CPU intensiva usar procesos o
núcleo nativo; un hilo Python no elimina el coste del GIL.

El cálculo entrega columnas exactas, estadísticas y procedencia. Aplicar una
solución crea una versión; no destruye el desarrollo original. Las fuentes y
reglas quedan congeladas para poder repetirlo, aunque cambien los datos en red.

Migrar `pronosticos.json` y desarrollos con copia previa. Si no se puede determinar
la jornada de unas columnas, pedir asignación y conservarlas como «sin asignar»;
no inventar identidad ni migrar silenciosamente a la jornada vigente.

### 4.3 Tecnologías y decisión medible

Python conserva coordinación y motor de referencia. PySide6/Qt es la UI objetivo,
no una obligación de reescribir todo de una vez. Mantener el arranque Tkinter
hasta que la nueva UI supere las pruebas de paridad. La documentación oficial
describe despliegue y licencias; revisar las obligaciones de los componentes
elegidos antes de distribuir, no asumir que todo módulo Qt tiene igual licencia.
[Qt for Python](https://doc.qt.io/qtforpython-6),
[despliegue](https://doc.qt.io/qtforpython-6/deployment/index.html).

Primero medir Python y representación compacta. Añadir NumPy/Numba o Rust solo
si los perfiles justifican el coste; no instalar todas las tecnologías por defecto.
Gráficas integradas con Qt; valorar PyQtGraph si el prototipo lo necesita. PDF
mediante un backend con licencia y salida reproducible verificadas.

## 5. Contratos matemáticos

### 5.1 Base, apuestas y probabilidades

`B=(S1,…,S14)`, cada `Si` es un subconjunto no vacío de `{1,X,2}`.
`D_base=S1×…×S14`, `N=∏|Si|`. Columna `c` tiene exactamente 14 signos.
El universo completo tiene `3^14=4.782.969` columnas. El Pleno es una pareja de
`{0,1,2,M}`: 16 categorías, donde M agrupa tres o más goles.

Una apuesta final es `(c,g_local,g_visitante,cantidad)`. Si hay varios Plenos,
las asignaciones concretas forman apuestas distintas; el coste depende de esas
apuestas, no solo del número de columnas de 14 signos. Un sistema de una columna
no se transforma silenciosamente en dos: explicar mínimos del canal de validación
y qué segunda apuesta se incorpora, si procede.

`p_i(s)` = probabilidad deportiva; `q_i(s)` = proporción jugada.
Validar finitud, 0≤valor≤1 y suma uno con tolerancia documentada. Importar cuotas
decimales autorizadas: `a_s=1/cuota_s`, `p_s=a_s/Σa`, indicando que se elimina
el margen con un método proporcional, no que se obtiene una verdad deportiva.
Combinar únicamente fuentes del mismo tipo mediante pesos no negativos que
suman uno; conservar pesos/fuentes y no presentar una mezcla de público y modelo
como modelo deportivo independiente.

Bajo independencia entre partidos: `P(c)=∏p_i(c_i)`, `logP(c)=Σlog p_i(c_i)`.
Un cero verdadero produce `−∞`, no una probabilidad positiva por redondeo.
Para evitar ceros por falta de muestra usar suavizado explícito del modelo.
El Pleno necesita una distribución propia; no se deriva de 1/X/2.
`P14(C)=Σ_{c∈unique(C)}P(c)`. No sumar dos veces columnas repetidas ni probabilidades
de sucesos solapados «alguna columna alcanza 12».

### 5.2 Garantías y reducción

Dominio `D`: base completa, base condicionada o escenarios externos explícitos.
Guardar su definición y hash; una garantía condicionada no es una garantía global.
`h(c,r)=Σ[c_i=r_i]`, `H_C(r)=max_{c∈C}h(c,r)`.

- Garantía exacta de m: `∀r∈D, H_C(r)≥m`.
- Número garantizado de apuestas con al menos m: mínimo sobre `r∈D` del número
  de apuestas que cumplen `h≥m`, con política explícita de cantidades/repetidos.
- Cobertura combinatoria: `|{r∈D:H_C(r)≥m}|/|D|` (escenarios equiponderados).
- Cobertura del modelo condicionada a D: suma de `P(r)` de escenarios cubiertos
  dividida por `Σ_{r∈D}P(r)`. Mostrar también cobertura incondicional si se calcula.
- Cobertura por muestreo: estimación, tamaño de muestra, semilla e intervalo;
  **nunca etiquetar como certificado matemático**, aunque no haya fallos observados.

Comprobar garantías con un verificador distinto al reductor. Un informe exacto
incluye m, dominio, columnas, cantidad de escenarios y un contraejemplo cuando
falla. Solo certificar al completar enumeración exacta o una prueba verificable.
En cálculo interrumpido informar qué queda sin verificar; no emitir un «100 %».

Heurística inicial propia: cobertura voraz (nuevos escenarios cubiertos por coste),
ponderación opcional por P, diversidad y búsqueda local con semilla. Comparar
contra el reductor existente. No llamar al método REDWIN/007R ni afirmar equivalencia.
Objetivo configurable: minimizar apuestas para m, o maximizar cobertura bajo
presupuesto. Si no se alcanza la garantía al presupuesto dado, entregar la mejor
solución como heurística y explicar el incumplimiento, sin elevar el gasto.

### 5.3 Premios, valor esperado y simulación

Por resultado `r`, contar apuestas de cada categoría. Pleno exige 14 y la pareja
correcta; el informe mantiene separados y acumula 14 y categoría especial cuando
las reglas lo contemplan. Con resultados pendientes, calcular aciertos conocidos,
confirmados y máximo, sin asignar X a 0–0 de partidos no comenzados.

`premio(C,r)=Σ apuestas × premios aplicables(r)`; `beneficio=premio−coste`.
Solo usar «premio definitivo» con resultado y escrutinio publicado. El resultado
deportivo definitivo sin escrutinio no determina cuánto cobra cada categoría.
Los informes muestran importes brutos; fiscalidad no se calcula sin reglas propias
verificadas. Con hasta tres partidos pendientes enumerar los signos posibles
(como máximo 27); incorporar aparte incertidumbre del Pleno y de los importes.

`EV(C)=E_r[premio(C,r)]−coste(C)` y `ROI=EV/coste` cuando coste>0.
No calcular EV monetario únicamente con P y q. Se necesita modelo de recaudación,
fondo por categoría, acertantes de público, botes y reglas de reparto.
Como aproximación, `Q(r)=∏q_i(r_i)` supone independencia del público y
`N_public×Q(r)` estima acertantes de 14, no todas las categorías ni una certeza.
Los acertantes de 10–13 requieren agregar las columnas a la distancia correspondiente.
La expectativa de un cociente no es el cociente de las expectativas: no confundir
`E[fondo/acertantes]` con `fondo/E[acertantes]`.

Un indicador propio de popularidad relativa puede usar `logP(c)−logQ(c)` con
tratamiento explícito de ceros y suavizado. Se llama «desviación modelo/público»,
no «CR de Quiniwin» ni beneficio garantizado. Sin modelo económico válido,
ocultar EV en euros y mostrar únicamente análisis de probabilidad/popularidad.

Monte Carlo: sortear resultados con el modelo congelado, semilla y dependencias
declaradas; usar los mismos escenarios al comparar estrategias. Informar categorías,
probabilidad de pérdida, cuantiles, intervalos, coste, premios simulados y sensibilidad.
Si faltan importes/modelo económico, simular aciertos, no inventar ganancias.

Entrenamiento: separación temporal entrenamiento/validación/prueba, partidos y
cuotas solo disponibles antes de apostar, baseline comparables y backtesting sin
fuga de información. Evaluar Brier multiclase, log-loss, calibración y tamaño de
muestra; no elegir modelos solo por un premio raro o por rendimiento en entrenamiento.
Predicción de goles (por ejemplo Poisson) es una hipótesis a contrastar, no función
ya entrenada. Explicaciones proceden de variables y fuentes reales, no de narrativas
inventadas por un modelo de lenguaje.

## 6. Inventario formal de filtros

Todos operan sobre columnas válidas, con posiciones de usuario 1–14. Cada regla
devuelve valor/valores, estado y explicación; no solo un booleano. Referencias y
grupos se evalúan una vez por columna y se reutilizan. Configuración serializada
con ID y versión; sin `eval` de expresiones escritas por el usuario.

| ID | Familia | Definición inicial verificable |
| --- | --- | --- |
| F01 | Recuentos | min/max de 1, X, 2 y variantes X+2; también en grupos de posiciones |
| F02 | Rachas | Máxima secuencia consecutiva por signo; límites inclusivos |
| F03 | Interrupciones | Número de pares adyacentes con signos distintos, entre 0 y 13 |
| F04 | Distancias | Diferencias entre posiciones consecutivas de un signo; sin pareja, condición vacuamente satisfecha, indicado en UI |
| F05 | CB/coincidencias | Aciertos contra referencia simple o patrón múltiple; min/max |
| F06 | Grupos de CB | Vector de aciertos de varias referencias y condiciones por grupo |
| F07 | CB relacionadas | Diferencia con/sin valor absoluto y sumas de aciertos entre grupos |
| F08 | Frecuencia relacionada | Número de grupos cuyo acierto pertenece a un intervalo |
| F09 | Escaleras | Relaciones ordenadas entre aciertos, p.ej. `hA≤hB≤hC`; operadores configurados |
| F10 | Patrones 2–7 | Posiciones explícitas y tuplas de signos admitidas; distinguir consecutivos/arbitrarios y política de solapamiento |
| F11 | Signos iguales/diferencias | Comparaciones entre pares de posiciones o bloques de igual tamaño; cantidad de igualdades/cambios |
| F12 | Figuras X/2/variantes | Tupla de recuentos por bloques definidos; lista de figuras admitidas |
| F13 | Dibujos | Firma posicional de variantes o signos en una cuadrícula definida; convención propia con ejemplos, no supuesta compatibilidad propietaria |
| F14 | Valoraciones/sumas | `Σv_i(c_i)`, total o solo 1/X/2/variantes; tablas explícitas |
| F15 | Productos/probabilidad | Producto o suma de logaritmos de valores positivos; ceros/negativos con validación y semántica definida |
| F16 | Rangos | Número de valores en intervalos no solapados `[a,b)`, último extremo explícito |
| F17 | Valor económico | Umbrales del estimador propio; deshabilitado sin modelo/datos económicos |
| F18 | IF THEN | Árbol tipado: si A pasa entonces B debe pasar; antecedente falso satisface la implicación |
| F19 | Reservas | Máximo de reglas/grupos incumplidos dentro de un conjunto marcado; reglas obligatorias fuera de esa tolerancia |

Los nombres especializados sin definición verificable se marcan como pendientes,
no se incorporan con un botón que ejecuta otro filtro. Para una figura «probable»,
estimar su frecuencia con el mismo modelo y método explícitos.

Informe de filtrado: entrada, salida, descartes marginales según orden y fallos
individuales sobre una muestra/dominio fijo. Los fallos de filtros se solapan:
no sumar porcentajes individuales como si fueran descartes disjuntos. Con reservas
evaluar el conjunto completo antes de rechazar; no descartar al primer fallo.
Advertir cuando no queda ninguna apuesta o se elimina un porcentaje elevado,
sin reactivar apuestas a escondidas. Preajustes tienen versiones y umbrales visibles.

## 7. Motor masivo, rendimiento y cancelación

Representar 1/X/2 como dígitos ternarios y codificar una columna en un entero
`uint32`; el Pleno puede codificarse en cuatro bits adicionales (`16*id14+id15`).
Las 4.782.969 columnas en un array compacto `uint32` ocupan unos 18,25 MiB,
sin contar metadatos; un bitmap de pertenencia ocupa unos 0,57 MiB. Las tuplas
Python y las matrices escenario×apuesta ocupan mucho más: evitarlas.

Generar en bloques (inicialmente 65.536 columnas, configurable), filtrar por
bloques y usar top-k/archivos temporales cuando no se necesita toda la colección.
El Pleno no obliga a materializar 76.527.504 objetos. Tablas muestran solo filas
visibles; exportación recorre todas las apuestas sin truncarlas a 100.

Una reducción exacta/cobertura puede ser mucho más costosa que generar columnas:
preestimar `|D|×|C|`, memoria y tiempo, sin prometer tiempos universales. Evaluar
bitsets/vecindarios por distancia y estrategias fuera de memoria con benchmarks.
Cancelar conserva la mejor solución completa, nunca una estructura a medio guardar.

Banco de pruebas reproducible: 14 fijos, 10 dobles, base nivel 10 (3 triples,
7 dobles, 4 fijos), 14 triples, varios tamaños finales y filtros simples/combinados.
Registrar CPU/RAM/SO, versiones, semilla, tiempo, memoria máxima y latencia de UI.
Objetivos a validar en el PC de referencia: UI sin bloqueo, cancelación atendida
en ≤1 s para operaciones por bloques, generación/filtrado simple bajo 256 MiB
adicionales. No extender este límite a optimización intensiva sin medirla.

## 8. Archivos, peñas y auditoría

TXT compatible: una apuesta por línea, 14 signos seguidos y dos caracteres del
Pleno cuando el destino lo exige. Texto explicativo/plan no se exporta como TXT
de apuestas. JSON versionado conserva jornada, columnas, cantidades, Plenos,
fuentes y filtros; XML con esquema propio. ASCII identifica codificación, no
promete un formato de terceros. ASD y QR oficiales requieren especificación
autorizada y prueba de compatibilidad; mientras tanto no anunciar soporte.

Importación valida longitud/signos, numeración, tamaño máximo y jornada. TXT sin
identidad se vincula mediante una selección visible del usuario. Proteger ZIP de
traversal/bombas y XML de entidades externas. Verificar fuentes contra temporada,
jornada y equipos antes de escribir la caché. Escribir atómicamente y recuperar
descargas fallidas sin perder los datos anteriores.

Taller: unión, intersección, diferencia, deduplicación, división equilibrada,
ordenación, cambio de posiciones, generación aleatoria/distancia e inferencia
descriptiva de recuentos. Deducir condiciones de un archivo no permite recuperar
exactamente sus reglas originales; etiquetarlo como resumen/inferencia.
Duplicados: preguntar mediante una opción de importación visible si conservar
cantidad o quitar repetidos; no alterar el gasto o el reparto silenciosamente.

Peñas: participaciones basadas en aportaciones confirmadas, no en intención de
pago. Separar simulación/reparto previsto del reparto de premios cobrados.
Repartir céntimos por mayores restos con desempate estable; suma de repartos
igual al importe repartible y registro de política. No transferir dinero ni
emitir justificantes que afirmen cobros/validaciones inexistentes.

Informe estándar: sistema/jornada, hashes, datos usados, columnas antes/después,
filtros, objetivo, coste, cobertura y método, incertidumbre, origen de premios,
fechas, versiones y decisiones. Historial de rentabilidad real solo incorpora
gasto confirmado y premios realmente registrados; las simulaciones van aparte.

## 9. Entregas y dependencias

### Fase 1 — Base fiable y navegación integrada

Extraer servicios reutilizando motores actuales; almacenamiento por sistema/jornada,
fuentes separadas, lector PRE y premios acumulables correctos, migración segura,
plantillas/bloqueos, asistente y exportación revisable. Prototipo Qt de siete
secciones con funcionalidades actuales. Mantener lanzador anterior disponible.

Salida: paridad funcional con el PC actual, datos personales intactos, edición
solo vigente, importación/exportación sin mezcla de jornadas, tests y paquetes
Linux/Windows verificables. No añadir «IA» o «garantías» como botones vacíos.

### Fase 2 — Optimización verificable

Motor por bloques, filtros F01–F16/F18/F19, impacto de reglas, reducción por
cobertura y verificador independiente. Semilla, progreso, cancelación y comparación.
F13 solo sale cuando su convención está documentada y probada.

Salida: garantías exactas en dominios pequeños y presupuestos computacionales
definidos; en dominios grandes, separación explícita entre certificado y estimación.
Benchmarks publicados; sin exigir generar todas las apuestas como objetos Python.

### Fase 3 — Predicción y evaluación económica

Datos autorizados, modelo calibrado 1/X/2 y Pleno, comparación de fuentes,
estimador de premios, F17, Monte Carlo, sensibilidad y backtesting temporal.
Generador explicable combina objetivos de probabilidad/cobertura; riesgo económico
solo disponible cuando el estimador está validado. No elevar riesgo para agotar dinero.

Salida: resultados frente a baseline fuera de muestra, parámetros/limitaciones
publicados, pruebas de calibración y economía. Si el modelo no mejora o no hay
datos suficientes, conservar baseline etiquetado y no afirmar mejora predictiva.

### Fase 4 — Taller y ecosistema

Herramientas avanzadas de archivos, PDF, Plenos variables, peñas, reparto e informes.
QR/ASD únicamente tras resolver especificación y validación correspondiente.
Auditoría y límites de gasto completos. Sin dependencia de Android.

Dependencias principales: M01/M02/M04 → M03/M05 → M06/M07 → M08/M10;
M01/M02/M12 → M09; M15 atraviesa todas las fases. M13/M14 necesitan apuestas,
reglas y precios estables, no necesariamente un modelo predictivo.

## 10. Pruebas de aceptación y puerta de publicación

| ID | Prueba | Resultado exigido |
| --- | --- | --- |
| T01 | Base 1X × 1 × 1X2, y 14 triples | 6 columnas en ejemplo; 4.782.969 IDs únicos en universo |
| T02 | Migración, cambio de jornada/temporada y reinicio | Sin pérdida ni reasignación de apuestas; consulta no permite edición |
| T03 | Cobertura/ajustes 0–10 y bloqueos | Reglas documentadas, 3456 en nivel 10 sin bloqueos; bloqueos no cambian |
| T04 | Fuentes cruzadas, inválidas y falta de histórico | Rechazo de jornada/temporada errónea; público no se etiqueta como deportivo |
| T05 | Cada filtro, extremos y composición IF/reservas | Comparación contra enumeración de referencia; intervalos inclusivos explícitos |
| T06 | Reducción y presupuesto repetido | Solo origen, coste ≤ presupuesto, sin duplicados accidentales; original conservado |
| T07 | Garantías en universos de 2–6 partidos | Igualdad con fuerza bruta, contraejemplo cuando falla; muestra no se llama garantía |
| T08 | Probabilidad de unión y cantidades | Sin sumar eventos solapados ni repetidos; cantidades sí afectan coste/premios |
| T09 | PRE con campo de jornada pegado a acertantes | Jornada y premios correctos por campo fijo, no prefijo numérico ilimitado |
| T10 | 14 + Pleno, pendientes y escrutinio ausente | Acumular conceptos aplicables; pendientes no son X; sin premio definitivo inventado |
| T11 | Simulación con igual semilla y escenarios | Repetibilidad con versiones fijadas y comparación pareada |
| T12 | TXT/JSON/XML, P15, repetidos, union/resta/división | Round-trip, cantidades preservadas y errores explícitos; exportación sin recortes |
| T13 | Modelos históricos | Corte temporal, sin fuga, calibración y métricas de prueba separadas |
| T14 | Reparto de peña | Suma exacta en céntimos y desempate reproducible, incluso aportaciones desiguales |
| T15 | UI pequeña/escalada y refresco idéntico | Botones accesibles, sin recorte ni parpadeo, selección/scroll preservados |
| T16 | Fallos de red, cancelación y recuperación | Caché anterior conservada, mejor solución completa, sin compras automáticas |
| T17 | Publicación PC | Tests, paquetes Linux/Windows y paridad; ningún archivo Android modificado |

Pruebas unitarias del dominio, propiedades y exhaustivas en dominios pequeños;
integración con proveedores simulados y paquetes reales congelados; pruebas GUI
con Qt y pruebas manuales en equipos de referencia. No hacer pagos reales para
comprobar exportaciones. Las pruebas no sobrescriben los pronósticos del usuario.

Toda entrega incluye matriz implementado/pendiente, benchmarks relevantes,
migraciones ensayadas, rollback de instalación y notas de limitaciones. Sincronizar
GitHub tras las mejoras usando rutas explícitas, excluyendo TXT personales,
base de datos, credenciales y copias del usuario.

## 11. Reglas oficiales y elementos condicionados

Consultado el 9/10/2026: la ayuda de SELAE describe 14 signos, Pleno 0/1/2/M,
55 % de recaudación para premios y acceso a normas. El PDF enlazado por esa
ayuda está fechado en octubre de 2019 y recoge precio de 0,75 € y reparto por
categorías. Es una referencia publicada por SELAE, no una API ni autorización
para descargar/sellar; antes de distribuir comprobar cambios normativos y reglas
del canal de validación. Precio, mínimos, cierre, categorías y botes deben ser
versionados por vigencia, no constantes perpetuas.
[Ayuda de SELAE](https://www.loteriasyapuestas.es/es/centro-de-ayuda/como-se-juega/como-jugar-a-la-quiniela),
[normas enlazadas](https://www.loteriasyapuestas.es/f/loterias/documentos/normativa/Normativa%20de%20los%20juegos/Normas_de_la_Quiniela_y_Elige8_Octubre_2019.pdf).

Fuentes públicas ya utilizadas por la base no equivalen a contratos de API ni
licencias de redistribución. Comprobar autorización, límites, identidad de datos
y condiciones de cada proveedor. No inventar acceso SELAE, Betfair u otras casas
ni eludir credenciales o restricciones. Integraciones que requieran una cuenta,
especificación o permiso exclusivo quedan bloqueadas **solo en ese adaptador**;
el resto del producto sigue funcionando con datos locales o fuentes disponibles.

No implementar algoritmos propietarios a partir de sus nombres. Definir métodos
propios, ejemplos y pruebas. IA, rentabilidad y QR se anuncian únicamente cuando
sus funciones y limitaciones estén verificadas.
