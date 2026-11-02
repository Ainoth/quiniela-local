# Escrutinio: análisis de fallos y reducciones — v2.0.8

## Requisito

**RF-ESC-016.** Con los 14 resultados definitivos disponibles, Escrutinio
permite consultar dónde falló la mejor apuesta y si la combinación ganadora
quedó fuera al aplicar una reducción guardada. El informe identifica la
revisión, el nombre de la pestaña y el valor observado frente a la condición
guardada (por ejemplo, Cuenta o SSeguidos). El panel permanece plegado hasta
que se solicite.

## Reglas de atribución

- El diagnóstico de partidos compara la apuesta con el resultado real y muestra
  el número, los equipos y ambos signos.
- Las reducciones solo reciben crédito por excluir la combinación ganadora si
  esta figura en el desarrollo de origen y se encuentra una revisión cuyo
  conjunto de entrada la contenía y cuya salida ya no la contiene.
- Si no estaba en el desarrollo original, se informa que no se puede culpar a
  una reducción. Si pasó por las reducciones, se indica que pudo quedar fuera
  durante la selección posterior de cartera u otro paso.
- Para la columna ganadora se listan todas las condiciones activas que fallan
  en la revisión identificada. Las cantidades, rachas y figuras muestran valor
  observado y criterio permitido.
- Los ficheros externos no llevan historial de filtros de esta app; solo se
  detallan sus partidos fallados.
- Es una explicación del estado guardado en Quiniela AI Studio, no una
  equivalencia con el comportamiento de WIN1X2 ni una predicción.

## Interfaz

Escrutinio conserva los marcadores y las tarjetas en la zona superior. El
resumen de mejor apuesta usa una fila baja; previsión y estado oficial quedan
en dos tarjetas de altura legible. El detalle de apuestas y el diagnóstico de
fallos son desplegables independientes, ambos cerrados al entrar.

## Aceptación

- La tarjeta oficial pendiente muestra «No publicado» por categoría.
- La tabla de apuestas empieza oculta y sigue accesible con su botón.
- El diagnóstico indica partido/signo fallado y atribuye una exclusión
  únicamente cuando puede demostrarla desde las revisiones guardadas.
- Pruebas deterministas para FSSeguidos y panel plegable; suite de Escrutinio.
