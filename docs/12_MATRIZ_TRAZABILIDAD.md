# 12 · Matriz de trazabilidad de requisitos

RF-UX-026/027 (v1.0.33): Cuenta presenta un solo selector de temporadas y una
distribución compartidos por Manual/Azar/Automática. Cabeceras dentro de sus
paneles; altura según contenido. Sin tablas vacías de reservas. Selección con
casillas verdes, búsqueda que conserva opciones ocultas y presets por lotes.
Pruebas: `test_season_presets_are_one_change_and_search_preserves_hidden_choices`,
`test_cuenta_uses_one_season_picker_and_keeps_labels_outside_scroll`,
`test_count_and_streak_mode_grids_apply_and_outer_squares_preserve_settings`.

RF-FIL-026 (v1.0.33): distancia entre X muestra el rango realmente activo y
explica la diferencia de posiciones; sin dos X no descarta. Prueba de filtro
con apuestas reales: `test_cuenta_dashboard_shows_joint_figures_distribution_seasons_and_distance_filter`.

RF-UX-028 (v1.0.33): el riesgo se elige mediante botones exclusivos en toda
la interfaz Qt; conserva datos y etiquetas al restaurar. Pruebas:
`test_risk_buttons_are_exclusive_and_restore_saved_labels`,
`test_every_risk_control_uses_visible_buttons` y pruebas de métodos aleatorios
y automáticos de `test_advanced_conditions_ui.py`.

RF-UX-023 (v1.0.32): Normal muestra el flujo de elección de porcentajes,
asignación, relleno, generación y exportación. La fuente de la matriz incluye
solo capturas reales y perfiles locales importados; el usuario puede mantener
la matriz editable. Las ponderaciones auxiliares actúan solo tras aplicar la
media ponderada. Pruebas: `test_visible_matrix_source_controls_the_percentages_used_for_base`,
`test_source_switch_updates_unedited_matrix_but_preserves_manual_edits`.

RF-UX-024 (v1.0.32): Cuenta mantiene Distancia X visible en Manual y
Automática, con su casilla conectada al filtro existente. Reservas/medias
no calculadas se indican expresamente como pendientes. Prueba:
`test_count_distance_controls_share_one_visible_filter_panel`.

RF-UX-025 (v1.0.32): la barra inferior muestra actividad indeterminada
durante trabajos de datos y progreso real de generación. Prueba:
`test_footer_progress_follows_generation_progress`.

RF-NOR-005 (v1.0.31): una jornada ya abierta incorpora las instantáneas nuevas
de mercado/popularidad; la matriz externa se refresca si estaba vacía o seguía
vinculada a esa fuente. Factores auxiliares sin datos no se ponderan. Prueba:
`test_same_round_source_refresh_populates_matrix_and_disables_missing_factors`.

RF-DAT-006 (v1.0.30): porcentajes de Quinielista aceptan los alias explícitos
PSV / PSV Eindhoven, Shaktar / Shakhtar Donetsk y Leipzig / RB Leipzig; sigue
rechazando equipos distintos. Prueba: `test_quinielista_market_names_match_win1x2_aliases_for_champions_round`.

RF-ESC-014 (v1.0.29): cambio de sistema oculta las dos tarjetas previas;
tarjeta compacta de categorías 15–10 con acertantes, premio oficial unitario,
apuestas propias, subtotal y total. Pruebas:
`test_switching_system_in_mis_sistemas_clears_previous_prize_before_aciertos`,
`test_cached_scrutiny_shows_prize_breakdown_and_clears_on_round_change` y
`test_published_page_cache_displays_real_j14_prize_when_pre_is_provisional`.

RF-UX-022 (v1.0.29): la pestaña visible se llama Escrutinio; conserva el
índice 4 y las rutas existentes. Prueba: `test_switching_system_in_mis_sistemas_clears_previous_prize_before_aciertos`.

RF-ESC-013 (v1.0.28): si el PRE es provisional y los 15 resultados están
finalizados, Aciertos consulta un espejo público del escrutinio en un hilo,
comprueba identidad completa y seis categorías, guarda el resultado validado
y muestra el premio positivo desglosado. Sin datos íntegros no muestra dinero.
Pruebas: `test_published_scrutiny_reference_j14_and_all_payouts`,
`test_published_scrutiny_rejects_wrong_round_fixture_score_or_amount`,
`test_published_page_cache_displays_real_j14_prize_when_pre_is_provisional`.

RF-ESC-012 (v1.0.27): Aciertos muestra importes desglosados solo con reparto
definitivo publicado en el PRE local de la jornada. Comprueba identidad del
boleto, copia y categoría; no afirma sellado ni pago. Pruebas:
`test_cached_scrutiny_shows_prize_breakdown_and_clears_on_round_change`,
`test_published_scrutiny_with_no_award_stays_neutral`,
`test_cached_scrutiny_with_wrong_teams_never_announces_a_prize` y `test_T10_accumulated_prizes_and_pending`.

