# Cambios

## 1.0.29 — Escrutinio y desglose por categoría

- RF-ESC-014: al cambiar de quiniela se limpian inmediatamente las tarjetas
  del sistema anterior. Una segunda tarjeta muestra, por categoría, los
  acertantes e importes unitarios publicados junto a tus apuestas, subtotal y
  total calculado. El desglose aparece también con total cero; el aviso dorado
  solo aparece con premio positivo.
- RF-UX-022: «Aciertos» pasa a llamarse «Escrutinio» en la pestaña, título y
  acceso desde Inicio, sin cambiar su posición interna.

## 1.0.28 — reparto publicado cuando el PRE sigue provisional

- RF-ESC-013: Aciertos consulta en segundo plano un espejo público del
  escrutinio de SELAE cuando los 15 marcadores son finales y el PRE local aún
  no contiene reparto. Valida fecha, temporada, jornada, los 15 equipos y
  marcadores y las seis categorías antes de calcular un importe.
- El escrutinio validado se conserva para uso sin conexión. La procedencia se
  indica en la tarjeta; con fuente ausente o contradictoria se mantienen solo
  los aciertos, sin anunciar dinero.
- Para la jornada 14 de 2026-27 se verificó el reparto publicado: 11 aciertos
  = 2,22 € por apuesta; 10 aciertos = 0,00 €.

## 1.0.27 — premios en Aciertos

- RF-ESC-012: Aciertos lee al abrir el PRE definitivo guardado para la jornada
  y muestra un panel destacado únicamente cuando las apuestas guardadas suman
  un premio positivo.
- El panel detalla categoría, número de apuestas, premio unitario y subtotal;
  las copias y el Pleno se cuentan conforme al escrutador existente.
- Resultado parcial, PRE ausente/incompleto o equipos distintos no anuncian
  dinero. Un reparto publicado sin premios se informa con un texto discreto.
- Se recuerda que el cálculo sobre apuestas guardadas no acredita un boleto
  sellado ni un pago.
- Capturas reproducibles con datos sintéticos en
  `docs/validacion_visual/escrutinio_premios_v1_0_27.png` y
  `docs/validacion_visual/escrutinio_premios_compacto_v1_0_27.png`.

## 1.0.26 — SSeguidos compacto y sin fondo ornamental

- RF-UX-021: SSeguidos usa el mismo fondo plano que Cuenta; el selector de
  temporadas se muestra en dos columnas y ocupa menos alto.
- Se conserva la estructura Manual/Azar/Automática, las estadísticas reales,
  el motor de rachas y la activación exterior apagada por defecto.
- Captura y comparación con la referencia Automática en
  `docs/validacion_visual/sseguidos_v1_0_26/`.

## 1.0.25 — reconstrucción visual de Cuenta

- RF-UX-020: Cuenta > Manual pasa a una composición compacta de tres bloques:
  matriz V/X/2 de 0–15, Figuras con botones independientes y panel derecho con
  distribución histórica por temporada, FILTROS y el resumen clásico de sumas.
- La fila 15 se presenta inhabilitada porque Cuenta opera sobre los 14 partidos.
  El selector de temporadas de la tabla queda sincronizado con Automática.
- Se conservan los filtros existentes. Las casillas de FILTROS y las celdas de
  sumas/reserva/media sin lógica definida permanecen vacías e inhabilitadas.
- Captura de Manual, referencia, composición lado a lado y superposición al 50 %
  en `docs/validacion_visual/cuenta_v1_0_25/`.

## 1.0.24 — Cuenta completa y compacta

- RF-UX-019: Cuenta reúne matriz V/X/2, perfiles conjuntos en Figuras,
  Distribución Signos, temporadas junto a esa distribución y Filtros; se quita
  el fondo ornamental solo de esta pantalla.
- RF-FIL-025: los perfiles históricos `(V, X, 2)` se aplican como condición
  conjunta. La separación entre equis usa el filtro existente y participa al
  activar Cuenta, sin duplicar su cálculo.
- El histórico se recalcula al seleccionar temporadas y presenta frecuencias
  observadas, no predicciones.
- Verificación Qt: panel, distribuciones, filtro de perfiles y distancia.

## 1.0.23 — apertura de reducciones guardadas

- RF-ARC-009: Mis Sistemas abre reducciones Hermes/Atenea/Artemisa cuyo
  informe guarda el verificador dentro de `coverage`. El pie de ventana lee
  también el formato plano de otras reducciones y no falla ante informes
  antiguos incompletos; en ese caso indica que la cobertura no está verificada.
- Prueba Qt de apertura de una reducción guardada y pruebas de los dos formatos
  de informe y del caso incompleto.

## 1.0.22 — réplica visual de Reducciones

