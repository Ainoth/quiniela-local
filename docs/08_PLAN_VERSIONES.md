# 08 · Hoja de ruta incremental para Codex

## Principio

Cada versión debe ser instalable y usable antes de continuar. **Prohibido marcar como terminada una funcionalidad que solo tenga botón, placeholder o pseudocódigo.** Cada hito entrega código, tests, manual corto, log de cambios y actualización de requisitos.

## v0.1 · Núcleo ejecutable offline — PRIMERA SESIÓN

**Depende de:** nada.

- Arquitectura de cuatro capas y proyecto con PySide6 + SQLite.
- Jornada DEMO ficticia con 15 partidos; edición de signos 1/X/2 y marcadores P15.
- Fijos, dobles, triples, cálculo exacto de columnas y coste configurable por `GameRuleset` demo.
- Iterador perezoso de columnas; vista paginada/limitada; export/import JSON/TXT propio.
- Guardar, recuperar, modificar sistema; registro de operaciones.
- Escrutinio offline contra resultados introducidos manualmente, sin premio monetario.
- Vistas principales y pantallas de «Pendiente» claras; instalación en Linux, guía Windows.

**Criterios:** pruebas del motor, export/import reversible, costes correctos, UI inicializa, nada de datos reales falsos. 14 triples no provocan intento de expansión en RAM. Versión etiquetada `v0.1.0` cuando sea estable.

## v0.2 · Motor de filtros básico

**Depende de:** v0.1.

- Registro de filtros versionados y serializables; activación/orden, contadores y progreso.
- FIL-01, 02, 03, 04, 13, 18, 19, 31 (solo si probabilidad válida), 32.
- Reglas con `AND`, listas de descartes, explicaciones por apuesta, import/export de filtros propios.
- Estudios simples de impacto sin prometer exactitud si usa muestra.

**Criterios:** invariantes, coincidencia contra evaluador de referencia, sumas de descartes por primer fallo y pruebas con resultados pequeños exhaustivos.

## v0.3 · Garantías y reducción inicial

**Depende de:** v0.2.

- Definir Ω y cobertura por categoría; verificador independiente y exhaustivo para Ω pequeño.
- Reductor `greedy_coverage_v1`, objetivo por columnas/presupuesto, modos internas y externas explícitos.
- Informe exacto o estimado con distinción visible; optimización no bloqueante y cancelable.

**Criterios:** oráculos pequeños, semillas reproducibles, nunca garantía sin prueba, costes correctos.

## v0.4 · Probabilidades, estadísticas y generadores

**Depende de:** v0.2 y núcleo de v0.3.

- Instantáneas de porcentajes manuales/importadas, algoritmo independiente de ranking, generación ponderada.
- Generador por distancias, estadística por signos, parejas/tríos y periodos.
- Estabilizador de porcentajes original con MAE medible y límites de iteración.
- Filtros intermedios de secuencias, grupos, CB y valoraciones.

**Criterios:** normalización y fechas comprobadas, reproducciones deterministas y cálculos independientes.

## v0.5 · Escrutinio completo e informes

**Depende de:** v0.1-v0.4.

- Escrutador parcial/final, resultados oficiales por conector autorizado o importación manual.
- Varios sistemas, categorías, premios definitivos con tabla oficial y cálculo condicional de escenarios restantes.
- Informes PDF, histórico y visor de boletos propio.

**Criterios:** pruebas de 14/13/12/11/10 y Pleno, no confundir parcial con final, no usar premios estimados como reales.

## v0.6 · Motor predictivo y rentabilidad

**Depende de:** historial consistente, datos fechados, baselines, v0.4/v0.5.

- Baselines de 1X2/goles, pipeline de backtesting cronológico, métricas y calibración.
- Modelos opcionales de ML solo si superan pruebas fuera de muestra.
- Estimador original de acertantes y premios con márgenes de error; ranking de EV y perfil de riesgo.
- Generador automático por presupuesto y modelo, explicaciones y registro de decisiones.

**Criterios:** log loss/Brier/calibración, ausencia de fuga de datos, modelo/versiones visibles, sin promesas de rentabilidad.

## v0.7 · Filtros expertos y reducción avanzada

**Depende de:** v0.2-v0.6.

- FIL-05..12, 14..17, 20..30 según semántica fijada; reservas y operadores condicionales.
- `local_search`, `random_restart`, garantías por partición y optimización avanzada.
- Comparar estrategias con mismos escenarios y evaluar efectos de filtros.

**Criterios:** aceptación individual por filtro, métricas de rendimiento y resultados verificables en dominios pequeños.

## v0.8 · Taller de archivos, peñas, sistemas propios

**Depende de:** v0.1-v0.7.

- Conjuntos enormes: unión, intersección, resta, ficheros fraccionados, dedup, ordenación, compactación viable.
- Peñas, participaciones y reparto exacto.
- Migraciones de datos, backups y restauración; importadores externos cuya documentación esté disponible.

**Criterios:** tests de ida/vuelta, archivos grandes sin disparar RAM, privacidad de integrantes y sumas exactas.

## v0.9 · Conformidad de formatos y distribución

**Depende de:** módulos completos, documentación externa disponible.

- Exportadores legales según estándares oficiales documentados; QR oficiales solo tras verificación.
- Empaquetado Linux/Windows, instalador/migraciones, diagnóstico de inicio y manual final.
- **Integración de sellado real solo como épica independiente**, previa autorización, revisión normativa y confirmación de cada operación.

**Criterios:** validación externa autorizada, smoke tests de instaladores, cero afirmaciones de sellado no comprobado.

## v1.0 · Release integral

- Revisión del catálogo funcional, bugs, accesibilidad, seguridad, documentación y carga real.
- Evaluación crítica del rendimiento y de los modelos; informe de limitaciones de módulos que no puedan ofrecer equivalencia exacta.
- Si algún formato/algoritmo sigue sin especificarse, mantenerlo fuera del release o claramente etiquetado, sin bloquear funciones consolidadas.

## Plantilla de definición de hecho para cada hito

- [ ] Implementación real en el motor, no solo GUI.
- [ ] Casos de error y cancelación.
- [ ] Test unitario, integración y, cuando proceda, propiedad matemática.
- [ ] Prueba manual documentada de interfaz.
- [ ] Rendimiento medido, límites conocidos y consumo de RAM.
- [ ] README, guía de usuario y CHANGELOG actualizados.
- [ ] Matriz de trazabilidad actualizada.
- [ ] Sin cambios incompatibles de schema sin migración y pruebas.
