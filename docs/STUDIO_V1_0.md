# Quiniela AI Studio v1.0.1

Entrega solicitada inicialmente como v0.1.14; el usuario cambió el número a
v1.0.0. Es una ampliación del proyecto existente, no una nueva aplicación.
No se modifican Android, archivos personales ni esquema/hashes anteriores.

La actualización 1.0.1 añade la elección de quiniela al arrancar, el boleto de
ancho fijo con el formato clásico de tabla, más espacio para los marcadores
de Aciertos e Inicio sin crear ejemplos. Conserva el motor y los límites de 1.0.0.

## Uso

Linux Mint/Python 3.11+: `./run_studio.sh`. Conserva el icono de escritorio.
Windows: `run_studio.bat`; código portable, ejecución nativa aún no comprobada.

El boleto conserva su ancho y la posición de sus casillas al ampliar la ventana.
Muestra partido, hora y porcentajes junto a 1/X/2 en filas alternas. **Modelo %**
muestra la fuente deportiva guardada; **Jugado %** muestra popularidad. Al
cambiar la fuente se actualiza la columna. Los datos ausentes quedan señalados;
no se sustituyen por un modelo inventado. El Pleno conserva equipos, parejas
múltiples, porcentajes y modo manual/automático en un bloque compacto.
En Aciertos, el área superior muestra los 14 partidos y el Pleno; la lista de
apuestas queda más pequeña debajo. Puedes ajustar el separador entre ambas.
En pantallas de poca altura las tablas permiten desplazamiento.

Al arrancar, **Sí, continuar** abre la última quiniela normal o reducida sin
crear versiones nuevas. **No, empezar una nueva** crea una normal de la jornada
actual; la anterior permanece en Mis Sistemas. Si no hay datos de una jornada
actual editable, la app los descarga en segundo plano y crea el boleto al
terminar. Si falla la descarga, avisa y no abre la anterior ni inventa una
jornada actual. En un perfil que solo contiene demo, la nueva es ficticia y
sigue señalizada. Sin quinielas anteriores no aparece la pregunta.

1. Normal/Reducidas siguen separadas. El Pleno inicia en **Manual**. **Automático
   según fuente** permite que las barras seleccionen goles. **Diversificado**
   permite marcar varias parejas manualmente; se multiplican las apuestas, no
   se reasignan silenciosamente goles. TuLotero las separa por Pleno común.
2. Conserva el editor de condiciones. En Optimizar introduce euros y objetivo.
   Se recupera el desarrollo de origen y se reaplican las condiciones activas;
   aumentar el presupuesto no depende de haber recortado una versión anterior.
3. **Optimizar mis apuestas** trabaja en segundo plano y comunica cantidades
   procesadas. La propuesta conserva cada Pleno. Revisa coste, remanente,
   cobertura, comparación y contribuciones antes de **Aplicar selección**.
   Cerrar sin aplicar conserva las apuestas. El progreso y **Cancelar optimización**
   están en esa misma pantalla. Los parámetros avanzados se muestran en el área
   desplazable, sin sacar los botones fuera de una pantalla de 1024×768.
   Los cálculos quedan en auditoría, también si se cancelan o fallan.
4. En Análisis puedes verificar cobertura por separado o abrir el modelo de las
   16 parejas del Pleno. Este modelo utiliza marginales y una hipótesis explícita
   de independencia entre goles; no es un modelo conjunto calibrado.
5. **TuLotero** agrupa apuestas existentes sin cambiarlas. Perfil publicado
   consultado 13/10/2026: 2–8 sencillas por boleto y Pleno común. Configurar otro
   mínimo/máximo crea un perfil personalizado cuya compatibilidad no se afirma.
   Grupos imposibles muestran un error: no se inventan apuestas ni goles.
   TXT original, TXT agrupado y CSV se validan mediante relectura exacta.
   La tabla permite introducir las apuestas manualmente. No hay importación
   automática documentada, envío ni pago. Demo no abre la web de juego.

## Motor y objetivos originales

Antes, v0.1.13 ordenaba por probabilidad de 14 (o lexicográficamente si faltaba)
y consumía el presupuesto incluso con cantidades repetidas. No analizaba la
ganancia marginal, cobertura ni diversidad. La función antigua queda como
referencia de regresión, no como optimizador de la interfaz nueva.

El nuevo motor recibe candidatas, base/universo, restricciones, precio congelado,
presupuesto, fuente deportiva, popularidad opcional, Plenos, objetivo, semilla y
tiempo. Elimina duplicados exactos para seleccionar cartera; no altera los
archivos originales ni multiplica premios. Probabilidades por logaritmos y
modelo de independencia entre encuentros. El normalizador acepta filas que
suman 1 o 100 (redondeo ±1%); rechaza valores no finitos/negativos. La utilidad
para cuotas retira margen proporcionalmente, método aproximado documentado.
El ranking utiliza logaritmos, también para las marginales del Pleno. El objetivo
de masa se reescala por una constante común para evitar subdesbordamiento.
Si la masa absoluta no es representable como float, aparece un aviso y se
conserva `probability_mass_log` en el informe; el cero mostrado no altera la
selección. `objective_score` de Máxima probabilidad usa esta escala relativa,
no euros ni probabilidad absoluta.

- **Automático:** 0,45 cobertura 13+ + 0,25 cobertura 12+ + 0,25 masa exacta
  relativa a todas las candidatas + 0,05 distancia media/14. Usa cobertura
  ponderada si existe masa deportiva válida; uniforme si no. Son pesos de
  objetivo, no probabilidades, garantías ni rentabilidad.