- RF-UX-018: piel clásica compartida, cabecera ovalada de temporada/jornada,
  paneles compactos y listas blancas en SSeguidos, FSSeguidos e Interrupciones.
  Cuenta y Grupo se armonizan sin afirmar igualdad visual con WIN1X2, pues
  faltan referencias originales inequívocas.
- RF-FIL-024: la subpestaña Distancias filtra de forma independiente la
  distancia máxima entre apariciones consecutivas de 1, X, 2 o variantes.
  Menos de dos apariciones equivale a distancia 0; el Pleno queda excluido.
- Capturas finales, superposiciones y diferencias están en
  `docs/validacion_visual/reducciones_v1_0_22/`. La comparación conserva
  diferencias de ornamento, tipografía y datos de ejemplo.

## 1.0.21 — Interrupciones y Distancias

- RF-UX-017: nueva pestaña compacta **Interrupciones** con Manual, Azar y
  Automática; matriz de celdas blancas/verdes/grises y panel independiente de
  totales y figuras, con botones de selección e inicialización por panel.
- RF-FIL-023: calcula cambios solo entre los 14 signos, permite filtrar por
  total y racha máxima consecutiva, y por particiones exactas de las
  interrupciones. El ejemplo `11X21221XX121X` da 10 cambios y figura `4-4-2`.
- El histórico integrado alimenta Automática por temporadas; Azar registra su
  semilla. Ambos filtros y la pestaña exterior se conservan apagados por
  defecto. La semántica de la columna «Seguidas» es explícita y provisional.
- Verificación: DP contra enumeración, casos del manual, filtros separados,
  persistencia y cálculo con histórico integrado.

## 1.0.20 — Figuras de Signos Seguidos

- RF-UX-016: nueva subpestaña compacta **FSSeguidos**, con Manual, Azar y
  Automática, cuatro listas Qt multiselección `1/X/2/V`, total editable por
  signo, temporada/jornada y botones Aplicar blanco/verde.
- RF-FIL-022: cada selección admite particiones exactas de rachas máximas
  (por ejemplo, 7 variantes con figura `3-2-1-1`). X/2 se agrupan solo para V;
  se excluye el Pleno y se limita a figuras alcanzables en la base.
- El filtro FSSeguidos tiene activación externa propia, permanece apagado por
  defecto y persiste sus totales, figuras, riesgo, semilla y temporadas. Azar
  es reproducible; Automática usa solo resultados finales del histórico
  integrado. SSeguidos mantiene sus condiciones de racha como filtro separado.
- Verificación: filtrado exacto, persistencia, perfiles históricos reales,
  semilla determinista y control de regresión en filtro oculto.

## 1.0.19 — Signos Seguidos según la guía Qt

- RF-UX-015: SSeguidos vuelve a ofrecer **Manual, Azar y Automática** en una
  interfaz Qt compacta de cuatro paneles `1/X/2/V`. Las tres páginas comparten
  valores, riesgo y temporadas; los cuadrados no usan tics. Automática muestra
  temporadas y riesgo junto a los cuatro resúmenes, con el cálculo debajo.
- RF-FIL-021: los límites mínimo/máximo distinguen campo vacío de cero; la
  matriz acepta cantidades de rachas máximas exactas y las figuras se comparan
  como particiones no solapadas. `V` agrupa X y 2 y el Pleno queda excluido.
  Azar guarda su semilla; Automática conserva perfiles históricos conjuntos.
- Persistencia: Aplicar guarda también cambios de reglas que no alteran la
  cantidad de apuestas. Cuenta conserva sus tres modos, y activar/desactivar
  SSeguidos sigue controlando si la reducción interviene.
- Verificación: pruebas de estructura Qt, persistencia de límites vacíos,
  perfiles conjuntos y comparación exhaustiva del DP contra bases enumeradas.

## 1.0.18 — SSeguidos solo automático y compacto

- RF-UX-014: SSeguidos muestra únicamente **Automática**. Sus cuatro paneles
  `1`, `X`, `2` y `V` juntan límites, frecuencias históricas y figuras en
  columnas estrechas, siguiendo la disposición de WIN1X2. El selector de
  temporadas ocupa menos espacio.
- Cuenta mantiene intactas sus tres modalidades y su matriz; los controles
  heredados de Racha quedan ocultos sin destruirse al cerrar la página Qt,
  conservando la carga de quinielas anteriores. La matriz de Cuenta acompaña
  cada método y queda junto a sus controles, sin el hueco vertical anterior.
- La condición sigue usando la regla Racha existente, sin duplicar el filtro;
  el tab externo continúa desactivado por defecto y solo aplica al activarlo.
- Verificación: regresión Qt para Cuenta, paneles compactos, pestaña automática
  única, filtrado y persistencia.

## 1.0.17 — SSeguidos compacto