RF-UX-021 (v1.0.26): SSeguidos usa fondo plano oscuro y selector histórico de
temporadas en dos columnas. No cambia la lógica de rachas. Prueba:
`test_sseguidos_three_modes_compact_panels_filter_and_share_state`.

RF-UX-015 / RF-FIL-021 (v1.0.19): SSeguidos implementa Manual, Azar y
Automática sobre estado compartido. Incluye límites opcionales con vacío
distinto de cero, frecuencias de rachas máximas exactas y figuras como
particiones; la base actual determina qué valores son posibles. Automática usa
perfiles conjuntos de resultados históricos, Azar es reproducible por semilla,
y el Pleno queda excluido. La activación externa conserva condiciones y decide
si intervienen. Pruebas: `test_sseguidos_three_modes_compact_panels_filter_and_share_state`,
`test_sseguidos_empty_bound_remains_empty_after_persistence`,
`test_sseguidos_automatic_keeps_joint_profiles_and_is_not_a_duplicate_filter`,
`test_attainable_run_frequencies_and_figures_match_exhaustive_small_base`.

RF-UX-016 / RF-FIL-022 (v1.0.20): FSSeguidos agrega un editor compacto de
particiones exactas por total para `1/X/2/V`, con Manual, Azar y Automática.
La selección es multivalor; las reglas se limitan a figuras alcanzables con
la base, usan estadísticas históricas reales, mantienen persistencia propia y
requieren activar la subpestaña. SSeguidos sigue independiente y no se elimina.
Pruebas: `test_fsseguidos_filters_exact_partition_separately_and_persists` y
`test_fsseguidos_automatic_uses_integrated_history_and_azar_repeats_seed`.

RF-UX-017 / RF-FIL-023 (v1.0.21): Interrupciones cuenta cambios en las 13
transiciones de los primeros 14 signos. Manual/Automática filtran los pares de
total y racha máxima; Distancias filtra totales y particiones exactas por
separado. Sus Aplicar internos y activación exterior son independientes.
Automática usa el histórico integrado por temporadas; Azar conserva semilla.
La semántica `(total, racha máxima)` de la matriz está documentada como propia
y provisional por no estar confirmada la columna histórica 0. Pruebas:
`test_interruption_matrix_and_distances_are_separate_active_filters_and_persist`,
`test_interruption_random_and_automatic_modes_use_reproducible_and_integrated_data`,
`test_dynamic_program_matches_exhaustive_reachability_for_restricted_base`.

RF-UX-019 / RF-FIL-025 (v1.0.24): Cuenta coloca la matriz de cantidades junto a
Figuras (perfiles conjuntos `(V, X, 2)`), Distribución Signos y las temporadas.
Las frecuencias 1/X/2 salen de jornadas históricas seleccionadas y suman 14
marcas por jornada. Filtros reutiliza la distancia entre equis existente; al
estar activa Cuenta participa una sola vez, y la casilla exterior sigue apagada
por defecto. Pruebas: `test_cuenta_dashboard_shows_joint_figures_distribution_seasons_and_distance_filter`,
`test_joint_automatic_profile_keeps_categories_dependent` y los casos de
activación exterior de Cuenta.

RF-UX-014 (v1.0.18): SSeguidos expone únicamente Automática y dispone sus
controles de temporadas y sus paneles `1`, `X`, `2`, `V` en una cuadrícula
compacta con frecuencias y figuras agrupadas. Cuenta mantiene sus tres modos y
su matriz al aislar los controles heredados de Racha. La activación de la
subpestaña conserva su semántica y sigue apagada por defecto. Pruebas:
`test_sseguidos_automatic_only_compact_panels_filter_and_share_racha_state`
y `test_count_and_streak_mode_grids_apply_and_outer_squares_preserve_settings`.

RF-UX-013 (v1.0.17): la pestaña de rachas consecutivas se muestra como
**SSeguidos** y presenta paneles compactos con límites mínimo/máximo derivados
de la base y frecuencias dentro de cuadrados blancos/verdes. Mantiene el
identificador y serialización Racha para no duplicar condiciones ni romper
sistemas guardados. Pruebas: `test_sseguidos_automatic_only_compact_panels_filter_and_share_racha_state`
y `test_sseguidos_minmax_choices_follow_current_base`.

RF-ESC-011 (v1.0.16): cuando el marcador principal no conecta, no devuelve una
jornada interpretable o deja partidos sin marcador tras su horario, un
adaptador alternativo consulta ESPN para Primera, Segunda y Liga F. Una
respuesta primaria con equipos distintos se rechaza directamente.
Solo acepta una fila al coincidir día y equipos local/visitante; los horarios
sin cobertura quedan en blanco. Los resultados programados 0–0 no cuentan como
marcador. Los refrescos reutilizan ESPN tras una respuesta válida.
Si ambas fuentes tienen datos, solo se completan filas vacías del proveedor
principal. Verificación: `tests/studio/test_espn_live.py` y consulta con J14.

