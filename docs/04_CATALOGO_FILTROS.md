# 04 · Catálogo de filtros (especificación implementable)

El historial de Quiniwin enumera filtros pero no siempre sus parámetros matemáticos. Aquí se define la **semántica original propuesta** para implementarlos de forma verificable. Las funciones cuya equivalencia exacta es indeterminada quedan marcadas con `POR DEFINIR` para una compatibilidad futura, nunca se atribuyen al producto tercero.

## 1. Contrato común

Para cada filtro: `id`, `version`, `enabled`, `description`, `match_scope`, `parameters`, `validation`, `evaluate(column, context)`, `explain(column, context)`, `estimate_cost`, `data_requirements`. Los parámetros se serializan con una versión de esquema. `match_scope` por defecto son los 14 partidos; el Pleno al 15 entra solo en filtros que lo declaren.

- Evaluación en streaming, por lotes con máscara booleana y estadísticas exactas.
- Combinar filtros duros mediante `AND`; el orden afecta el rendimiento y el informe de eliminación **pero no el resultado** si no hay reservas ni estado dependiente del orden.
- Para auditar descartes, guardar `first_failed_filter` y opcionalmente `all_failed_filters`; las sumas de eliminaciones **por primer fallo** coinciden con el total descartado, las de todos los fallos pueden solaparse.
- Un filtro vacío/deshabilitado no modifica el resultado. Un filtro activo inválido bloquea el cálculo con explicación.
- `RESERVAS`: semántica propuesta `count_failed(reserve_conditions)<=K` por grupo; cada condición tiene ID único y peso opcional *solo en una versión posterior*. La activación global de un filtro desactiva también sus entradas en reservas. Registro de grupos A..J para compatibilidad conceptual, sin asumir los límites internos del tercero.
- Los intervalos `[min,max]` son inclusivos salvo que se indique lo contrario. Cualquier límite imposible debe detectarse antes de iniciar el trabajo.

## 2. Inventario y semántica

| ID | Filtro | Especificación original propuesta | Dependencias | Estado |
|---|---|---|---|---|
| FIL-01 | Conteo de signos | `min_s <= #signos(s en posiciones) <= max_s`, `s∈{1,X,2}` | Columna | REQUERIDO |
| FIL-02 | Variantes | Variante = `X o 2`; rango sobre número total/posiciones | Columna | REQUERIDO |
| FIL-03 | Secuencias | Coincidencia de patrones ordenados de signos, máximo/mínimo de apariciones, con o sin solape | Columna | REQUERIDO |
| FIL-04 | Signos seguidos | Longitud máxima/mínima de rachas de 1, X, 2 o variantes | Columna | REQUERIDO |
| FIL-05 | Interrupciones | Número de transiciones `predicado(si)!=predicado(si+1)` en posiciones consecutivas seleccionadas | Columna | PROPUESTO |
| FIL-06 | Parejas | Conteos de patrones en parejas de índices declaradas (disjuntas o solapadas) | Columna + grupos | REQUERIDO |
| FIL-07 | Tríos | Igual que parejas, con grupos de 3 índices | Columna + grupos | REQUERIDO |
| FIL-08 | Cuartetos | Igual, grupos de 4 índices | Columna + grupos | REQUERIDO |
| FIL-09 | Quintetos | Igual, grupos de 5 índices | Columna + grupos | REQUERIDO |
| FIL-10 | Sextetos | Igual, grupos de 6 índices | Columna + grupos | REQUERIDO |
| FIL-11 | Septetos | Igual, grupos de 7 índices | Columna + grupos | REQUERIDO |
| FIL-12 | Parejas por partido | Para índice ancla, contar patrones de pareja contra índices seleccionados | Columna + grupos | REQUERIDO |
| FIL-13 | Columnas Base (CB) | Aciertos respecto a una referencia de signos únicos `hits14` en scope; con referencia múltiple, acierto si signo∈máscara | CB + máscaras | REQUERIDO |
| FIL-14 | Fallos seguidos CB | Máximo número de posiciones consecutivas que no coinciden con la referencia CB | CB | REQUERIDO |
| FIL-15 | Sumas de CB | Sumar aciertos frente a lista de referencias, aplicar rangos y operadores sobre suma | CB + grupos | REQUERIDO |
| FIL-16 | Grupos de CB | Para un grupo de hasta N referencias, contar cuántas CB cumplen una condición de aciertos | CB + grupos | REQUERIDO |
| FIL-17 | CB relacionadas | Relacionar resultados de coincidencia con varias CB con expresiones AND/OR/suma/diferencia | CB | PROPUESTO |
| FIL-18 | Diferencias | Distancia de Hamming y/o signos cambiados con respecto a referencia; seleccionar scope | CB | REQUERIDO |
| FIL-19 | Coincidencias | Contar posiciones donde columna coincide con una o varias máscaras/referencias | CB + máscaras | REQUERIDO |
| FIL-20 | Grupos generales | Reglas de signo, secuencia y coincidencia aplicadas a subconjuntos de partidos con nombre | Grupos | REQUERIDO |
| FIL-21 | Figuras X-2 | Vector `(nX,n2)` por agrupación seleccionada y lista de figuras admitidas; definición exacta del tercero indeterminada | Columna | PROPUESTO |
| FIL-22 | Dibujos de variantes | Representación binaria de X/2/variante en posiciones; aceptar/descartar máscaras o familias explícitas | Columna | PROPUESTO |
| FIL-23 | Valoraciones suma | `V=Σ_i w[i,signo_i]`, dentro de rangos | Matriz de pesos | REQUERIDO |
| FIL-24 | Valoraciones producto | `V=∏_i w[i,signo_i]`; usar log solo con `w>0`; definir ceros/negativos con errores o modo explícito | Matriz de pesos | REQUERIDO |
| FIL-25 | Valoraciones logaritmos | Suma de logaritmos positivos; fijar base y comportamiento con cero | Matriz de pesos | PROPUESTO |
| FIL-26 | Rangos | Rango de probabilidad de premio/acertantes **según estimador versionado**; nunca activarlo sin proveedor/modelo | Estimador | POR DEFINIR |
| FIL-27 | Coeficiente de Rentabilidad (CR) | Rango de una puntuación/EV **propia**, incluyendo versión y supuestos | Estimador premios | PROPUESTO |
| FIL-28 | IF THEN | Si antecedente lógico sobre posiciones/CB es verdadero, evaluar consecuente lógico; implicación `!A or B` | Expresiones | REQUERIDO |
| FIL-29 | Grupos relacionados | Relaciones entre recuentos/aciertos de grupos (sumas, intervalos, condiciones) | Grupos | PROPUESTO |
| FIL-30 | Reservas | Tolerancia a incumplimientos, sobre grupos de filtros activados | Filtros previos | PROPUESTO |
| FIL-31 | Probabilidad | `min <= logP(c) <= max` o percentil con distribución explícita | Probabilidades | REQUERIDO |
| FIL-32 | Signo del Pleno | Restringir pareja de marcadores y calcular independencia/relaciones solo si están definidas | P15 | REQUERIDO |