- RF-UX-013: la subpestaña de rachas se muestra como **SSeguidos**, con cuatro
  paneles compactos para `1`, `X`, `2` y `V`; los intervalos mínimo/máximo se
  limitan a las rachas posibles de la base. Cada panel ofrece
  cuadrados de valores con frecuencias históricas dentro y límites de figuras.
- Conserva las tres modalidades, las reglas y el estado persistido de Racha.
  La pestaña empieza apagada y al activarla aplica las condiciones al filtro
  real. No se crea un segundo motor ni una reducción duplicada.
- Verificación: `tests/studio/test_advanced_conditions_ui.py`, incluyendo
  filtrado min/máx y persistencia.

## 1.0.16 — Respaldo de marcador ESPN

- RF-ESC-011: si Dataradar no conecta, no devuelve una jornada interpretable
  o deja sin marcador partidos cuyo horario ya pasó, Aciertos
  consulta ESPN para Primera, Segunda y Liga F españolas. Empareja por jornada,
  fecha, local y visitante; muestra la fuente usada y deja sin marcador los
  partidos sin cobertura. Si ambas fuentes aportan resultados, conserva los
  del proveedor principal y completa solo los partidos que estaban vacíos.
  Los 0–0 de encuentros programados no se interpretan como resultados.
- Tras una primera consulta correcta, se reutiliza esa fuente en los refrescos
  de la misma jornada para evitar repetir la espera de un proveedor caído.
- Verificación: pruebas del estado programado/final, aliases de equipos,
  equipos femeninos, alternativa al proveedor principal y consulta de J14.

## 1.0.15 — Estados de Aciertos según el horario

- RF-ESC-010: cuando todavía no hay marcador descargado, Aciertos distingue los
  partidos cuyo inicio está en el futuro («Por comenzar») de aquellos cuyo
  horario ya pasó («Sin resultado»). La hora nunca se usa para inventar un
  marcador ni para afirmar que el partido terminó.
- La ausencia de datos y la desactivación del marcador automático se explican
  con mensajes separados; los fallos de conexión ya no describen toda la tabla
  como pendiente.
- Verificación: pruebas deterministas para horarios anteriores, futuros y no
  disponibles; pruebas de estados de marcador y suite de interfaz.

## 1.0.14 — Marcador más resistente y Reducciones compactas

- RF-ESC-009: se reintenta una vez una interrupción de red del proveedor del
  marcador; Aciertos mantiene las filas de los 15 partidos mientras espera y
  conserva los resultados guardados si falla la actualización.
- RF-DAT-005: el histórico integrado se identifica como carga automática; la
  importación opcional de resultados se mueve a Configuración.
- RF-UX-012: Reducciones muestra por ahora solo Cuenta, Racha y Grupo. Las otras
  páginas permanecen en el código para futuras entregas, sin aplicar condiciones
  ocultas. Normal pasa a ser la primera pestaña y se omite Inicio.
- Verificación: pruebas de reintento, importador histórico, activación de
  filtros y navegación de pestañas.

## 1.0.13 — TXT clásico de apuestas

- RF-EXP-004: TXT exporta una apuesta por línea con 14 signos 1/X/2 seguidos
  por los dos signos del Pleno, sin cabecera ni separadores; las copias se
  repiten en líneas distintas. La exportación normal y la directa comparten
  serializador y el diálogo identifica el formato.
- Verificación: líneas de 16 caracteres, secuencia, Pleno, cantidad y relectura.

## 1.0.12 — Cantidades manuales y automáticas de dobles/triples

- RF-NOR-004: Manual permite indicar cuántos triples y dobles se desean; el
  sistema elige los partidos según sus probabilidades. Automática decide también
  las cantidades para maximizar la probabilidad conjunta dentro de un límite de
  columnas configurable (6 por defecto). Se elimina la selección por partido.
- La matriz de porcentajes vuelve a ser compacta, sin columna «Tipo».
- Cuenta y Racha muestran una sola cuadrícula estrecha, con frecuencias
  históricas dentro de cada casilla blanca/verde.
- Verificación: pruebas de cantidades manuales, límite automático, bloqueos y
  estado de cuadrícula.

## 1.0.11 — Histórico integrado y asignación manual de la base

- RF-NOR-004: Normal permite elegir asignación automática de dobles/triples por
  probabilidad o asignación manual por partido (Fijo/Doble/Triple); conserva
  bloqueo, configuración por jornada y deja los signos elegidos por probabilidad.
- RF-FIL-020 / RF-DAT-004: las subpestañas de Reducciones empiezan desactivadas;
  se preservan activaciones explícitas del usuario y se migran los antiguos
  valores predeterminados activos a apagado. La cuadrícula Cuenta/Racha muestra
  frecuencias empíricas por temporadas seleccionadas.