RF-ESC-010 (v1.0.15): sin marcador recibido, Aciertos compara el horario de
inicio con la hora local para distinguir partidos por comenzar de partidos sin
resultado disponible. El horario no se interpreta como resultado final. Los
errores de conexión tampoco describen toda la tabla como pendiente.
Verificación: `test_waiting_marker_uses_schedule_without_claiming_unknown_result`
y pruebas de la pantalla Aciertos.

RF-ESC-009 (v1.0.14): el marcador reintenta una vez fallos transitorios y la
tabla de Aciertos conserva los 15 encuentros en estado pendiente cuando aún no
hay caché. Una respuesta fallida no sustituye el último marcador válido.
Verificación: `test_fetch_retries_one_transient_connection_error`,
`test_fetch_reports_connection_error_after_retry` y suite de Aciertos.

RF-DAT-005 / RF-UX-012 (v1.0.14): el histórico integrado se carga al iniciar;
la importación adicional queda en Configuración. Reducciones presenta solo las
pestañas disponibles en esta fase (Cuenta, SSeguidos y Grupo), dejando el código de
las otras páginas intacto. Normal es la primera entrada en lugar de Inicio.
Verificación: `test_automatic_season_picker_is_compact_and_has_bulk_selection`
y `test_group_editor_adds_compact_side_by_side_group_cards`.

RF-EXP-004 (v1.0.13): el TXT clásico es una apuesta por línea, 14 signos 1/X/2
más los dos signos del Pleno, sin delimitadores; las cantidades se expanden en
líneas repetidas. Exportación normal y directa usan el mismo serializador.
Pruebas: `test_T12_roundtrip_quantity_and_full_export` y
`test_direct_txt_export_reports_written_count_without_changing_draft`.

RF-NOR-004 (v1.0.12): Manual indica cantidades de triples/dobles y el motor
elige los partidos por masa probabilística; Automática elige además las
cantidades con programación dinámica exacta y objetivo de probabilidad
conjunta bajo el máximo configurable. Los bloqueos se preservan y los empates
se resuelven de forma determinista. Cuenta/Racha integra las frecuencias
históricas dentro de los botones de valores. Pruebas: `test_automatic_base_selects_quantities_exactly_under_column_limit`, `test_automatic_base_respects_locked_width_and_impossible_limit`, `test_normal_generator_manual_mode_chooses_counts_and_parties_by_probability`, `test_normal_generator_automatic_selects_counts_under_column_limit` y `test_count_and_streak_mode_grids_apply_and_outer_squares_preserve_settings`. RF-FIL-020: activaciones de Reducciones apagadas por defecto;
solo las pestañas que el usuario active participan. Los ajustes anteriores se
migran como inactivos hasta que el usuario confirme activaciones. RF-DAT-004:
histórico CSV incluido, auto-cargado, con `results14` y marcadores opcionales
`score_01`…`score_15`; los 880 registros enriquecidos se verifican con los
signos publicados. Las frecuencias compactas se recalculan con las temporadas
marcadas. Pruebas: `test_manual_base_uses_requested_widths_and_probability_order`,
`test_bundled_historical_results_load_and_include_verified_scores` y UI.

RF-UX-011 (v1.0.10): compacta las cuadrículas de valores de Cuenta/Racha y
reemplaza el carril horizontal de temporadas por una cuadrícula compacta de
selección múltiple, ordenada de más reciente a más antigua, con controles
Todas/Ninguna y resumen de jornadas. Los cuadrados mantienen estado accesible.
Verificación: `test_automatic_season_picker_is_compact_and_has_bulk_selection`
y la suite `test_advanced_conditions_ui.py`.

RF-FIL-018 / RF-FIL-019 / RF-UX-010 (v1.0.9): se amplían Cuenta y Racha
existentes, sin sustituir Cambio. Cuenta filtra valores permitidos V/X/2
(V=X+2); Racha admite longitudes máximas y frecuencias de figuras exactas,
no solapadas, incluyendo la clase mixta V. Manual usa recuadros blancos/verdes;
Azar selecciona valores observados del desarrollo con semilla reproducible;
Automática importa resultados finales CSV/JSON y selecciona perfiles conjuntos
empíricos. Activa/desactiva cada subpestaña sin perder valores; estado, regla,
fuente, temporada, muestra, riesgo y semilla se serializan en filter_spec.
El fixture demo sintético se rechaza. No se afirma predicción ni equivalencia
con el software del manual. Pruebas: `test_streak_statistics.py`,
`test_reduction_rules.py`, `test_advanced_conditions_ui.py` y `test_ui.py`;
plan en `docs/planes/VARIANTES_RACHAS.md`.

