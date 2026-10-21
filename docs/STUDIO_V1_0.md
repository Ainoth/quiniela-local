## Quiniela AI Studio 1.0.27 — premios en Aciertos

Aciertos lee el escrutinio definitivo PRE guardado de la jornada y muestra un
panel dorado cuando las apuestas del sistema suman un premio positivo. El
desglose identifica la categoría, la cantidad de apuestas, el importe unitario
y el subtotal. Con reparto cero presenta un estado discreto; sin PRE definitivo
solo muestra aciertos. El importe calculado no prueba que un boleto se haya
validado o pagado. Véase [plan y pruebas](planes/ESCRUTINIO_PREMIOS_V1_0_27.md).

## Quiniela AI Studio 1.0.26 — SSeguidos sin fondo ornamental

Cuenta conserva Manual/Azar/Automática. Manual reconstruye la distribución clásica de matriz V/X/2, Figuras, distribución histórica por temporada, FILTROS y cuadro de sumas en tres bloques compactos. Los porcentajes por temporada son observados; la selección está sincronizada con Automática. El filtro de distancia entre equis reutiliza la regla existente. Las casillas de reserva/media quedan inhabilitadas mientras su semántica no esté definida. Véase [plan y decisiones](planes/CUENTA_PANEL_V1_0_25.md) y [captura comparativa](validacion_visual/cuenta_v1_0_25/comparacion_lado_a_lado.png).

# Quiniela AI Studio v1.0.29

## Mis Sistemas v1.0.23

La lista puede abrir una reducción de cobertura guardada por Hermes, Atenea o
Artemisa. El resumen inferior acepta informes con verificador anidado o plano;
si una copia histórica no contiene un estado verificable, muestra «cobertura
aún no verificada» sin impedir abrir la quiniela. Las apuestas guardadas y el
informe original no se modifican.

## Réplica visual de Reducciones v1.0.22

Se aplicaron la guía de SSeguidos, el prompt visual v2 y las referencias del
ZIP local. SSeguidos, FSSeguidos e Interrupciones comparten un lienzo azul
ornamental con temporada/jornada ovaladas, pestañas compactas, paneles
estrechos y listas blancas. Interrupciones tiene dos vistas internas:
**Interrupciones** conserva la matriz de cambios y las figuras; **Distancias**
contiene cuatro filtros independientes para `1/X/2/V`. Cuenta y Grupo reciben
la misma piel visual sin reclamar fidelidad exacta ante la falta de imagen
original inequívoca. Véanse el [plan](planes/REPLICA_VISUAL_REDUCCIONES_V1_0_22.md)
y la [comparación de capturas](validacion_visual/reducciones_v1_0_22/README.md).

La distancia de cada signo es la mayor diferencia de posiciones consecutivas
entre sus apariciones en los catorce partidos; con cero o una aparición es 0.
Esta convención es original y comprobada por enumeración, no una atribución
al algoritmo interno de WIN1X2.

## Interrupciones y Distancias v1.0.21

Reducciones incorpora **Interrupciones** con modos Manual, Azar y Automática.
La matriz izquierda permite seleccionar pares de total de cambios y máxima
racha de cambios consecutivos; el panel **Distancias** filtra particiones
exactas como `3-2-1-1`. Cada panel tiene un Aplicar independiente y su propio
Marca todos / Inicializar. La pestaña exterior empieza desactivada; encenderla
es necesario para que intervenga cualquiera de los dos filtros.

En una columna de 14 signos se examinan sus 13 transiciones. Para
`11X21221XX121X`, el total es 10 y las rachas máximas de transiciones forman
`4-4-2`. El Pleno al 15 queda fuera. La asociación provisional de la columna
«Seguidas» con la mayor racha consecutiva está documentada en
`docs/planes/Interrupciones_V1_0_21.md`; no se presenta como equivalencia
certificada con el programa antiguo.

Automática usa resultados finales del histórico integrado y temporada
seleccionada; Azar guarda la semilla. Los riesgos describen la cobertura
muestral solicitada, no probabilidades de premio ni predicciones.

## Figuras de Signos Seguidos v1.0.20

Reducciones suma la subpestaña **FSSeguidos**, junto a Cuenta, SSeguidos y
Grupo. Presenta Manual, Azar y Automática; cada método comparte cuatro paneles
compactos `1/X/2/V`, listas de particiones multiselección y un total editable.
Para siete variantes, por ejemplo, `3-2-1-1` exige rachas máximas de 3, 2, 1
y 1. La base actual limita las figuras disponibles; X/2 se agrupan únicamente
en V y el Pleno queda fuera.