- Se incluye el CSV histórico en el paquete de la app y se carga sin diálogo.
  Contiene 2.609 jornadas y marcadores 1–15 en 880 filas verificadas contra
  sus 14 signos; los datos ausentes se dejan vacíos. El importador conserva
  los campos opcionales `score_01`…`score_15`.
- Verificación: pruebas de asignación manual, filtros apagados/activados,
  carga del histórico empaquetado, matriz y suite de Reducciones.

## 1.0.10 — Cuenta/Racha más compactas

- RF-UX-011: sustituye las listas estiradas de valores por paneles gráficos
  estrechos; cambia el selector de temporadas horizontal por una cuadrícula
  compacta ordenada por año, con botones Todas/Ninguna y resumen de jornadas.
- Conserva los cuadrados blancos/verdes, la selección entre temporadas y el
  cálculo histórico existente. Pruebas Qt: 10 de interfaz avanzada.

## 1.0.9 — Modos gráficos en Cuenta y Racha

- RF-FIL-018 / RF-FIL-019: amplía las subpestañas existentes Cuenta y Racha;
  mantiene Cambio separado. Cuadrículas compactas de recuentos y rachas exactas,
  controles de activación cuadrados blancos/verdes, métodos Manual/Azar/
  Automática y generación azarosa reproducible sobre apuestas de origen.
- Racha cuenta figuras como rachas máximas exactas sin solape; V agrupa X y 2.
  Azar guarda semilla/riesgo. Automática importa CSV/JSON de resultados finales,
  rechaza datos marcados como demo y admite perfiles conjuntos para no separar
  categorías correlacionadas. La cobertura histórica es descriptiva, no predictiva.
- RF-UX-010: las activaciones de subpestaña y los valores se conservan por
  separado; se puede acceder a una pestaña desactivada sin borrar sus ajustes.
- Verificación: pruebas de dominio de perfiles/rachas, persistencia e interacción
  Qt. Windows nativo pendiente; requiere importar historial real para Automática.

## 1.0.8 — Generadores probabilísticos gráficos en Normal

- RF-NOR-001: tabla de 14 partidos con porcentajes 1/X/2 editables, validación,
  normalización explícita y selección exacta de fijos/dobles/triples que maximiza
  la masa probabilística retenida; incorpora los cambios al boleto abierto.
- RF-NOR-002: ponderaciones por jornada y gestor de fuentes locales CSV/TXT/JSON;
  los factores sin datos reales se muestran como no disponibles. Se conservan
  las fuentes Mercado y Popularidad y la selección previa de Normal.
- RF-NOR-003: tabla compacta de acciones con ranking exacto top-K por producto
  de probabilidades en logaritmos, rangos inclusivos, terminaciones posicionales
  1-indexadas, rango mínimo/máximo de C.P., bases triples/dobles, importación de columnas y
  concatenación/unión/intersección. Trabajo cancelable y fichero atómico TXT,
  CSV o JSON. C.P. es un modelo de independencia, no un indicador de premio.
- La matriz, ponderaciones, filas, fuentes y opciones se guardan por jornada;
  la auditoría conserva criterios, distribución, conteos y procedencia.
- Verificación: pruebas contra enumeración exhaustiva, conteo 7T/7D, 100.000
  posiciones/terminaciones, filtros de combinación, persistencia e interfaz Qt.
  Windows nativo y feeds LAE/Betfair/WIN1X2 siguen pendientes.

## 1.0.7 — Tablero de grupos inspirado en WIN1X2

- RF-UX-009: refuerza el aspecto gráfico de Reducciones con panel azul
  enmarcado, cabeceras por grupo y matriz 1/X/2 compacta; los nombres de los
  equipos siguen apareciendo solo en el boleto fijo.
- Acorta las etiquetas de las 17 pestañas y mantiene su explicación completa
  al pasar el cursor, para que los métodos se encuentren más fácilmente.
- Aclara las instrucciones de la pestaña Grupos y reduce el texto introductorio.
- Revisión visual en Linux y comprobaciones de interfaz, estilo y regresión.

## 1.0.6 — Reducciones completamente gráficas

- RF-UX-008: sustituye la escritura de referencias y patrones por matrices
  interactivas 1/X/2. Repeticiones y coincidencias muestran los 14 partidos;
  parejas, tríos, cuartetos y quintetos muestran solo las filas necesarias.
  Frecuencias permite añadir y retirar columnas desde otra matriz visual.
- RF-FIL-017: suma de aciertos máximos de varios grupos en Columnas; diferencia
  entre dos grupos en Relacionados; implicación «Si… entonces» visual, con
  intervalos por grupo y tolerancia común.
- Los límites numéricos de Reducciones se ajustan con flechas; no admiten
  escritura libre. La pestaña conserva el estilo de botones claros sobre panel
  azul y evita campos de texto libre.