RF-NOR-001 / RF-NOR-002 / RF-NOR-003 (v1.0.8): generador Normal integrado.
La base gráfica edita porcentajes 1/X/2, ponderaciones y cantidades T/D; el
dominio aplica DP exacta para maximizar masa retenida y audita la selección.
Las filas compactas generan rangos por top-K exacto en log-probabilidad,
terminaciones desde posición 1, rango C.P. mínimo/máximo, bases triples/dobles y ficheros
locales; combinan por concatenación, unión o intersección en SQLite temporal.
Fuentes CSV/TXT/JSON se validan contra jornada y equipos y persisten por jornada.
Fuentes inexistentes no se simulan. Pruebas:
`test_normal_generation.py`, `test_normal_generation_files.py` y
`test_normal_generator_ui.py`; plan y alcance en
`docs/planes/GENERADOR_NORMAL_AUTOMATICO.md`.

RF-UX-009 (v1.0.7): refuerza la similitud visual con el manual WIN1X2 en
Reducciones: tablero azul enmarcado, cabeceras destacadas, seis matrices
compactas 1/X/2 por defecto y etiquetas breves para que las 17 pestañas se
vean juntas en una ventana de escritorio amplia. Los nombres completos de
método siguen disponibles como ayuda emergente. Verificación Qt a 1600×950;
la interfaz se adapta a ventanas más estrechas con desplazamiento.

RF-UX-008 / RF-FIL-017 (v1.0.6): referencias, patrones y selección de columnas
se realizan con botones 1/X/2 en matrices gráficas; los valores numéricos se
ajustan con flechas no editables. Columnas suma los aciertos máximos de varios
grupos; Relacionados conserva la diferencia entre dos; Si… entonces expresa
una implicación acotada. Frecuencias añade y elimina columnas desde la matriz.
Pruebas de interacción en `test_advanced_conditions_ui.py` y persistencia en
`test_advanced_conditions.py`.

RF-FIL-015 / RF-FIL-016 / RF-UX-007 (v1.0.5): reglas de reducción propias
serializables (esquema basic-local-v5), pestañas Qt compactas antes de
Optimizar y matriz de grupos visual 1/X/2. Patrones de 2–5 posiciones
consecutivas, repetición de referencia, frecuencia entre referencias y suma o
log-probabilidad con snapshot explícito; se combinan con filtros existentes y
se actualizan en vivo. Cobertura Hermes/Atenea/Artemisa asíncrona, cancelable,
con selección de candidatas determinista y verificador independiente; copia
nueva con informe. La garantía solo vale si universo exacto; el Pleno queda
fuera. Si… entonces añade una implicación tipada entre dos grupos con
intervalos independientes y comparte la tolerancia de fallos. Columnas informa
de operaciones que ya resuelven Optimizar/Atenea, para evitar reducciones
duplicadas; no incorpora suma/diferencia colectiva de apuestas. Pruebas
`test_reduction_rules.py`, `test_coverage_reducer.py`,
`test_advanced_conditions_ui.py`, `test_advanced_conditions.py` y
`test_filters_integration.py`.

RF-FIL-014 / RF-UX-006 (v1.0.4): editor visual de hasta ocho grupos en columnas
compactas simultáneas, solo con número de partido y botones 1/X/2, relación
configurable entre pares y explicación breve. La pestaña aparece antes de Optimizar. Lee condiciones del
esquema v1.0.3 y las migra a máscaras visuales al guardar. Pruebas en
`test_advanced_conditions.py` y `test_advanced_conditions_ui.py`.

RF-FIL-014 (v1.0.3): pestaña independiente de condiciones avanzadas. Compara
dos grupos configurables de partidos con signos de referencia, limita la suma
o diferencia de aciertos y permite tolerar fallos de condiciones. Se evalúa
junto con los filtros básicos desde el desarrollo de origen; el resultado y
coste se actualizan automáticamente. Reglas deterministas originales; no
predicen resultados ni ofrecen garantías. Pruebas en
`tests/studio/test_advanced_conditions.py`; restauración/compatibilidad con
filtros anteriores mediante `filters_from_parameters`.

RF-UX-005 (v1.0.2): icono de Quiniela Local en ventanas y diálogos Qt y barra
de tareas; imagen incluida en la wheel y clase de ventana estable. Verificación
nativa Linux/X11 de `WM_CLASS` y los 65.536 píxeles de `_NET_WM_ICON`, herencia
de icono en diálogo y carga del recurso desde una instalación aislada. Regresión
de arranque y distribución mediante las pruebas existentes. Identidad Windows
preparada, ejecución nativa pendiente.

RF-UX-004 (v1.0.1): tabla clásica de la base con número, partido, hora,
porcentajes y 1/X/2; filas alternas, Pleno compacto y ancho fijo. La fuente
deportiva y la popularidad se muestran por separado según la selección, sin
alterar valores de cálculo ni inventar datos ausentes. Verificado en
`test_aciertos_layout.py`: calendario, cambio de fuente, ausencia de datos,
hash/bets intactos y geometría estable. Pleno y bloqueos mantienen su cobertura
de interacción en las pruebas existentes.

