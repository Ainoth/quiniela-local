# 11 · Riesgos, incertidumbres y decisiones pendientes

## 1. Decisiones técnicas pendientes con política por defecto

| ID | Cuestión | Estado / decisión por defecto |
|---|---|---|
| DP-01 | Precio por columna y reparto de premios vigente | `GameRuleset` versionado; usar precio demo declarado hasta verificar norma oficial |
| DP-02 | Acceso automático a SELAE | Solo proveedor permitido y documentado; importación manual como fallback |
| DP-03 | Formato oficial ASD(JSON) | No desarrollar conjeturas; recopilar especificación y fixtures autorizadas |
| DP-04 | Formato AD243 y NUM | Igual; adapters desactivados hasta validación |
| DP-05 | QR oficial y boleto físico | No declarar conformidad sin documentación y prueba de validación externa |
| DP-06 | Fórmula de CR de Quiniwin | Desconocida; desarrollar métrica propia, denominarla de otro modo |
| DP-07 | Algoritmos REDWIN, 007R y Tradicional | Desconocidos; construir reductores originales verificables |
| DP-08 | Figuras X-2, Rangos, interrupciones y dibujos | Usar semántica documentada propia o mantener marcado «Por definir» |
| DP-09 | Probabilidad de P15 y dependencia con 1/X/2 | Modelo conjunto especializado, asumir independencia solo en baseline etiquetado |
| DP-10 | Universo sobre el que se calculan garantías | Usuario debe seleccionarlo; por defecto, producto de combinaciones de sistema base, con etiqueta visible |
| DP-11 | Reglas de premios, botes y Elige8 | Motor extensible con reglas vigentes, no copiar parámetros de versiones antiguas |
| DP-12 | Tasas/impuestos y pagos a peñas | Fuera de cálculo financiero base sin reglas verificadas y fecha |
| DP-13 | Integración de sellado por Internet | Épica separada y **apagada** hasta autorización/seguridad/confirmación |
| DP-14 | Datos deportivos históricos/licencias | Inventariar origen y permisos antes de descargar/entrenar |
| DP-15 | Soporte de predicción «IA» | No publicar estimaciones productivas hasta validar fuera de muestra |
| DP-16 | Requisitos de rendimiento | Benchmarks sobre hardware objetivo antes de fijar SLA |
| DP-17 | Ámbito de peñas y datos privados | Definir privacidad, copias y acceso antes de compartir información |
| DP-18 | Apuestas externas en reductores | Necesita semántica explícita y advertencia de que pueden no pertenecer a base |
| DP-19 | Almacenamiento de combinaciones enormes | Streaming/chunks + persistencia segmentada, no guardar todo en una tabla sin estudio |
| DP-20 | Equivalencia con Quiniwin | No es objetivo afirmar clones exactos; se persigue cobertura funcional propia |

## 2. Registro de decisiones (ADR)

Cada decisión no trivial debe quedar en `docs/decisiones/ADR-XXXX-titulo.md` con fecha, contexto, alternativas, decisión, consecuencias, requisitos afectados, pruebas y vínculo al commit. Se permite avanzar sin aclaración del usuario cuando la política por defecto permite crear una versión segura y verificable. No usar supuestos escondidos.

## 3. Riesgos principales

**R1 — Exactitud combinatoria:** un error puede producir costes o garantías falsos. Mitigación: invariantes y verificador independiente.

**R2 — Datos obsoletos:** cambios oficiales, temporadas y fuentes web. Mitigación: metadatos de corte, estado provisional/final y reglas versionadas.

**R3 — Predicción aparente sin fundamento:** riesgo de inducir decisiones basadas en falsos niveles de confianza. Mitigación: backtesting, calibración, baseline, interfaces honestas.

**R4 — Compatibilidad mal entendida:** archivos JSON inventados pueden parecer ASD. Mitigación: namespaces/esquemas propios y bloqueo de formato externo no validado.

**R5 — Legal/IP:** los nombres y algoritmos propietarios no se reproducen; SELAE tiene marcas y normas. Mitigación: implementaciones originales y revisión de autorizaciones/licencias.

**R6 — Consumo descontrolado de recursos:** 76 millones de columnas potenciales con P15. Mitigación: contador algebraico, iteradores, chunked IO, límites y cancelación.

**R7 — Rentabilidad engañosa:** el payout real depende de terceros. Mitigación: intervalos y supuestos, separar oficial/estimado.

**R8 — Complejidad de la interfaz:** decenas de funciones confunden. Mitigación: navegación reducida, modo básico/experto, ayuda contextual.

## 4. Criterios para desbloquear una función externa

Se requieren: (a) especificación y permisos aplicables, (b) fixtures representativas autorizadas, (c) pruebas de conformidad positivas y negativas, (d) validación de seguridad y errores, (e) aviso legal/UX adecuado, (f) caso de éxito reproducible. Sin estas evidencias la función sigue desactivada.