- Validación con pruebas Qt, de serialización y de dominio; Windows nativo
  pendiente.

## 1.0.5 — Reducciones visuales y motor de cobertura griego

- RF-FIL-015 / RF-FIL-016 / RF-UX-007: una sección **Reducciones** con 17
  pestañas compactas inspiradas en el manual WIN1X2. Los filtros existentes se
  trasladan a su pestaña canónica para evitar controles duplicados; grupos con
  matriz numerada 1/X/2, sin repetir nombres de equipos.
- Reglas originales serializables para referencias, patrones solapados de 2–5
  partidos, frecuencia de aciertos y valoraciones con snapshot de porcentajes.
  Esquema basic-local-v5; lee versiones anteriores.
- La pestaña Si… entonces incorpora una implicación tipada entre dos grupos,
  con intervalos independientes y tolerancia compartida. Columnas no añade
  otro reductor: informa de las operaciones que ya cubren Optimizar/Atenea.
- Motor Athena Cover 1.0.0: Hermes greedy, Atenea con intercambios locales y
  Artemisa con búsqueda exacta acotada. Ejecución cancelable en segundo plano;
  guarda una copia independiente y verifica los resultados de forma separada.
  Solo declara garantía para universo enumerado por completo; el Pleno al 15
  queda explícitamente fuera de la cobertura de signos.
- La selección por presupuesto permanece en Optimizar. La reducción de
  cobertura tiene presupuesto propio porque es una operación distinta; no
  modifica el desarrollo original.
- Validación Linux; ejecución nativa Windows pendiente. Sin equivalencia
  declarada con algoritmos propietarios de WIN1X2.

## 1.0.4 — Condiciones visuales por grupos

- RF-FIL-014 / RF-UX-006: grupos visuales con casillas 1/X/2 para cada partido,
  hasta ocho grupos en columnas compactas y simultáneas, números de partido
  (los equipos ya aparecen en el boleto base) y relación elegida entre pares.
  Explicación simplificada y navegación visible antes de Optimizar.
- Los grupos aceptan uno o varios signos por partido; se migra automáticamente
  la referencia única guardada en sistemas v1.0.3. El motor conserva Plenos,
  cantidades, tolerancia y compatibilidad con reglas anteriores.
- Verificación: pruebas de migración, selección múltiple, navegación y regresión
  de UI; grupos dispuestos en fila con desplazamiento horizontal si hace falta.
- RF-DAT-004: se reconoce «Madrid CCF» del PRE local como variante de «Madrid
  CFF» de la fuente de porcentajes. Se valida la identidad de ambos equipos y
  el número de partido igual que antes; no se relaja la comprobación general.

## 1.0.3 — Condiciones avanzadas por grupos

- RF-FIL-014: nueva pestaña **Condiciones avanzadas** para comparar grupos de
  partidos con referencias 1/X/2, limitar la suma o diferencia de sus aciertos y
  permitir una cantidad configurable de condiciones incumplidas. Se combina
  con los filtros de Optimizar y actualiza en vivo apuestas/coste; conserva
  Pleno y cantidades exactas. Reglas originales, sin garantía de aciertos.
- Se guardan las condiciones en la versión de la quiniela y se recuperan al
  reabrirla; los filtros v1/v2 anteriores siguen siendo legibles.
- Verificación: 235 pruebas correctas, 2 omitidas para validación externa;
  Ruff E9/F/I correcto en los archivos revisados y `git diff --check` limpio.

## 1.0.2 — 14/10/2026 · Icono de escritorio

- RF-UX-005: ventana y diálogos Qt cargan el icono de Quiniela Local. La imagen
  queda incluida en la wheel, sin depender de la carpeta del repositorio.
  Identidad estable para agrupar ventanas en Linux y Windows; acceso directo
  local asociado mediante `StartupWMClass=quiniela-ai-studio`.
- Linux/X11: icono y clase de ventana comprobados. Windows nativo sigue pendiente.
- 11 regresiones de arranque/distribución correctas; Ruff E9/F/I y acceso directo
  válidos. Wheel/sdist construidas, icono cargado desde la wheel aislada y
  arranque nativo comprobado con perfil temporal.

## 1.0.1 — 14/10/2026 · Arranque y distribución de escritorio

- RF-UX-004: recuperado el formato clásico de tabla para la base: partido,
  hora, porcentajes y 1/X/2, filas alternas y Pleno compacto. Modelo/Jugado
  muestran la fuente seleccionada, con procedencia y ausencia de datos explícitas.

- RF-UX-003: retirados de Inicio el botón de crear ejemplo y su explicación;
  acciones de crear normal/reducida y consultar aciertos agrupadas.