RF-UX-003 (v1.0.1): retirado el acceso de crear ejemplo y su texto de Inicio;
crear normal/reducida y consultar aciertos comparten la fila de acciones.
Verificación de las acciones visibles en Qt y regresión existente de interfaz
`test_ui.py`. README actualizado para el recorrido actual.

RF-UX-002 (v1.0.1): ancho fijo del boleto, filas compactas alineadas arriba y
espacio sobrante debajo de los controles. Aciertos da prioridad a sus 15 filas
de marcador (14 partidos y Pleno); la tabla inferior queda más pequeña y permite
ajustar el reparto. En pantallas bajas se usa desplazamiento. Pruebas en
`test_aciertos_layout.py`: posiciones estables entre 1200×975 y 1920×1080,
marcadores completos, selección de apuesta conservada y controles a 1024×768.

RF-QUI-010 (v1.0.1): pregunta de arranque en español; Sí continúa el sistema
abierto por última vez, también reducido, y No crea una quiniela normal nueva
para la jornada actual. Conserva IDs, hashes y versiones anteriores. Descarga
asíncrona si falta la jornada; sin conexión no fabrica una jornada actual ni
retoma la anterior. Perfil solo demo explícito. Pruebas en `test_startup.py`:
clics reales Sí/No, reapertura con modos separados, importación, fallo de red
y primera sesión offline. `--smoke-test` no muestra la pregunta.

Continuación v1.0.0: RF-RED-002 comparaciones de cardinalidad exacta con DP por
Pleno; RF-AUD-001 inicio/fallo/cancelación correlacionados; RF-PRO-001 datos
numéricos extremos rechazados; RF-UX-001 cancelación visible y avanzados
desplazables. Regresiones: `test_portfolio.py` y `test_v1_gui.py`.
RF-GAR-001/003: retirar informes obsoletos al editar/restaurar sin destruir
versiones anteriores; RF-PRO-005: diferencias de masa menores de 1e-12 siguen
contando en búsqueda exhaustiva. Oráculos y persistencia: `test_portfolio.py`.
RF-PRO-005: ranking y objetivo de masa reescalados desde logaritmos, incluidas
marginales del Pleno; regresiones de subdesbordamiento (1e-100 y 1e-300), aviso
y log(masa) conservado en informe y vista previa.

v1.0.0: RF-RED-002 carteras por objetivo; RF-GAR-001/002/003 verificador
independiente y métricas por universo; RF-PRO-005 masa deportiva; RF-QUI-002
Pleno explícito/manual/diversificado; RF-ARC-009 preparación TuLotero con
relectura; RF-AUD-001 auditoría. Pruebas en `test_portfolio.py` y `test_v1_gui.py`.
Alcance/métodos/pendientes: `STUDIO_V1_0.md`. Valor esperado, IA calibrada,
solver externo e importación oficial TuLotero NO se declaran implementados.

Revisión 0.1.13: RF-QUI-005/006 separan Normal y Reducidas por sistemas propios;
RF-GEN-003/005 añaden barra reactiva y bases específicas respetando bloqueos;
RF-RED-001/002 reutilizan las seis matrices con elección de tipo; RF-PRO-003/008
añaden diferenciación opcional como pesos originales, no rentabilidad/probabilidad.
Pruebas `tests/studio/test_construction_modes.py`; alcance y decisiones en
`planes/MODOS_REDUCIDAS_REACTIVOS.md`. Backtesting y rentabilidad siguen pendientes.

Revisión 0.1.12: RF-PRO-008 / RF-QUI-002 separan visualmente porcentajes y
casillas del Pleno, alineados por goles, sin alterar la selección ni cálculos.
Prueba: `test_percentages_are_separate_and_aligned_below_goals` en
`tests/studio/test_pleno_probabilities.py`.

Revisión 0.1.11: RF-PRO-001/002/008 incorporan marginales 0/1/2/M del Pleno,
RF-GEN-003/005 preselección progresiva explícita y RF-QUI-002/003 visibilidad
del producto de columnas y parejas. Pruebas: `tests/studio/test_pleno_probabilities.py`;
alcance y heurística propia: `planes/PLENO_PORCENTAJES.md`. No se declara un
modelo conjunto calibrado de goles ni garantías de acierto.
RF-QUI-005: restauración de parámetros de selección múltiple al deshacer,
verificada al recuperar un Pleno manual tras preselección automática.

Revisión 0.1.10: RF-JOR-007 y RF-PRO-008 añaden descarga explícita de fuentes
para la jornada abierta y estado visible; RF-PRO-001/002 incorporan mercado y
popularidad de Quinielista por separado. No se declara cobertura completa de
fuentes, calibración, LAE separado o predicción del Pleno. Evidencia:
`tests/studio/test_probability_sources.py`; decisión y alcance en
`planes/FUENTES_PORCENTAJES.md`.