Cada signo tiene su propio botón Aplicar y la pestaña FSSeguidos otro cuadrado
de activación, ambos apagados por defecto. Las selecciones sobreviven al cambio
de total y al desactivar filtros; se aplica solo el total visible. Azar usa una
semilla reproducible. Automática cuenta resultados finales reales del histórico
integrado. SSeguidos sigue siendo una reducción separada de límites de racha y
frecuencias.

La primera aplicación de filtros sobre un desarrollo nuevo y sin condiciones
no crea una revisión vacía. Esto mantiene fuera del estado guardado las casillas
de funciones que todavía no están publicadas.

## SSeguidos según la guía Qt v1.0.19

Reducciones conserva las subpestañas visibles Cuenta, SSeguidos, Grupo y ahora
FSSeguidos. SSeguidos
ofrece **Manual**, **Azar** y **Automática** en cuatro paneles compactos `1`,
`X`, `2` y `V`. Los tres modos comparten el mismo estado. Manual admite límites
opcionales de racha máxima, cantidades exactas de rachas por longitud y figuras
como particiones de rachas máximas. Las frecuencias y figuras posibles se
calculan desde la base actual.

Automática presenta temporadas reales del histórico integrado y conserva
perfiles conjuntos por riesgo descriptivo; no predice. Azar muestrea la base
con una semilla reproducible y no depende de temporadas. `V` agrupa X y 2; el
Pleno queda excluido. Un campo sin número se conserva vacío y distinto de 0.
El cuadrado externo de SSeguidos sigue apagado por defecto: al activarlo aplica
la reducción; al apagarlo conserva los ajustes y no los usa. Las reglas
serializadas con el identificador Racha se mantienen para quinielas existentes.

La acción explícita **Aplicar** persiste cambios de reglas incluso cuando la
lista resultante de apuestas no cambia.

## SSeguidos automático y compacto v1.0.18

Reducciones conserva Cuenta, SSeguidos y Grupo. SSeguidos presenta únicamente
la modalidad **Automática**: temporadas, riesgo, cálculo y cuatro paneles
estrechos de `1`, `X`, `2` y `V` que agrupan límites, recuentos históricos y
figuras exactas. Cuenta conserva Manual/Azar/Automática y su cuadrícula propia.
Los antiguos controles internos de Racha permanecen disponibles para cargar y
guardar configuraciones anteriores, sin mostrarse como páginas ni destruir los
editores usados por la aplicación. La matriz Cuenta acompaña la página de cada
método y permanece debajo de sus controles. El filtro sigue siendo el mismo de Racha,
conserva la activación externa apagada por defecto y solo se aplica cuando esa
pestaña está activa. Requisito RF-UX-014.

## SSeguidos compacto v1.0.17

Reducciones muestra **Cuenta**, **SSeguidos** y **Grupo**. SSeguidos publica
con ese nombre la condición consecutiva que antes se mostraba como Racha; usa
el mismo filtro, índice y datos guardados, por lo que no crea una reducción
duplicada ni pierde configuraciones anteriores. Tiene modos Manual, Azar y
Automática. Manual permite fijar el intervalo posible de la racha máxima de
`1`, `X`, `2` y `V` según la base, con selección exacta adicional en la
cuadrícula y límites de veces para figuras máximas. Los datos históricos y el Pleno al 15 conservan la
semántica ya documentada. Requisitos: RF-UX-013 y RF-FIL-019.

## Respaldo de marcador ESPN v1.0.16

Si Dataradar no conecta, no devuelve una jornada interpretable o deja sin
marcador partidos cuyo horario ya pasó, Aciertos consulta el marcador público
ESPN en Primera, Segunda y Liga F. Una respuesta primaria con equipos distintos se
rechaza. Los resultados alternativos se asignan solo cuando
coinciden la fecha y los dos equipos en el orden local/visitante. Las filas sin
cobertura se mantienen en blanco; si ambas fuentes tienen datos, se conservan
los marcadores principales y se completan solo los vacíos. Los ceros de partidos futuros no son resultados.
La columna de estado y la línea de consulta indican la fuente. Después de una
respuesta de ESPN, la misma fuente se usa en los siguientes refrescos de esa
jornada.

## Estados de Aciertos según el horario v1.0.15

Cuando no se recibe el marcador, Aciertos identifica los partidos con hora
futura como «Por comenzar» y los de hora pasada como «Sin resultado». La hora
programada no se interpreta como marcador ni como confirmación de que el
encuentro terminó. La pantalla también separa la falta de datos de la opción
«Marcador automático» desactivada.

## Mejoras de interfaz y marcador v1.0.14