- RF-UX-002: boleto de ancho fijo con filas compactas; deja de ensancharse y
  desplazar pronósticos al maximizar. Aciertos reserva altura a los 14 resultados
  y el Pleno; tabla de apuestas inferior más pequeña y reparto ajustable. Los
  controles siguen accesibles en pantallas pequeñas, con desplazamiento.

- RF-QUI-010: pregunta de arranque para continuar la última quiniela normal o
  reducida, o crear una normal nueva para la jornada actual. Conserva las
  versiones anteriores; descarga asíncrona si faltan datos actuales, con error
  claro en modo offline. La prueba de arranque automático omite la pregunta.

- Validación de 1.0.1: 228 pruebas Studio y 32 históricas correctas; 2 TXT
  personales opcionales ausentes. Ruff E9/F/I, self-check y arranque correctos;
  wheel/sdist construidas y arranque de la wheel aislada verificado.

## 1.0.0 — 13/10/2026 · Optimización verificable y boletos manuales

- Continuación: referencias con idéntica cantidad mediante DP por Pleno;
  auditoría correlacionada de inicio, éxito, cancelación y fallo; entradas
  numéricas extremas sin desbordamientos no controlados.
- Cancelación y progreso visibles en Optimizar; parámetros avanzados
  desplazables para no ocultar botones en pantallas pequeñas.
- Informes de garantía invalidados al editar/restaurar y conservados en el
  histórico; búsqueda exacta sin descartar diferencias de masa inferiores a 1e-12.
- Ranking y objetivo de masa en escala logarítmica/reescala común, incluido
  Pleno: las probabilidades absolutas diminutas no se convierten en empates
  ficticios; aviso e informe de log(masa) cuando el float se redondea a cero.

- Entrega pedida como v0.1.14 y renumerada a v1.0.0 por el usuario.
- RF-RED-002 / RF-GAR-001/002/003: carteras con ganancia marginal, intercambio,
  exhaustivo acotado y muestreo reproducible; cobertura uniforme/ponderada
  independiente, mínimos condicionales y certificado solo cuando procede.
- RF-PRO-005 / RF-AUD-001: cuatro objetivos (valor esperado no disponible),
  fuentes deportivas separadas de popularidad, propuesta antes de aplicar,
  comparación, aportaciones, auditoría y remanente de presupuesto.
- RF-QUI-002: Pleno manual predeterminado; automatismo explícito, parejas
  múltiples/diversificadas y modelo independiente de goles etiquetado.
- RF-ARC-009: asistente manual TuLotero 2–8 por boleto, Pleno común, reglas
  configurables, TXT/CSV con relectura. Sin importación automática/envío/pago.
- Sin cambios destructivos de datos/esquema ni nuevas dependencias pesadas.
  Documentación y límites: `docs/STUDIO_V1_0.md`.
## 0.1.13 — 13/10/2026 · Normal y Reducidas independientes

- RF-QUI-005/006: dos constructores independientes por jornada; Normal y
  Reducidas recuperan sus propios sistemas, sin copiar la base normal.
- RF-GEN-003/005: barra normal reactiva con agrupación de eventos (150 ms),
  protección de jornada/revisión, sin necesitar «Cambiar el boleto».
- RF-RED-001/002: seis tipos disponibles; base específica por porcentajes,
  fijos/dobles/triples según cada tabla y bloqueos; alternativas/coste con Pleno,
  ajuste manual opcional y generación exacta. Normal permanece intacta.
- RF-PRO-003/008: diferenciación original 0–10 con log(p) − alpha*log(q), solo
  como pesos de selección; requiere mercado y popularidad de Quinielista.
  No sustituye las probabilidades del proveedor ni calcula premios esperados.
  Puede reducir aciertos; no garantiza rentabilidad o exclusividad.
- Pruebas de todos los tipos, independencia/reinicio, Pleno, exportación, fuentes,
  bloqueos y eventos atrasados. Sin migración de hashes antiguos ni cambios Android.

## 0.1.12 — 13/10/2026 · Pleno más claro y ordenado

- RF-PRO-008 / RF-QUI-002: panel visual del Pleno con casillas 0/1/2/M
  separadas de una fila inferior de porcentajes, alineada por columnas.
- Casillas más amplias, título diferenciado y resumen de coste en dos líneas.
  Sin selección se muestran instrucciones, no una multiplicación por cero.
- Cálculos, selección múltiple y exportación sin cambios. Prueba de geometría
  para alineación y visibilidad de Generar a 1024×768. Android sin cambios.

## 0.1.11 — 13/10/2026 · Porcentajes y preselección del Pleno múltiple

- RF-PRO-001/002/008: porcentajes 0/1/2/M del local y visitante en la fuente
  congelada, visibles junto a casillas. Lectura mercado/público con identidad
  completa y validación; los JSON anteriores siguen siendo compatibles.
