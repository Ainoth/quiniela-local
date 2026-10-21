# v1.0.32 · Flujo Normal y Cuenta

## Objetivo
Hacer visible el orden de trabajo y el origen efectivo de los porcentajes sin alterar el boleto izquierdo. Ordenar Cuenta y distinguir filtros operativos de estadísticas aún no definidas.

## Entregas comprobables
- Normal: fuente de la matriz explícita, pasos de descarga/selección, asignación, relleno, generación y exportación con ayuda contextual; ponderaciones identificadas como fuentes auxiliares importadas.
- Cuenta: composición alineada, sin controles superpuestos; Distancia X con estado y alcance claros; estadísticas no implementadas etiquetadas como tales.
- Barra inferior: actividad indeterminada durante operaciones de red y progreso determinado durante generación.
- Pruebas Qt para selección de fuente y flujo, más comprobación visual.

## Criterios de aceptación
La matriz que se usa al rellenar corresponde a la fuente indicada; las ponderaciones sólo intervienen tras recalcular con datos importados; el boleto permanece intacto; Distancia X se aplica a la reducción cuando se activa; la barra indica tareas en curso y se restaura al terminar.
