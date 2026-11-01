# Previsión orientativa de premios · v2.0.1

## Propósito

Recuperar en el Escrutinio de escritorio la tarjeta de previsión integrada en
la app móvil. La estimación se presenta en una tarjeta dorada independiente
del premio oficial.

## Datos y escenario

- La fuente es la página de estimación de Quinielista. Se extraen recaudación,
  bote, precio de apuesta y porcentajes públicos `quinielista`/`real`.
- Se comprueban temporada y jornada. La descarga tiene timeout y límite de
  respuesta; la última respuesta válida se guarda con la clave de jornada.
- El escenario usa los signos recibidos en directo o introducidos a mano. En
  los partidos pendientes usa el signo con más porcentaje `real`.
- El número esperado de acertantes se calcula con la distribución de
  probabilidades independientes por partido y el tamaño estimado del público.
  El importe por acierto no supera el fondo disponible para la categoría.
- El Pleno se estima con el par de goles de mayor probabilidad cuando no se ha
  recibido un resultado. Las probabilidades local/visitante se combinan como
  independientes, igual que en la app móvil.

## Interfaz

- Tarjeta de previsión con total estimado, recaudación, bote, apuestas propias
  por categoría, importe unitario y subtotal.
- Resumen de la mejor apuesta con aciertos confirmados, aciertos provisionales,
  fallos confirmados y partidos pendientes.
- Actualización en segundo plano al abrir Escrutinio y cada diez minutos,
  además de un botón manual. La caché se conserva por jornada.
- Cuando existe reparto definitivo, la estimación se oculta y se muestra la
  tarjeta oficial y su desglose, sin mezclar importes estimados y publicados.

La cifra es orientativa, depende del escenario y de los porcentajes publicados,
y no confirma un premio ni el cobro de apuestas.

## Verificación

- Pruebas de lectura de temporada, recaudación, porcentajes y Pleno.
- Rechazo de jornadas distintas y escenarios inválidos.
- Cálculo de premios propios en categorías 14 y 15.
- Representación Qt del resumen y de la tarjeta dorada.