- RF-GEN-003/005: «Cambiar el boleto» preselecciona también goles del Pleno
  con heurística propia progresiva (1 a 16 parejas), sin alterar los bloqueos
  de los 14 partidos. Si no hay datos conserva la selección manual con aviso.
- RF-QUI-002/003: multiplicación de columnas y parejas del Pleno explícita,
  coste total y advertencia nivel 10 hasta 55.296 apuestas. Generación y TXT
  incluyen cada pareja; los pares exactos importados siguen preservados salvo
  preselección explícita. No se afirma independencia ni garantía del marcador.
- RF-QUI-005: Deshacer recupera también las máscaras y parejas previas del
  Pleno, no solo el campo de marcador único.
- Pruebas y alcance: `tests/studio/test_pleno_probabilities.py`,
  `docs/planes/PLENO_PORCENTAJES.md`. Android permanece sin cambios.

## 0.1.10 — 13/10/2026 · Porcentajes reales y textos claros

- RF-JOR-007 / RF-PRO-008: sustituido «Usar los últimos datos» (solo copiaba
  SQLite) por una descarga asíncrona de la jornada abierta. Identidad completa,
  rechazo de resultados si cambia el sistema y conservación ante fallos.
- RF-PRO-001 / RF-PRO-002: importación del mercado `p_bf_*desc` ya publicado en
  el XML completo, separado de los signos jugados en Quinielista. No es una IA
  propia ni demuestra mayor tasa de acierto. Pleno y LAE separado pendientes.
- Fuente, hora de captura y ausencia de porcentajes visibles. Descargar no
  modifica apuestas/precio; las recomendaciones requieren una fuente existente.
- Equivalencias explícitas de abreviaturas verificadas en jornada 13 para
  Manchester United/City, Bayern, Dortmund y CSU Craiova; no coincidencia difusa.
- Plan y pruebas: `docs/planes/FUENTES_PORCENTAJES.md` y
  `tests/studio/test_probability_sources.py`. Android sin cambios.

## 0.1.9 — 12/10/2026 · Guardar apuestas y preparar su carga manual

- RF-ARC-009: Guardar apuestas (TXT) visible desde cualquier pestaña; conserva
  exactamente las apuestas optimizadas/reducidas, copias y Plenos presentes.
- Mis Sistemas exporta la fila elegida, aunque esté abierta otra quiniela.
  Corregidos tanto TXT como JSON; botones de selección claramente separados.
- Confirmación con ruta, cantidad, coste congelado y pasos para cargar el TXT.
  Botones de abrir carpeta y web únicamente por clic. Sin subida ni pago
  automático; demo y jornadas de consulta desactivan el acceso a la web.
- Nombre con jornada/revisión, carpeta recordada y auditoría del TXT guardado.
- Guardado bloqueado mientras se actualizan condiciones, para evitar sacar
  apuestas anteriores. La tabla indica cuándo ya están listas para guardar.
- 137 pruebas Studio y 32 históricas con GUI correctas; Ruff, arranque nativo,
  self-check e importación de la wheel aislada correctos.

## 0.1.1 — 10/10/2026

- AI Studio integra descarga, carpeta y ZIP WIN1X2, revisión y caché offline.
- Porcentajes públicos XML validados y separados de deportiva; actualización
  explícita de fuentes congeladas y selección de ranking deportivo/público.
- Marcador manual y caché por jornada, sin tratar pendientes como empates ni
  calcular premios económicos del directo. Consulta de PRE guardado.
- Recuperación de versiones SQLite de Quiniela Local como copias idempotentes,
  conservando apuestas/Plenos/repetidos y desarrollo original.
- Filtros básicos del motor anterior y restauración de apuestas de origen.
- SQLite esquema 2, copia previa de esquema 1 y auditoría de importaciones.
- Constructor muestra horarios y los equipos del Pleno al 15.
- Se conserva el lanzador Tkinter. Android queda intacto; paridad completa y
  ejecución nativa Windows siguen pendientes.

## 0.1.2 — 11/10/2026 · revisión de aceptación v0.1

- Recuperada la experiencia visual de Quiniela Local: fondo azul, quiniela
  permanente, pestañas, descarga en cabecera y Pleno con casillas de goles.
- Contadores y coste de base en vivo; selección parcial del Pleno persistente.
- Proyecto organizado en src con domain/application/infrastructure/ui y aliases
  compatibles; Python >=3.11 y rutas estándar mediante platformdirs.
- Reglas locales de precio configurables para sistemas nuevos y auditadas.
- Exportación directa TXT/JSON perezosa, atómica y cancelable, con apuestas
  exactas de sistemas reducidos. Importación del fixture original de 12 apuestas.
- Se conservan descarga, importación y recuperación de la entrega anterior.

## 0.1.3 — 11/10/2026 · corrección de filtros

