# Entrega v1.0.0 (solicitada inicialmente como v0.1.14)

RF-RED-002, RF-GAR-001/002/003, RF-PRO-005, RF-ARC-009, RF-AUD-001.

Diagnóstico v0.1.13: `domain.engine.optimize` agrega apuestas por signos/Pleno,
ordena por probabilidad de 14 (o lexicográficamente sin datos) y consume el
presupuesto, incluyendo cantidades repetidas. No usa cobertura marginal,
distancia ni intercambio, ni certifica optimalidad. Pleno no entra en su ranking.

Plan de ejecución: motor independiente de cobertura, cartera greedy/intercambio
y exhaustivo limitado; muestreo reproducible para universos grandes. Verificador
separado, bases/universos explícitos, métricas exactas/estimadas y auditoría.
Interfaz asíncrona, vista previa antes de aplicar, comparación con estrategias
de igual presupuesto; conservar filtros. Asistente TuLotero manual con perfiles
configurables, agrupación sin modificar Plenos, TXT/CSV con relectura.
Pleno manual predeterminado y automatismo solo explícito; modelo marginal
independiente de goles opcional, sin confundirlo con distribución conjunta real.

## Continuación en el equipo de casa

RF-RED-002/RF-AUD-001/RF-PRO-001: corregir comparaciones atrapadas en grupos
de Pleno, auditar inicio/cancelación/error con el mismo ID de ejecución, validar
enteros extremos sin OverflowError y mostrar cancelación/progreso en Optimizar.
RF-UX-001: parámetros avanzados dentro del área desplazable; los controles de
presupuesto no deben quedar ocultos a 1024×768. Criterios: regresión contra
oráculo exhaustivo de cardinalidades, cancelación real en Qt sin modificar
apuestas, errores de dominio explícitos y suites completas sin regresiones.

Fuentes revisadas 13/10/2026:
- https://tulotero.es/jugar-quiniela/ : mínimo dos apuestas para validar, hasta
  ocho sencillas por boleto y un Pleno común. Perfil versionado configurable,
  no afirmar importación automática de TXT/CSV ni enviar/pagar apuestas.
- https://www.loteriasyapuestas.es/es/paginas-informativas/quinielas-reducidas-maximiza-tus-posibilidades : mantiene las seis modalidades y remite al BOE 2009.
  Reutilizar matrices transcritas, verificar sobre las columnas reales.

Aceptación: 72 columnas/5€/75c -> ≤6 únicas; reducción 3, 216 escenarios y 24
columnas, garantía condicional independiente; exportación por Pleno 2–8 por
boleto con relectura exacta; reproducción/cancelación/ausencia de datos; no
migrar destructivamente y excluir los cuatro TXT personales. Objetivo de valor
esperado desactivado sin recaudación/reparto/modelo de acertantes fiable.
