# Cambios

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