Esta tabla está generada inicialmente a partir de `01_ESPECIFICACION_FUNCIONAL.md`. Codex debe convertir los rangos de versión en una **versión precisa** al implementar cada requisito y sustituir PENDIENTE por IMPLEMENTADO solo tras superar las pruebas pertinentes.

| Requisito | Entrega prevista | Estado inicial | Descripción |
|---|---|---|---|
| `RF-UX-015` | v1.0.19 | IMPLEMENTADO | Tres métodos compactos SSeguidos, cuadrados accesibles, temporadas reales y persistencia de límites opcionales. |
| `RF-FIL-021` | v1.0.19 | IMPLEMENTADO | Límites de racha máxima, frecuencias exactas, figuras-partición, perfiles conjuntos y filtro gobernado por la subpestaña activa. |
| `RF-UX-016` | v1.0.20 | IMPLEMENTADO | FSSeguidos con listas compactas multiselección, total editable y tres métodos que comparten controles. |
| `RF-FIL-022` | v1.0.20 | IMPLEMENTADO | Filtra particiones exactas por total, signo y alcanzabilidad; conserva regla y activación propias. |
| `RF-UX-017` | v1.0.21 | IMPLEMENTADO | Interrupciones con matriz compacta, Distancias por figuras, tres métodos y botones cuadrados blanco/verde. |
| `RF-FIL-023` | v1.0.21 | IMPLEMENTADO | Cuenta las 13 transiciones; filtra total/racha y total/figura por separado. El mapa de columna a racha se identifica como provisional. |
| `RF-UX-018` | v1.0.22 | IMPLEMENTADO CON DIFERENCIAS | Lienzos compactos de piel clásica y comparaciones visuales para SSeguidos, FSSeguidos, Interrupciones y Distancias; Cuenta/Grupo armonizados sin referencia original. Ornamento y tipografía siguen siendo aproximados. |
| `RF-ARC-009` | v1.0.23 | CORREGIDO | Mis Sistemas abre informes de cobertura planos o anidados; una copia antigua incompleta conserva el acceso y se rotula sin cobertura verificada. Prueba Qt sobre reducción persistida. |
| `RF-FIL-024` | v1.0.22 | IMPLEMENTADO | Distancias de 1/X/2/V independientes, alcanzabilidad exacta, activación propia y persistencia bajo la pestaña Interrupciones. |
| `RF-UX-019` | v1.0.24 | IMPLEMENTADO | Cuenta compacta integra matriz, Figuras, distribución histórica, temporadas y filtros; fondo ornamental retirado solo aquí. |
| `RF-FIL-025` | v1.0.24 | IMPLEMENTADO | Perfiles conjuntos matemáticamente válidos V/X/2 y distancia entre equis desde Cuenta; ambas condiciones respetan activación de la pestaña. |
| `RF-UX-020` | v1.0.25 | IMPLEMENTADO CON DIFERENCIAS | Cuenta > Manual recrea la composición compacta de tres bloques; cifras por temporada usan resultados reales, controles de reserva/media siguen vacíos e inhabilitados mientras su fórmula no esté definida. Evidencia y checklist en `docs/planes/CUENTA_PANEL_V1_0_25.md` y `docs/validacion_visual/cuenta_v1_0_25/`. |
| `RF-UX-021` | v1.0.26 | IMPLEMENTADO | SSeguidos mantiene sus tres métodos y reglas; el panel automático usa fondo plano y temporadas en dos columnas. Evidencia en `docs/planes/SSeguidos_PANEL_V1_0_26.md` y `docs/validacion_visual/sseguidos_v1_0_26/`. |
| `RF-ESC-012` | v1.0.27 | IMPLEMENTADO | Premio positivo destacado en Aciertos, desglose definitivo 10–15 y carga automática del PRE local válido; sin premio o sin escrutinio no hay anuncio de dinero. |
| `RF-UX-005` | v1.0.2 | IMPLEMENTADO | Icono de ventana/barra de tareas, recurso empaquetado y asociación estable del acceso directo. Windows pendiente de validación nativa. |
| `RF-UX-004` | v1.0.1 | IMPLEMENTADO | Tabla clásica con horario y porcentajes de la fuente elegida; Pleno compacto y datos ausentes explícitos. |
| `RF-UX-003` | v1.0.1 | IMPLEMENTADO | Inicio sin botón ni instrucciones para crear ejemplos. |
| `RF-UX-002` | v1.0.1 | IMPLEMENTADO | Boleto de tamaño estable y prioridad a todos los resultados en Aciertos. |
| `RF-JOR-001` | v0.1/v0.5 | PARCIAL | Crear, abrir, modificar y archivar temporadas, jornadas y sus 15 partidos. |
| `RF-JOR-002` | v0.1/v0.5 | PARCIAL | Validar orden 1..14 y partido 15; detectar duplicados y entradas incompletas. |
| `RF-JOR-003` | v0.1/v0.5 | PENDIENTE | Registrar equipos, fecha/hora con zona horaria, competición y estado del evento. |
| `RF-JOR-004` | v0.1/v0.5 | PENDIENTE | Capturar resultados manualmente y cargarlos desde proveedor autorizado, distinguiendo provisionales/finales. |
| `RF-JOR-005` | v0.1/v0.5 | PARCIAL | Guardar instantáneas de datos con proveedor, hora de captura, versión y calidad. |
| `RF-JOR-006` | v0.1/v0.5 | PENDIENTE | Historial de temporadas, jornadas, recaudación, premios y acertantes cuando estén publicados. |
| `RF-JOR-007` | v0.1/v0.5 | PARCIAL | Política de caché, reintentos, actualización explícita y modo offline. |
| `RF-JOR-008` | v0.1/v0.5 | PARCIAL | Comparación y conciliación entre proveedores; nunca sobrescribir un dato manual sin informar. |
| `RF-QUI-001` | v0.1/v0.8 | PARCIAL | Editor de 14 casillas con subconjuntos no vacíos de `{1,X,2}`: fijo, doble, triple. |
| `RF-QUI-002` | v0.1/v0.8 | PARCIAL | Selector de Pleno al 15 con marcadores `{0,1,2,M}` por equipo; permitir múltiples resultados o uno fijo. |
| `RF-QUI-003` | v0.1/v0.8 | PARCIAL | Contador de fijos, dobles, triples y columnas, multiplicando por selecciones del Pleno al 15. |
| `RF-QUI-004` | v0.1/v0.8 | PARCIAL | Precio configurable/versionado, presupuesto y coste total en céntimos. |
| `RF-QUI-005` | v0.1/v0.8 | PARCIAL | Bloquear signos, deshacer/rehacer, duplicar sistema, plantillas, iniciar, vaciar y completar. |
| `RF-QUI-006` | v0.1/v0.8 | PENDIENTE | Elegir jornadas, asociar sistemas a jornada y registrar objetivo/estrategia. |
| `RF-QUI-007` | v0.1/v0.8 | PENDIENTE | Sistemas mixtos: combinar columnas concretas, bloques múltiples y reducciones sin duplicación involuntaria. |
| `RF-QUI-008` | v0.1/v0.8 | PENDIENTE | Construcción manual desde fichero existente y edición segura de combinaciones importadas. |
| `RF-QUI-009` | v0.1/v0.8 | PENDIENTE | Preparar modelo de Elige8 como modalidad independiente y opcional; requisitos de validación específicos en versión posterior. |
| `RF-QUI-010` | v1.0.1 | IMPLEMENTADO | Preguntar al arrancar: continuar la última quiniela o crear otra normal en la jornada actual, conservando las guardadas. |
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
| `RF-FIL-009` | v0.2/v0.7 | PARCIAL | Activación independiente, orden, presets, clonación, import/export versionado de condiciones. |
| `RF-FIL-010` | v0.2/v0.7 | PENDIENTE | Estudio previo de cada filtro: límites posibles, distribución, efecto y recomendación **sin prometer resultados**. |
| `RF-FIL-011` | v0.2/v0.7 | PENDIENTE | Informe de fallo: qué condición descartó una columna/resultado ganador y por qué. |
| `RF-FIL-012` | v0.2/v0.7 | PENDIENTE | Guardar opcionalmente descartes por filtro, en modo streaming. |
| `RF-FIL-013` | v0.2/v0.7 | PENDIENTE | Filtros de rentabilidad y probabilidad solo cuando existan datos válidos. |
| `RF-FIL-014` | v1.0.3 | IMPLEMENTADO | Grupos de aciertos de partidos, relación suma/diferencia y tolerancia a condiciones incumplidas; pestaña separada y aplicación conjunta con Optimizar. |
| `RF-RED-001` | v0.3/v0.7 | PENDIENTE | Reducir sobre conjunto base ya filtrado con presupuesto o número objetivo de columnas. |
| `RF-RED-002` | v0.3/v0.7 | PENDIENTE | Modos de optimización: cobertura, probabilidad o combinación ponderada; explicar los compromisos. |
| `RF-RED-003` | v0.3/v0.7 | PARCIAL | Objetivos de 14 a 9 aciertos y objetivos de N premios si son matemáticamente interpretables. |
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
| `RF-ESC-002` | v0.1/v0.5 | PARCIAL | Categorías de aciertos 14,13,12,11,10 y Pleno al 15 según reglas vigentes. |
| `RF-ESC-003` | v0.1/v0.5 | PARCIAL | No conceder Pleno al 15 por acertar solo el marcador si faltan los 14. |
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
| `RF-ARC-009` | v0.1 | IMPLEMENTADO | Guardado visible de apuestas exactas, exportación de fila seleccionada y ayuda para cargar el TXT manualmente; sin envío automático. |
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