- RF-FIL-009: casillas individuales visibles para los siete filtros básicos,
  límites habilitados solo al activarlos y valores desactivados ignorados.
- Referencia obligatoria al activar coincidencias; error sin guardar versión.
- RF-RED-002: estado explícito de reductores pendientes en Optimizar; la selección
  por presupuesto sigue sin garantía. Estado de IA pendiente (v0.6) en Análisis.
- 83 pruebas Studio, incluidas interacción por clic, desactivación y validación.

## 0.1.4 — 11/10/2026 · recuperación del flujo de filtros

- RF-FIL-009: desactivar todos los filtros; errores de configuración dentro del
  panel, sin diálogo que bloquee desmarcar casillas.
- RF-FIL-001: aplicación deshabilitada si no hay apuestas exactas guardadas y
  explicación de cómo generar el desarrollo antes de filtrar.
- La barra vuelve a cero y muestra «Sin desarrollo generado» si una edición
  invalida las apuestas; no mantiene el 100 % de una generación anterior.
- 85 pruebas Studio: error seguido de desmarcado por clic, desactivar todos,
  versión intacta tras error y progreso coherente después de editar signos.
- Instrucciones de tres pasos y condiciones con nombres cotidianos; los detalles
  de separación entre X pasan a ayuda contextual, sin jerga AND en el panel.
- RF-AUD-004: revisión del lenguaje de las siete secciones, archivos descritos
  por su contenido, precio visible y detalles técnicos del historial plegados.

## 0.1.5 — 11/10/2026 · barra progresiva en Optimizar

- RF-QUI-005 / requisito PC T03: barra 0–10 también en Optimizar, sincronizada
  con Crear, con propuesta de dobles/triples, apuestas y coste antes de aplicar.
- Se reutiliza el motor de plantillas comprobado; mover la barra no altera
  apuestas ni crea versiones. Aplicar exige generar de nuevo.

## 0.1.6 — 11/10/2026 · recuperación de Ajustes rápidos

- Corregida la interpretación de la barra solicitada: Optimizar ajusta condiciones
  automáticamente; dobles y triples quedan en Crear Quiniela.
- RF-FIL-002/009: recuperados cambios entre signos y racha máxima de 1;
  filtros locales versión 2 con valores neutros compatibles con los anteriores.
- Niveles 0 menos / 10 máximo según petición, usando límites históricos invertidos
  y nivel 10 neutro. Sin tope silencioso 200/50 ni garantía de reducción.
- Aplicación desde las apuestas originales, para recuperar más al ampliar el nivel.
- 94 pruebas Studio: oráculo independiente, niveles anidados, apuestas/Plenos/
  cantidades intactos, parámetros inválidos y recuperación completa en nivel 10.

## 0.1.7 — 11/10/2026 · Optimizar reactivo

- RF-FIL-001/009: barra y condiciones recalculan apuestas/coste automáticamente,
  sin botones de confirmar nivel ni aplicar filtros. Barra propia e independiente.
- Trabajador cancelable, agrupación de cambios y descarte de resultados obsoletos;
  cierre seguro y recuperación de ajustes al abrir de nuevo.
- RF-RED-001/002: presupuesto al final, aplicado únicamente al resultado filtrado.
- Textos reducidos; cero coincidencias muestra 0 apuestas / 0 €, recuperable;
  exportación directa impide sustituir una selección vacía por su base.
- 100 pruebas Studio: reacción, última petición, vacío/recuperación, cancelación,
  cierre, presupuesto final, persistencia de condiciones y exportación segura.

## 0.1.8 — 12/10/2026 · Aciertos automáticos, Pleno múltiple y Reducidas

- RF-ESC-001/002/003/004: Aciertos con marcador de 15 partidos, comparación por
  apuesta, aciertos/fallos/pendientes y Pleno condicionado a 14 y goles finales.
- RF-JOR-007: refresco automático cada 30/60/120 s en la sección, caché validada
  por jornada/equipos y fallos de red no modales; modo manual reactivo para demo.
- RF-QUI-002/003/004: varias selecciones de goles por equipo, multiplicación de
  apuestas/coste y persistencia/import-export, sin perder parejas de Pleno exactas.
- RF-RED-001/003/009: pestaña opcional con seis matrices del BOE 2009 enlazado por
  el artículo SELAE, verificación exhaustiva y creación como copia independiente.
- Tablas fechadas, sin declararlas formato oficial vigente: discrepancias de
  transcripción con PDF posterior registradas; mínimo verificado tabla 6 = 9.
- No se modifica Android, no se implementa sellado ni premios inventados.
- 120 pruebas Studio y 32 de regresión histórica correctas; Qt/X11 y proveedor
  real verificados; las apuestas seleccionadas se mantienen al cambiar el ranking.
