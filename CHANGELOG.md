# Cambios

## 1.0.0 — 13/10/2026 · Optimización verificable y boletos manuales

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