## 3. Reglas por parejas/tríos/cu.../septetos

Un `PatternGroup` contiene `indices=[i1,...,ik]` (todos únicos, 1..14), `allowed_patterns` (tuplas de tamaño k), `minimum_occurrences`, `maximum_occurrences`, `overlap_policy`. Las posiciones pueden ser no consecutivas; si se desean ventanas deslizantes se genera un conjunto determinista de `indices`.

- Caso a: parejas `(1,2)` y `(2,3)` con signos `1X`, ambas cuentan si coinciden; son **solapadas**.
- Caso b: parejas `(1,2)` y `(3,4)` son disjuntas.
- Debe registrarse la política, porque «parejas no solapadas» puede referirse a distintos cómputos.
- En el análisis experto pueden coexistir varias condiciones de grupos, combinadas mediante AND/OR declarados.

## 4. Columnas base: tres significados diferentes

1. `ReferenceColumn`: signos únicos en 14 partidos, comparación directa con `hits14`.
2. `ReferenceMask`: varios signos permitidos por partido, «acierto» en posición si la columna pertenece a máscara.
3. `ReferenceGroup`: lista de referencias, se aplican operadores `ANY`, `ALL`, `AT_LEAST_N`, `SUM_OF_HITS`.

No convertir automáticamente referencias múltiples en una sola columna sin advertir que cambia la semántica.

## 5. Ejemplos exactos de tests

- FIL-01: `111XXXX2222111` (14 posiciones comprobadas por constructor de fixture): contar signos sin usar `str.count` como oráculo único.
- FIL-02: catorce `1` => variantes=0; catorce `X` => variantes=14.
- FIL-04: `1111XXXXXXXXXX` => racha máxima de `X`=10 y de `1`=4.
- FIL-05: `1111XXXXXXXXXX` con predicado «variante» => 1 transición.
- FIL-13: distancia Hamming=0 con referencia idéntica, 14 si todos difieren.
- FIL-23: pesos todos 1 => valoración suma=14, independiente de la columna.
- FIL-24: pesos todos 1 => producto=1, no 14.
- FIL-28: A falsa => filtro IF THEN pasa; A verdadera, B falsa => falla.
- FIL-30: con `K=1`, dos filtros en reserva fallidos => falla; uno => pasa.

## 6. Orden de implementación

- **Básicos:** FIL-01,02,03,04,13,18,19,31,32.
- **Intermedios:** FIL-05..12,14..16,20,23,24,25,28.
- **Expertos:** FIL-17,21,22,26,27,29,30.

Los filtros expertos con semántica `POR DEFINIR` no se deben presentar como equivalentes al original aunque compartan el nombre.

## 7. Prevención de errores históricos

Antes de desarrollar cada filtro, definir formalmente: alcance 14/15; fichas de grupo; límites mínimo/máximo; tratamiento de nulos; si los patrones se solapan; cálculo exacto de descartes; serialización y lectura de versiones anteriores. Probar entradas vacías, números grandes, filtros inactivos, reservas, combinación ganadora no presente y cancelación.