**Requisitos RF inventariados:** 123.

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

## Aceptación v0.1, revisión 0.1.2

RF-QUI-001/002/003/004, RF-ARC-001 y RF-AUD-001/004/008 cuentan con evidencias
del encargo inicial en `tests/studio/test_original_v01.py` y `test_ui.py`.
El oráculo original produce 12 apuestas / 900 céntimos, conserva draw_id/reglas
y verifica 14 + Pleno. El universo de 14 triples se inicia perezosamente sin
materializar millones de resultados. La regla local cambia solo sistemas nuevos.
La selección parcial de Pleno se recupera al reiniciar y la quiniela permanece
visible al cambiar de sección.

Estructura canónica: `src/quiniela_ai_studio/{domain,application,infrastructure,ui}`.
Guía actual: [STUDIO_V01_ENTREGA.md](STUDIO_V01_ENTREGA.md). Se mantienen estados
PARCIAL para los requisitos completos que incluyen funcionalidades de fases futuras.

## Corrección de filtros 0.1.3

RF-FIL-009: activación independiente mediante casillas visibles y marca textual;
los límites inactivos no filtran. Pruebas GUI de clic, AND con valores neutrales
para condiciones inactivas y error de referencia sin crear versión. Presets,
ordenación e intercambio de condiciones siguen pendientes. RF-RED-002 continúa
pendiente: aviso de estado en Optimizar, sin nuevos algoritmos. Análisis señala
que IA predictiva v0.6 no está implementada.