- **Máxima probabilidad:** masa de eventos exactos distintos. Ordenación
  certificada solo para objetivo aditivo sin restricciones adicionales por
  grupo. Sin modelo de Pleno cuenta eventos de 14 únicos; con la opción explícita
  de independencia de goles cuenta parejas completas. Si faltan probabilidades,
  este objetivo se rechaza, no usa popularidad como sustituto.
- **Máxima cobertura:** 0,7 cobertura 13+ + 0,3 cobertura 12+.
- **Valor esperado:** desactivado; faltan recaudación, reparto y un modelo fiable
  de acertantes. No se presenta popularidad ni p/q como ROI real.

Universos pequeños: enumeración de todos los subconjuntos de 1 a K, solo si el
coste estimado no supera 20.000 subconjuntos/5 millones de evaluaciones de
aciertos. Se certifica optimalidad únicamente al completar la búsqueda.
Otros: greedy por ganancia marginal y mejora por intercambio; canal con mínimo
por Pleno añade bloques válidos. Cartera inicial viable de respaldo si expira el
tiempo. Sin afirmación de óptimo global. Los universos grandes tienen pool de
candidatas por probabilidad/muestreo y escenarios uniformes reproducibles.
Matriz `array('B')`, caché por columna compartida entre Plenos, sin dependencias
numéricas pesadas. Límites configurados: 256 candidatas/2.048 escenarios por
defecto; se ajustan escenarios para limitar verificaciones a ~2 millones de
pares. Un muestreo pequeño puede tener incertidumbre considerable.

El tiempo máximo limita **la búsqueda**; preparación de datos y verificación
independiente de la propuesta/referencias pueden alargar el tiempo total.
Todas las fases permiten cancelar. No se escribe una selección parcial al cancelar.

## Cobertura y garantías

El verificador calcula directamente coincidencias contra todas las columnas
elegidas, sin reutilizar la matriz del optimizador. Cobertura 14/13+/12+/11+/10+
uniforme y ponderada normalizada **dentro del universo indicado**. Base completa
incluye resultados descartados; candidatas restringidas es un universo distinto.
En muestreo se utilizan pesos de importancia y se muestra el tamaño efectivo;
se informa mínimo observado, nunca garantía. La probabilidad absoluta de eventos
exactos se presenta aparte: no es el porcentaje condicional de cobertura.
Editar signos/goles invalida los informes de cobertura de la versión actual.
Restaurar el desarrollo retira el informe de la selección optimizada anterior.
Ambas operaciones conservan las versiones históricas y permiten verificar de nuevo.

En búsqueda exhaustiva las puntuaciones se comparan sin un umbral absoluto que
pudiera ocultar diferencias reales cuando las probabilidades son muy pequeñas.
Los cálculos usan coma flotante; la certificación corresponde al objetivo/modelo
calculado, no demuestra que el modelo prediga la jornada real.

Las seis modalidades siguen publicadas por SELAE y remiten al BOE 2009. Matrices
ya transcritas se reutilizan sin inventar otras. Cada generación en Reducidas
invoca el verificador sobre las apuestas reales. Reducción 3: 3 dobles + 3 triples,
216 escenarios, 24 columnas; mínimo verificado 13 dentro de esa base. Esto NO
garantiza acertar la base en la jornada, el Pleno o un premio económico. Si se
recorta una reducida por presupuesto, la cobertura se vuelve a calcular; no se
conserva automáticamente la garantía original.

Fuentes de referencia:
- [SELAE: modalidades](https://www.loteriasyapuestas.es/es/paginas-informativas/quinielas-reducidas-maximiza-tus-posibilidades).
- [BOE: matrices](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2009-12204).
- [TuLotero: instrucciones y restricciones](https://tulotero.es/jugar-quiniela/).

## Auditoría y comparaciones

Registro local: UUID, fecha, jornada, hash/revisión, versión del algoritmo,
configuración, fuente/instantáneas, semilla, presupuesto, candidatas/descartadas,
selección, coste/remanente, métricas, tiempo, advertencias y aportación marginal.
Informe JSON exportable. Guardar informe o archivo no valida apuestas.
El inicio y el resultado comparten ID. Cancelación/error conservan configuración,
jornada y causa, pero no inventan métricas de una selección que no se completó.

Referencias: entrada recortada determinísticamente, aleatoria con semilla y más
probables (referencia v0.1.13). Mismo universo, modelo, techo de presupuesto,
restricciones y la misma cardinalidad. Un DP de cuotas por Pleno evita quedar
atrapado en un grupo inicial de dos apuestas cuando la referencia requiere tres.
Con mínimo por Pleno, las referencias priorizan los grupos según su primera
aparición y luego las apuestas del grupo según el orden de referencia; no son
óptimos económicos. Sin restricciones, mantienen el orden global original.
El universo completo «antes» puede costar más y no se vende como comparación a
igual precio. Mejorar cobertura no implica mejorar la masa de 14 ni dinero.

## Pruebas y límites

`./run_studio.sh --self-check`, `.venv-studio/bin/python -m pytest -q`,
`RUN_PC_GUI_TESTS=1 python3 -m unittest discover -q`, arranque `--smoke-test`.
Fixtures sintéticos explícitos. Los dos TXT reales pedidos se usan si existen
localmente; no se copian a Git ni se inventan si faltan.

Pendientes: IA entrenada/calibración, modelo económico fiable/ROI, solver externo,
garantías exhaustivas de universos gigantes, prueba nativa Windows y validación
real externa del canal. Los formatos agrupados son propios, no formatos oficiales
de importación TuLotero. Ningún cálculo aquí garantiza ganar dinero.
