# Plan · identidad común de equipos y partidos · v1.0.37

## RF-DAT-008

Evitar que cambios de acentos, puntuación, abreviaturas, sufijos oficiales y
erratas tipográficas habituales entre proveedores bloqueen una jornada válida.
Aplicar una sola normalización en descarga de calendarios, porcentajes,
marcadores, escrutinios y archivos de probabilidades.

## Trabajo

1. Crear un normalizador puro en `domain` que canonicalice formato y aliases,
   conserve los rasgos de identidad (categoría femenina, equipos B/II y
   calificadores de edad) y permita una tolerancia tipográfica acotada.
2. Sustituir las normalizaciones duplicadas en adaptadores de Quinielista,
   ESPN y escrutinio; usar la misma regla al importar porcentajes y al
   reconciliar una jornada local actualizada.
3. Conservar el orden y número del partido como parte de la validación: el
   nombre tolerante nunca reordena encuentros ni mezcla local/visitante.
4. Añadir pruebas positivas de nombres equivalentes y negativas de equipos
   homónimos, filiales, categorías distintas, partidos invertidos y jornadas
   reordenadas.
5. Documentar aliases explícitos, la tolerancia y sus límites.

## Criterios de aceptación

- Los nombres aceptados comparten una única función de identidad en el código
  modular; no hay tablas independientes para ESPN y Quiniela.
- Acentos, mayúsculas, signos de puntuación, abreviaturas reconocidas,
  sufijos legales y una errata de un carácter en un token significativo se
  toleran.
- No se confunden clubes distintos, primer equipo con filial, ni femenino con
  masculino cuando la fuente identifica expresamente la categoría.
- La lista de partidos debe seguir teniendo 15 filas en orden; cada fila debe
  validar local con local y visitante con visitante.
- Los errores restantes identifican jornada, número y nombres esperados y
  recibidos; no invalidan resultados válidos de otros encuentros.
- Pruebas, lint y comprobación de arranque completan sin regresiones.

## Decisión

Los aliases oficiales y los apodos/abreviaturas se convierten en un nombre
canónico. La tolerancia difusa se limita a una edición por token y solo si se
conservan cantidad/orden de tokens y calificadores de categoría. Una marca de
categoría femenina ausente solo se admite en adaptadores que ya han identificado
la competición femenina, como el feed ESPN de Liga F. No se usa semejanza
parcial libre ni se intenta adivinar una fila ausente.