## Corrección del flujo 0.1.4

RF-FIL-001/009: diferencia visible entre base y apuestas generadas, botón de
aplicación deshabilitado sin desarrollo, desactivar todos y validación inline.
Pruebas GUI: error seguido de clic para desmarcar, sin ventana modal; reset de
condiciones sin cambiar apuestas; editar signos elimina el progreso obsoleto.

RF-AUD-004: revisión transversal de textos y acciones en las siete secciones;
proveniencia técnica accesible mediante ayuda y detalles del historial. No se
modifican modelos, precios, formatos ni cálculos por simplificar el lenguaje.

## Recuperación de la barra 0.1.5

RF-QUI-005 / T03 de ESPECIFICACION_PC: barra progresiva visible en Optimizar y
sincronizada con Crear. Prueba GUI: previsualización sin mutar el sistema,
aplicación nivel 10 con 3.456 combinaciones y conservación del partido bloqueado.
El requisito general sigue parcial; no se añaden algoritmos de reducción.

## Ajustes rápidos 0.1.6

RF-FIL-002/009 / PC T03: barra de condiciones recuperada, distinta de la de
creación. Límites locales versionados v2; cambios entre signos y racha de 1.
Pruebas: extremos de referencia, oráculo sobre 729 apuestas, monotonía de
niveles, GUI sin edición del boleto y recuperación desde origen al volver a 10.
La barra de dobles/triples en Optimizar de 0.1.5 se retira; Crear la conserva.

## Optimizar reactivo 0.1.7

RF-FIL-001/009 y RF-RED-001/002: cálculo automático desde origen, barra
independiente, trabajo cancelable con descarte de peticiones obsoletas y
presupuesto aplicado al final sobre la selección. Tests GUI cubren cambios
rápidos, cierre durante cálculo, recuperación de cero resultados, condiciones
guardadas y coste exacto tras presupuesto. El requisito de reducción completa
sigue pendiente: no hay garantía ni nuevos reductores.

## Incremento 0.1.8

RF-QUI-002/003/004: máscaras de goles, producto de parejas, coste y límite global,
round-trip y streaming. RF-ESC-001/002/003/004 y RF-JOR-007: refresco automático
con proveedor simulado, actual/provisional/final, conservación de caché ante
errores y rechazo de otros equipos; comparación del Pleno requiere 14 + final.
RF-RED-001/003/009: tablas del artículo fechadas BOE 2009, mapeo de partidos y
dobles, extras al directo, P15 múltiple y copia opcional. Cada mínimo se verifica
exhaustivamente, sin asumir 13 para todas. Tests en test_pleno_reductions.py y
test_ui.py. No se declaran fases completas ni formatos autorizados actuales.

## Guardado guiado 0.1.9

RF-ARC-009: botón global, selección independiente en Mis Sistemas, TXT exacto,
nombre con jornada/revisión, carpeta recordada, cantidad/coste congelados y
ayuda tras guardar. Pruebas de exportar una fila distinta de la abierta,
reducción con Plenos múltiples, cancelación, filtros pendientes y navegación
externa solo por clic. RF-ARC-001 y RF-AUD-001 siguen parciales; RF-BOL-005
continúa pendiente: abrir la web no implementa envío, pago ni recibo.
