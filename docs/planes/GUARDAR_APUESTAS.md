# Guardar apuestas y preparar su carga manual — 0.1.9

## Objetivo

RF-ARC-009: encontrar el guardado desde cualquier pestaña, identificar qué
quiniela se exporta y recibir pasos concretos para cargar el TXT manualmente.
No se implementa envío automático, pago ni validación de apuestas reales.

## Incremento y aceptación

- Botón global para las apuestas exactas de la quiniela abierta.
- Mis Sistemas guarda la fila seleccionada, aunque esté abierta otra quiniela.
  También se corrige el guardado JSON de la fila elegida.
- Una reducida u optimizada se exporta tal cual, sin generar de nuevo el boleto.
  El número de líneas incluye copias y todas las parejas del Pleno.
- Guardado atómico existente; nombre sugerido con jornada y revisión, carpeta
  recordada y confirmación con cantidad, coste de referencia y ruta.
- Botones explícitos para abrir carpeta o la página pública de carga; ningún
  archivo se sube automáticamente. Demo y jornadas de consulta no abren la web.
- Impedir guardar la selección anterior mientras se recalculan las condiciones.
- Pruebas de selección distinta de la abierta, reducción con Plenos múltiples,
  coste congelado, cancelación, recalculado y navegación solo por clic.

## Fuente externa consultada

El 12/10/2026 se comprueban la [página de archivos de Quinielista](https://www.eduardolosilla.es/quiniela/archivos)
y su [muestra TXT](https://www.eduardolosilla.es/assets/archivos/1x2.txt):
una apuesta por línea, 14 signos y dos goles. Se contrasta el contenido, sin
cargar archivos reales ni asegurar aceptación por otros proveedores. La web
pide archivo y número de apuestas, y gestiona jornada, precio y pago.

RF-BOL-005 continúa pendiente: la navegación manual no es una integración
autorizada de envío con confirmación y recibo. Windows sigue sin prueba nativa.

## Resultado comprobado

Implementado y documentado como RF-ARC-009. 137 pruebas Studio y 32 históricas
con GUI correctas; Ruff, self-check, arranque nativo y wheel aislada correctos.
El guardado no altera el sistema abierto ni sube archivos a un proveedor.
