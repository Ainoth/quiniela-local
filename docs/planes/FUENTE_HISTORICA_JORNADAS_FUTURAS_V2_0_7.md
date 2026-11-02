# RF-DAT-009 / RF-NOR-008 — fuente histórica y jornadas futuras

## Objetivos

- Permitir preparar jornadas futuras antes de su apertura oficial de venta.
- Descargar probabilidades públicas indicando temporada y jornada.
- Añadir una fuente local basada en temporadas históricas seleccionadas.

## Decisiones

- Una jornada futura es editable hasta su `editable_until`; después vuelve a ser
  de consulta. El diálogo de exportación sigue impidiendo abrir la web de venta
  mientras no esté en curso.
- Porcentajes jugados y probabilidad real de mercado se consultan por separado
  en la API de Eduardo Losilla; el parser valida temporada, jornada, orden y
  equipos antes de guardar cualquiera de las dos capturas.
- El método histórico provisional cuenta `1/X/2` por posición del boleto en
  todas las jornadas finales de las temporadas elegidas. Es descriptivo, no
  está calibrado y no modela equipos ni competición.

## Criterios de aceptación

- Un round futuro con fecha límite vigente permite crear un sistema; uno cerrado
  o pasado continúa en solo consulta.
- Los porcentajes actuales y futuros se descargan con los identificadores
  exactos de temporada y jornada. Un calendario distinto no modifica caché.
- Fuente → Histórico calcula una fila 1/X/2 por cada uno de los 14 partidos,
  usa exclusivamente las temporadas elegidas y permite editar la matriz
  resultante sin alterar el histórico original.
- El UI identifica el método como frecuencias observadas y no lo llama
  pronóstico.

## Verificación

Pruebas deterministas con XML sintético para identidad/calendario, matriz
histórica por posición y selección de temporada en la interfaz. Comprobación
manual de la API pública para una jornada futura.