Normal es ahora la primera pestaña y sustituye al panel redundante Inicio. En
Reducciones solo se muestran Cuenta, SSeguidos y Grupo; las páginas reservadas
siguen en el proyecto para desarrollarse después. La importación opcional de
resultados históricos se encuentra en Configuración, mientras que el histórico
incluido se carga automáticamente. Aciertos mantiene visibles los partidos aun
sin conexión y reintenta una vez los fallos transitorios del proveedor.

## TXT clásico v1.0.13

Guardar apuestas genera texto plano sin cabecera: una línea por apuesta, con
los 14 signos 1/X/2 y, al final, los dos signos del Pleno (local y visitante).
Cada línea tiene 16 caracteres y las copias se repiten. La ventana de guardado
indica esta estructura y el importador puede releerla.

## Histórico y asignación de base v1.0.12

Normal permite alternar entre **Manual** (indicar cantidades de dobles y
triples; el sistema elige los partidos según la matriz 1/X/2) y **Automática**
(el sistema elige también las cantidades para maximizar la probabilidad
conjunta sin superar el máximo de columnas, 6 por defecto). La decisión
automática usa programación dinámica exacta y desempata por menos columnas y
anchuras en orden fijo/doble/triple. Las filas bloqueadas conservan sus signos
y cuentan dentro del límite. La matriz ya no permite asignar tipos por partido.
El informe `normal_base_generation` registra cantidades, coste, probabilidad
conjunta y decisión por encuentro.

Las subpestañas de Reducciones se inicializan apagadas, incluidas las
quinielas antiguas cuyos checks activos eran valores predeterminados. Al
activar una pestaña, sus reglas entran en la aplicación del filtro; apagarla
las excluye sin borrar configuración. La elección explícita queda guardada por
sistema.

El histórico `data/historico_resultados_quiniela.csv` se empaqueta en la
aplicación y se copia a su configuración la primera vez que arranca, sin diálogo
de importación. Contiene resultados 1/X/2 de 2.609 jornadas y marcador de los 15
partidos en 880 jornadas, con signos verificados. La cuadrícula compacta Cuenta
y SSeguidos integra frecuencias observadas en los botones de valor blancos/verdes.
Las filas sin marcador publicado se mantienen vacías; consulta la nota de
[procedencia](../data/ORIGEN_HISTORICO_QUINIELA.txt).

Entrega solicitada inicialmente como v0.1.14; el usuario cambió el número a
v1.0.0. Es una ampliación del proyecto existente, no una nueva aplicación.
No se modifican Android, archivos personales ni esquema/hashes anteriores.

## Cuenta y Racha v1.0.10

Las subpestañas **Cuenta** y **Racha** amplían los filtros ya existentes; no se
crean pestañas paralelas ni se sustituye **Cambio**. En cada una, el método
Manual/Azar/Automática se elige en sus subpestañas y comparte la cuadrícula de
valores. Los recuadros blancos/verdes no usan ticks. El cuadrado junto a cada
subpestaña activa o suspende sus condiciones sin borrar la configuración.

Cuenta cuenta V=X+2, X y 2 en los 14 partidos. Racha mide longitudes máximas y
frecuencias de figuras exactas no solapadas; V agrupa X y 2. Es una convención
propia, no una afirmación de equivalencia con WIN1X2. Azar usa una semilla y
conteos observados en el desarrollo de origen. Automática importa resultados
finales con temporada, jornada y `results14` de 14 signos desde CSV/JSON y
selecciona perfiles conjuntos según su frecuencia histórica. No predice ni
garantiza resultados; los archivos marcados como demostración se rechazan.
Consulta [el plan funcional](planes/VARIANTES_RACHAS.md).

La matriz de valores se presenta en paneles estrechos alineados, evitando que
las casillas se estiren por todo el ancho de la pantalla. La selección de años
usa una cuadrícula vertical compacta, ordenada de más reciente a más antigua,
con acciones **Todas** y **Ninguna** y un resumen del número de temporadas y
jornadas importadas. La lista se desplaza verticalmente y conserva el estado
de cada temporada al importar más datos.

La actualización 1.0.1 añade la elección de quiniela al arrancar, el boleto de
ancho fijo con el formato clásico de tabla, más espacio para los marcadores
de Aciertos e Inicio sin crear ejemplos. Conserva el motor y los límites de 1.0.0.

La corrección 1.0.2 restaura el icono de Quiniela Local en ventanas, diálogos
y barra de tareas. La imagen se distribuye dentro del paquete Qt, también
al instalar una wheel fuera del repositorio. En Linux, la identidad de ventana
y `StartupWMClass` son `quiniela-ai-studio`; la entrada de menú puede llamarse
`quiniela-ai-studio.desktop`. Cierra y vuelve a abrir para ver el cambio.

