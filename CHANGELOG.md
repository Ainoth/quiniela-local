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
