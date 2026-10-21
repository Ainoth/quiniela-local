# Cuenta unificada · v1.0.33

RF-UX-026: una composición común en Manual/Azar/Automática, sin duplicar
temporadas o distribución y sin tablas de reservas carentes de cálculo.
Paneles alineados, controles legibles y todo el ancho dentro del escritorio.

RF-UX-027: selector único de temporadas con casillas verdes, selección por
temporada completa, búsqueda, accesos Últimas 5/10, Todas/Ninguna y resumen
de temporadas y jornadas válidas. Los accesos se aplican en un solo lote y
conservan las temporadas ocultas por una búsqueda. La recomendación histórica
continúa usando exclusivamente los registros seleccionados.

RF-FIL-026: distancia entre X conserva la diferencia de posiciones entre
apariciones consecutivas. Ejemplo X1X = 2; con menos de dos X no descarta.
Mostrar su estado real y comprobar el efecto mediante apuestas de referencia.

RF-UX-028: todos los selectores de riesgo de Qt usan botones exclusivos con
el nivel seleccionado resaltado; se conservan niveles, fórmulas y etiquetas
de versiones anteriores. También se sustituyen los radios de SSeguidos y
FSSeguidos por botones del mismo estilo, adaptados a su columna estrecha.

Aceptación: sin desplazamiento horizontal a 1920×1080, mismo selector en los
tres métodos, cuadrados verdes sincronizados, ninguna estadística simulada,
pruebas de selección por lotes y filtro real, captura con Automática abierta.

## Validación

- 43 pruebas dirigidas de controles de selección, interfaz de reducciones,
  generador Normal e integración de filtros. Se actualizó la expectativa
  visual antigua de celdas de 24 px a las nuevas celdas de 36 px.
- Casos de referencia de Distancia X: X1X cumple distancia 2; X11X incumple
  ese mismo rango. Apagar Cuenta conserva los ajustes y excluye el filtro.
- Prueba de geometría: resumen fuera del área desplazable, filtro completo
  dentro del lienzo y ancho de Cuenta inferior al área derecha a 1920×1040.
- Capturas [Manual](../validacion_visual/v1_0_33/cuenta_manual.png) y
  [Automática](../validacion_visual/v1_0_33/cuenta_automatica.png), reproducibles
  con `QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv-studio/bin/python scripts/capture_cuenta_unificada.py`.
- Ruff completo limpio en los módulos y pruebas nuevos; comprobación E9/F/I
  limpia en la ventana. La ventana conserva 16 avisos de estilo previos fuera
  del alcance de esta entrega. `--self-check` verifica SQLite y cálculos.

Los resúmenes son descriptivos del histórico seleccionado. No se ha definido
ni simulado el cálculo de reservas o sumas del programa antiguo.
