# Porcentajes descargables y transparentes — 13/10/2026

RF-JOR-007, RF-PRO-001, RF-PRO-002, RF-PRO-008.

Problema: «Usar los últimos datos» solo adoptaba fuentes en SQLite; no hacía
peticiones. El XML completo publicado ya contenía mercado, pero el importador
solo leía popularidad de Quinielista. Mercado quedaba ausente y las plantillas
podían usar orden 1/X/2 sin avisarlo en el constructor.

Incremento: descarga asíncrona para la jornada abierta, lectura separada de
`p_jugados_*` y `p_bf_*desc` (alternativa `p_bf_*` cuando no hay decimales),
validación de temporada, jornada, 15 equipos y probabilidades de los 14 signos.
Actualización explícita versionada sin modificar apuestas, precio ni bloqueos.
Jornada o versión cambiada, cancelación, error de red o datos inválidos no deben
aplicar porcentajes al sistema. Las versiones anteriores conservan sus fuentes.

Interfaz: origen y hora de **captura** visibles; no confundir con la hora de
publicación. Fuente ausente produce un mensaje, nunca inventa probabilidades.
La demo sigue siendo sintética y no se descarga. Descargar no selecciona signos;
«Cambiar el boleto» los aplica respetando bloqueos, como acción independiente.

Fuente comprobada: el proveedor publica XML/CSV y distingue mercado, LAE y
Quinielista en https://www.eduardolosilla.es/quiniela/ayudas/porcentajes .
Se mantiene el XML completo ya utilizado, sin credenciales ni evasión de acceso.
Football-Data (https://www.football-data.co.uk/downloadm.php) ofrece CSV históricos
para evaluación, pero no se integra: requiere correspondencia de equipos,
cobertura de competiciones y fechas, y permisos revisados. No se promete mayor
tasa de acierto ni equivalencia a una IA calibrada. LAE separado y predicción
del Pleno siguen fuera de este incremento.

Aceptación: pruebas de mercado/público distintos, ausencia/invalidez, identidad,
descarga de jornada exacta, conservación ante error/cambio y aplicación guiada;
suite Studio, pruebas históricas y arranque nativo. Android no se modifica.

Validación realizada: 151 pruebas Studio y 32 históricas (GUI incluida),
self-check SQLite/cálculos y arranque Qt nativo correctos. Ruff E9/F/I correcto
en los archivos tocados; otras advertencias previas de estilo de la ventana
(B008/BLE001/C408/B023) quedan fuera de este cambio.
Descarga real 26-27/J13: primer partido mercado 45,68 / 26,62 / 27,70 y
popularidad 49,89 / 27,69 / 22,42; identidad y equipos comprobados. Esta
comprobación demuestra lectura correcta, no precisión predictiva superior.
