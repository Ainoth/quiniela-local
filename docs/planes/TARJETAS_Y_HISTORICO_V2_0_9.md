# Tarjetas de escrutinio y temporadas históricas — v2.0.9

## Objetivos

- RF-ESC-017: compartir la estructura de seis filas entre previsión y premios
  oficiales, usando dorado para la estimación y verde para el dato publicado.
- RF-ESC-017: compactar los metadatos de la previsión en el pie de la tarjeta.
- RF-UX-031: presentar el generador como «Quiniela», explicar el estado de las
  ponderaciones auxiliares y facilitar la selección de temporadas históricas.

## Criterios de aceptación

- La previsión muestra sus seis categorías, importe y una sola línea inferior
  con estado, recaudación, bote, hora y fuente.
- La tarjeta oficial presenta las mismas categorías y métricas, con color verde;
  cada categoría pendiente indica «No publicado».
- El usuario distingue matriz sin ponderar, ponderación aplicada y cambios
  posteriores a la aplicación.
- Una configuración histórica nueva incluye todas las temporadas con jornadas
  finalizadas; el selector permite limitar la selección.

## Limitación

La aplicación de ponderaciones cambia la matriz visible. Para trasladarla al
boleto hay que pulsar «Rellenar quiniela base». La frecuencia histórica sigue
siendo descriptiva y no constituye una predicción calibrada.
