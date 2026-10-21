# Escrutinio: cambio de sistema y desglose visual · v1.0.29

## Objetivo

RF-ESC-014: al abrir otra quiniela, ocultar inmediatamente todo premio de la
anterior y reconstruirlo solo con las apuestas de la quiniela activa. Mostrar
además una tarjeta compacta con los acertantes e importes unitarios publicados
por categoría, el número de apuestas propias premiadas y su subtotal.

RF-UX-022: renombrar la pestaña y el título «Aciertos» como «Escrutinio», sin
cambiar su índice interno ni la navegación guardada.

## Criterios de aceptación

- [x] El cambio de quiniela desde Mis Sistemas oculta ambas tarjetas de la
  quiniela anterior antes de cualquier evaluación posterior.
- [x] Con escrutinio definitivo, el panel nuevo muestra las seis categorías
  (Pleno al 15 y 14–10), acertantes publicados, premio unitario, apuestas de
  la quiniela activa, subtotal y total en céntimos exactos.
- [x] El panel de desglose también informa cuando el total propio es cero;
  la tarjeta dorada sigue reservada para un total positivo.
- [x] Sin reparto válido, ninguna tarjeta de premios permanece visible.
- [x] La pestaña se llama Escrutinio y conserva la posición anterior.
- [x] Pruebas Qt para cambio desde Mis Sistemas, reparto PRE y reparto
  publicado de la J14 2026-27; captura revisada a 1920×1000.

La tarjeta muestra importes calculados para apuestas guardadas. La validación
del resguardo de una apuesta real continúa fuera del alcance de esta versión.
