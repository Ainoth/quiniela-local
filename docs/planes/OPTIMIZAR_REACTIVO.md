# Optimizar reactivo — 0.1.7

RF-FIL-001/009 y RF-RED-001/002. Barra independiente de Crear: cada cambio
recalcula apuestas exactas y coste a partir del origen, con debounce, trabajador
cancelable y descarte de resultados obsoletos. Sin botones para confirmar el
nivel ni aplicar condiciones. Las condiciones manuales también recalculan.
Presupuesto al final: solo se aplica al resultado ya filtrado, por acción explícita.

Reducir textos a nivel, condiciones, resultado y presupuesto. Cero coincidencias
es un resultado válido, recuperable al ampliar filtros. Preservar precio, Plenos,
cantidades y versiones; cerrar/cambiar de sistema no aplica tareas antiguas.
Pruebas: reacción real, independencia de sliders, ampliación/resultado vacío,
última petición prevalece, presupuesto final y cancelación/cierre.

Resultado: 100 pruebas Studio y 32 históricas con GUI correctas; Ruff, Qt/X11
y paquete aislado verificados. Presupuesto visible al final en captura revisada.
Cambios: ui/window.py, application/services.py, domain/filters.py, infraestructura
de archivos, pruebas y documentación. No se implementan nuevos reductores ni IA.
