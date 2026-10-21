# SSeguidos · v1.0.26

## Objetivo y trazabilidad

RF-UX-021: alinear visualmente Reducciones → SSeguidos con el panel compacto de
Cuenta, retirando el fondo ornamental y haciendo más denso el selector de
temporadas. No modifica el dominio ni la semántica del filtro de rachas.

## Cambios y aceptación

- [x] Lienzo SSeguidos con fondo azul oscuro plano, sin textura ni círculos.
- [x] Temporadas en dos columnas y con menor altura para dejar visible más
  contenido histórico en el mismo espacio.
- [x] Mantener Manual/Azar/Automática, controles de rachas, estado compartido,
  y la activación exterior independiente.
- [x] Capturar la vista Automática junto a la referencia original y ejecutar
  regresiones Qt del filtro y del estado.

La estética clásica de bordes, celdas blancas/verdes y listas sigue intacta;
solo se elimina el fondo ornamental de SSeguidos.
