# Cuenta: composición clásica compacta v1.0.25

## Objetivo

Aplicar el checklist descargado de Cuenta a la subpestaña Manual y compararla
con `00_OBJETIVO_ORIGINAL_MANUAL.png`. Se reconstruye el interior como tres
bloques contiguos, conservando el motor de Cuenta y el aspecto oscuro general.

## Composición

- Izquierda: Variantes, Equis, Doses; valores históricos dentro de las casillas,
  controles individuales, Aplicar general, icono de frecuencias y acciones
  Marcar Todos / Inicializar. Se ven 0–15; 15 está inhabilitado al contar solo
  los catorce signos de la quiniela.
- Centro: Figuras conjuntas observadas (Veces/V/X/2), con fondo blanco, Aplicar
  propio y acciones independientes.
- Derecha: porcentajes 1/X/2 agrupados por temporada en una tabla vertical. La
  selección de cada temporada se sincroniza con Automática y recalcula las
  estadísticas existentes. Debajo se integran FILTROS, la distancia entre
  equis ya implementada y la tabla clásica de diez sumas.

## Decisiones y límites honestos

- Los porcentajes por temporada se derivan de los `results14` cargados; no son
  valores de ejemplo ni predicciones.
- La fila 15 se representa visualmente, pero no puede seleccionarse ni entrar
  en las reglas, porque el Pleno no forma parte del recuento.
- La separación entre equis permanece conectada al filtro existente. Los
  controles `Ap. Filtros`, `Obtener %`, `Aplicar` y la tabla coloreada de
  reservas/medias se muestran para completar la estructura; quedan vacíos e
  inhabilitados porque el proyecto aún no define su semántica ni su motor.
- Manual se compara visualmente con la captura Manual original. Azar y
  Automática conservan sus paneles y cálculos, incluido su selector de
  temporadas. El lienzo se reduce a 700 px solo en Manual/Azar; Automática
  recupera 1140 px para no recortar la banda de temporada y recomendación.

## Verificación y artefactos

- `tests/studio/test_advanced_conditions_ui.py`: presencia de 0–15, lista de
  figuras, diez filas de sumas, acciones separadas y sincronización de
  temporadas con estadísticas históricas; regresión de los tres modos.
- Captura y comparación repetibles con
  `QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv-studio/bin/python
  scripts/capture_cuenta_manual.py`.
- Evidencia: `docs/validacion_visual/cuenta_v1_0_25/`.

Requisito: RF-UX-020. La visualización queda implementada con diferencias
funcionales documentadas en los controles históricos de reserva/media.
