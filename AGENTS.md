# Instrucciones permanentes para Codex

## Misión y fuentes de verdad

Construir **Quiniela AI Studio**, una app de escritorio Linux/Windows en español, a partir de esta especificación. Lee primero `README.md`, `docs/00_INDICE.md` y los documentos específicos de tu tarea. Si hay contradicciones: seguridad y reglas oficiales vigentes > especificación formal de dominio > decisiones registradas > requisitos funcionales > ejemplos ilustrativos. No utilices como reglas los números de un historial de cambios antiguo.

## Forma de trabajo

1. Analiza el estado real del repositorio antes de editar. Para una tarea grande, crea o actualiza un plan en `docs/planes/` con objetivos, subtareas y criterios de aceptación.
2. Entrega **incrementos pequeños, ejecutables y comprobables**; prioriza la primera versión definida en `docs/08_PLAN_VERSIONES.md`. No simules que todo está implementado.
3. Mantén separación `domain` / `application` / `infrastructure` / `ui`; la lógica de negocio no importa módulos de Qt, proveedores web ni persistencia.
4. Cada requisito nuevo o modificado lleva identificador `RF-...`, pruebas y documentación. Actualiza `docs/12_MATRIZ_TRAZABILIDAD.md` y `CHANGELOG.md` si existen.
5. Si una fórmula/algoritmo no está especificado, etiquétalo como **original/provisional**, crea prueba de referencia y registra la decisión; nunca afirmes equivalencia a REDWIN o CR de terceros.
6. No generes predicciones con un LLM sin modelo calibrado y evaluación retrospectiva. Si faltan datos, ofrece modo demo y muestra claramente sus limitaciones.
7. Las dependencias externas deben quedar encapsuladas en adaptadores; soporta modo offline y errores de red sin bloquear la interfaz.
8. Ninguna integración de sellado, pago o envío de apuestas reales se activa por defecto. Requiere proveedor autorizado, validación de formato y confirmación explícita del usuario.
9. No guardes secretos en Git ni en logs. Usa directorios del usuario (`platformdirs`) y configuración portable; no hardcodees rutas o credenciales.
10. Evita interfaces saturadas: inicio, crear, optimizar, analizar, escrutar, mis sistemas, configuración; opciones avanzadas plegadas.

## Calidad mínima por entrega

- Código con tipos y docstrings en cálculos delicados; `pytest` para dominio y adaptadores; `ruff` para estilo; comprobación de tipos cuando esté configurada.
- Pruebas deterministas para combinatoria, filtros, garantías, costes y serialización. Usa semillas fijas y fixtures versionadas.
- Ejecuta los comandos de prueba existentes; si algo no puede ejecutarse, especifica por qué y cómo reproducirlo.
- No ocultes errores; muestra mensajes claros al usuario, progreso/cancelación en cálculos largos y un registro de auditoría comprensible.
- Da al final de cada tarea: archivos cambiados, funciones implementadas, pruebas ejecutadas, limitaciones y siguiente fase. No declares funcionalidades ausentes como completadas.

## Primera tarea

Sigue `CODEX_EMPEZAR_AQUI.md` y `docs/08_PLAN_VERSIONES.md`; desarrolla **solo v0.1** como vertical end-to-end inicial. Consulta el catálogo completo para preservar la extensibilidad, pero no intentes desarrollar todos los reductores y filtros de una sola vez.