## Generadores gráficos de Normal v1.0.8

**Quiniela Base Automática** permite revisar y editar la matriz 1/X/2,
establecer cantidades exactas de triples y dobles, normalizar filas de forma
explícita y rellenar la base maximizando la masa probabilística retenida.
Guardar/Cargar conserva una matriz por jornada. Las ponderaciones de
Clasificación, 5 últimas jornadas e Historial solo se aplican con matrices
verificadas importadas para esos factores; el proyecto aún no tiene feeds
estructurados de esos datos.

Debajo, cinco filas iniciales (ampliables) ejecutan acciones independientes
por fuente: top-K exacto, base triples/dobles o fichero de columnas local.
`Desde` y `Hasta` son inclusivos y empiezan en posición 1; sin rango se usa
`Núm. Colum.`. Las terminaciones filtran la última cifra de la posición antes
de descartes y sin renumerar. Los empates se resuelven por orden de signos
1 < X < 2, de izquierda a derecha. C.P. es el producto de las 14 probabilidades
calculado en logaritmos, con mínimo y máximo ajustables y supuesto de
independencia. Las acciones se
combinan como concatenación con duplicados, unión exacta o intersección y se
exportan en TXT, CSV o JSON mediante escritura atómica. Se importan matrices
CSV/TXT/JSON validadas y columnas abiertas con 14 signos; no se adivinan
formatos propietarios.

Se conserva la integración ya existente de Mercado y Popularidad. LAE,
Betfair independiente, clasificación, forma, historial y WIN1X2 necesitan una
fuente importada o un proveedor integrado; no se simulan datos. La auditoría
registra criterios, jornada, procedencia, rangos y resultados.

## Reducciones v1.0.7

La sección **Reducciones** presenta 17 pestañas internas compactas basadas en
las familias del manual WIN1X2. Los controles existentes de recuento, rachas,
cambios, coincidencias, grupos y tolerancia viven en una única pestaña cada uno;
no se repiten en Optimizar. Los grupos muestran números de partido y botones
1/X/2; los equipos siguen visibles en el boleto fijo. Referencias, patrones y
columnas se eligen en matrices visuales de botones 1/X/2 y una lista. Los límites
numéricos se ajustan con flechas; no hay que escribir pronósticos en campos.
La vista de Grupos presenta un tablero azul enmarcado, cabeceras para cada
grupo y controles 1/X/2 compactos, siguiendo la composición visual del manual.
Las etiquetas de las pestañas son cortas y conservan su explicación completa
en la ayuda emergente.

Hermes, Atenea y Artemisa son modos del motor propio `athena-cover-1.0.0`:
selección greedy, mejora por intercambios y búsqueda exacta acotada. Todas
parten de apuestas elegibles del desarrollo activo y aplican un presupuesto
propio para esa cobertura. La propuesta se calcula en segundo plano, se puede
cancelar y se guarda como sistema nuevo, conservando el original. La cobertura
se verifica con un recorrido independiente; una muestra se identifica como
estimación y la garantía, si existe, se limita al universo enumerado y a signos
1/X/2. El Pleno se conserva por apuesta pero no forma parte de esta garantía.

Los patrones de parejas a quintetos cuentan ventanas consecutivas solapadas;
frecuencias y valoraciones usan referencias/snapshots explícitos. Son reglas
originales y no reproducen exactamente WIN1X2. **Columnas** permite sumar los
aciertos máximos de varios grupos; **Relacionados** limita la diferencia entre
dos grupos. **Si… entonces** permite una
implicación entre dos grupos con intervalos independientes; se combina con el
contador compartido de condiciones incumplidas. No se admiten expresiones
condicionales arbitrarias. Los filtros
experimentales siguen requiriendo revisión antes de usarse con dinero real.

## Uso

**Condiciones avanzadas**, antes de Optimizar, permite crear hasta ocho grupos
en columnas compactas visibles simultáneamente, con desplazamiento horizontal
cuando no caben. Cada columna muestra los números de partido; los equipos ya
figuran en el boleto base. Pulsa los signos 1/X/2 que aceptas. Puedes
marcar más de uno; un partido sin marcas no participa en el grupo. Indica el
mínimo y máximo de coincidencias. Opcionalmente compara la suma o diferencia de
dos grupos y permite incumplir cierto número de reglas. El panel informa de las
apuestas conservadas y qué reglas incumplen apuestas del desarrollo original;
los recuentos pueden solaparse. Las condiciones se guardan y Optimizar las
aplica al desarrollo de origen. No son una predicción ni una garantía.

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
