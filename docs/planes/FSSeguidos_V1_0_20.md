# FSSeguidos · v1.0.20

## Objetivo

RF-UX-016 / RF-FIL-022: permitir filtrar particiones exactas de rachas
máximas mediante una subpestaña separada de SSeguidos.

## Implementación

- [x] Añadir FSSeguidos como subpestaña visible de Reducciones, con su propio
  cuadrado exterior apagado por defecto.
- [x] Crear Manual/Azar/Automática con cuatro paneles compactos `1/X/2/V`;
  total numérico, lista Qt multiselección y cuadrado Aplicar por signo.
- [x] Enumerar particiones alcanzables desde la base. X/2 forman la clase V;
  los primeros 14 partidos se analizan y el Pleno se excluye.
- [x] Azar muestrea terminaciones de la base con semilla repetible.
- [x] Automática cuenta resultados reales del histórico integrado por
  temporada y recomienda figuras compatibles con la base.
- [x] Persistir selección por total, total actualmente visible, activaciones,
  método, riesgo, semilla y temporadas.
- [x] Conservar SSeguidos como filtro independiente de máximos y frecuencias.

## Criterios matemáticos

- Una figura ordena de mayor a menor las longitudes de las rachas máximas.
- La suma de sus partes debe coincidir con el total seleccionado.
- Para V, X y 2 son miembros de la misma familia y pueden alternarse dentro de
  una racha.
- Aplicar un signo solo compara su total visible y sus figuras seleccionadas;
  cambiar el total no borra las listas previas.
- La activación de la subpestaña y el cuadrado Aplicar por signo son
  independientes. Ninguna selección se aplica de forma predeterminada.

## Pruebas

`test_fsseguidos_filters_exact_partition_separately_and_persists` verifica la
partición `3-2-1-1`, su rechazo frente a `4-3`, el control exterior y la
restauración Qt. `test_fsseguidos_automatic_uses_integrated_history_and_azar_repeats_seed`
verifica estadísticas reales y reproducción por semilla.
