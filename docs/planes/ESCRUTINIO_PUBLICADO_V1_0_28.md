# Escrutinio publicado con PRE provisional · v1.0.28

## Objetivo

RF-ESC-013: si los quince marcadores ya son finales pero el PRE de WIN1X2
sigue sin reparto, consultar una fuente pública de escrutinio y mostrar el
premio de las apuestas guardadas. El PRE definitivo conserva prioridad.

## Incrementos y aceptación

- [x] Adaptador de red independiente de Qt con timeout y límite de respuesta.
- [x] Comprobar fecha, temporada, jornada, orden de los quince partidos,
  equipos masculinos/femeninos, marcadores, signos, Pleno y seis categorías.
- [x] Consultar en un hilo después del cierre de los 15 partidos; reintentar
  como máximo cada diez minutos si la fuente no está disponible.
- [x] Guardar solo el escrutinio validado con identidad de la jornada para uso
  sin conexión; no modificar PRE, TXT ni apuestas del usuario.
- [x] Mostrar la procedencia del reparto en la tarjeta dorada y mantener el
  estado sin premio si la validación falla.
- [x] Pruebas de la J14 2026-27, identidades contradictorias, importe inválido
  y representación Qt de una apuesta de 11 aciertos.

Fuente secundaria usada: [Comprobar Lotería, jornada del 18/10/2026](https://comprobarloteria.com/quiniela/2026-10-18/),
que reproduce el [escrutinio publicado por SELAE](https://www.loteriasyapuestas.es/es/la-quiniela/escrutinios/la-quiniela-premios-y-ganadores-del-18-de-octubre-de-2026).
La web oficial devuelve HTTP 403 al cliente de escritorio en este equipo.
El adaptador no declara la web secundaria oficial: indica su nombre y exige
que coincidan los quince encuentros y marcadores de la jornada guardada.

Para el sistema `J14_Toni-26-27-J14-v140` presente en la máquina del usuario,
el cálculo sobre 8 apuestas guardadas produce 4 apuestas de 11 aciertos ×
2,22 € = **8,88 €**; dos de 10 aciertos tienen premio unitario 0,00 €.
Esto no acredita que las apuestas se hayan sellado ni que exista derecho de
cobro sin comprobación del resguardo validado.
