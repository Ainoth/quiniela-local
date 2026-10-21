# Escrutinio de premios · v1.0.27

## Objetivo

RF-ESC-012: presentar el dinero calculado a partir de un escrutinio publicado
para las apuestas guardadas, con desglose de categorías y copias, y cargar el
PRE local de la jornada al abrir Aciertos cuando esté disponible.

## Criterios de aceptación

- [x] Con resultado parcial o manual sin escrutinio publicado, no se anuncia
  dinero ganado; se indica que falta el escrutinio.
- [x] Con PRE definitivo válido, se muestran categoría, apuestas acertantes,
  importe unitario, subtotal y total; el Pleno al 15 suma su categoría a los
  14 aciertos según el motor existente.
- [x] El aviso destacado solo aparece cuando el total supera cero.
- [x] Al cambiar de jornada o de sistema, el premio anterior no permanece.
- [x] Un PRE ausente, incompleto o de equipos distintos no se anuncia como
  premio; el error de identidad se muestra de forma comprensible.
- [x] Las pruebas cubren categorías, copias, Pleno, parcial, cero premios,
  carga automática de PRE y cambio de jornada.

El valor describe apuestas guardadas en la app. La app no acredita que se
hayan sellado ni que SELAE haya pagado un premio; la comprobación del boleto
validado sigue siendo necesaria.

Capturas con PRE **sintético**, no una apuesta real:
[ventana amplia](../validacion_visual/escrutinio_premios_v1_0_27.png) y
[ventana compacta](../validacion_visual/escrutinio_premios_compacto_v1_0_27.png).
