# 03 · Dominio de La Quiniela y fórmulas matemáticas

> **Normativa**: consultar [SELAE](https://www.loteriasyapuestas.es/es/centro-de-ayuda/como-se-juega/como-jugar-a-la-quiniela), reglas vigentes y límites de apuestas por jornada. Los ejemplos de precio y reparto de premios de historiales antiguos NO son fuentes normativas. Versionar las reglas.

## 1. Signos y columna

- Partidos 1..14: alfabeto `A={1,X,2}`. Cada selección `S_i` es un subconjunto no vacío de `A`.
- Pleno al 15: dos pronósticos de goles, local y visitante, `G={0,1,2,M}`; `M` significa 3 o más. Cada selección del Pleno al 15 es una **pareja** `(g_local,g_visitante)`. Permitir conjunto de parejas y, cuando se edita con dos máscaras independientes, expandir producto cartesiano; también permitir subconjuntos de parejas que no sean cartesianos en el modelo experto.
- Una columna concreta `c=(c_1,...,c_14,g_local,g_visitante)` contiene exactamente un signo por cada partido y una pareja en el 15.
- La categoría superior del Pleno al 15 exige, además, acertar los primeros 14 partidos según las reglas vigentes.

## 2. Número de columnas

Para selecciones independientes: `N_14 = product_{i=1..14} |S_i|`.

Si `P15` es el conjunto explícito de marcadores permitidos: `N_total = N_14 * |P15|`.

Si P15 se expresa como máscaras independientes, `|P15| = |G_local| * |G_visitante|`.

Ejemplos de referencia:
- 14 fijos + 1 marcador del Pleno = 1 columna.
- 1 doble + resto fijos + 1 Pleno = 2 columnas.
- 2 triples + 1 doble + resto fijos = `3²×2 = 18` columnas por marcador Pleno.
- `3^14 = 4.782.969` columnas de 14 signos diferentes.
- `3^14 × 16 = 76.527.504` columnas posibles contando los 16 marcadores individuales del Pleno.

El precio de la apuesta se extrae de `GameRuleset` y se computa `cost_cents = N_purchased_lines × unit_price_cents + optional_complements_cents`. Proteger desbordamientos, límites de compra y duplicados. No confundir **columnas únicas de un sistema** con **líneas efectivamente adquiridas** si el usuario repite una columna.

## 3. Resultado ganador, distancia y aciertos

Para una columna `c` y resultado oficial `r`: `hits14(c,r)=Σ_{i=1}^{14} 1[c_i=r_i]`.

`full15_hit(c,r)= (hits14(c,r)==14) AND (c.P15 == r.P15)`.

Distancia de Hamming 14-signos: `d14(a,b)=Σ_{i=1}^{14} 1[a_i != b_i] = 14-hits14(a,b)`.

Opcional: distancia total = `d14 + 1[(gH,gA) ≠ (rH,rA)]`, **solo si está explícitamente definido**; no mezclar 14 signos con P15 en el mismo indicador sin etiquetarlo.

En escrutinio parcial, definir `resolved` (partidos finalizados), `hits_fixed` entre resueltos, `unknown=14-|resolved|`; intervalo posible `hits_fixed..hits_fixed+unknown` sobre cada apuesta. Un acierto en el Pleno no se declara definitivo sin el 14 completo.

## 4. Probabilidad de una columna

`p_i(1)+p_i(X)+p_i(2)=1` para cada partido. Pleno: `Σ_{a,b ∈ G} p15(a,b)=1`.

**Modelo básico aproximado, con independencia explícita:**

`P(c) ≈ (product_i p_i(c_i)) × p15(c.P15)`.

Este producto puede estar mal calibrado porque los marcadores, signos y acontecimientos están correlacionados. Almacenarlo como `probability_model='independence_v1'`, con fuente/fecha de cada vector y límites de precisión. Para ordenar columnas, usar log-probabilidad: `log P(c) = sum_i log p_i(c_i) + log p15(c.P15)`; manejar probabilidades cero como `-∞`.

**Probabilidad de al menos una columna exacta ganadora** en un conjunto de columnas **únicas y mutuamente excluyentes como resultados completos** bajo una distribución conjunta válida: suma de sus probabilidades. No sumar probabilidades de **categorías de premios** sin tratar solapamientos.

**Porcentaje público** `q_i(s)` es distinta magnitud; se usa para estimaciones de distribución de apuestas de terceros, no como probabilidad deportiva salvo que se justifique.

## 5. Distribuciones de un sistema

Sobre un multiconjunto de columnas `C` con `N>0`: `share_i(s) = #{c∈C:c_i=s}/N`. Si se desea contar columnas repetidas, declarar `multiset=True`; de lo contrario, las métricas sobre columnas únicas se calculan con `set(C)`.

Distancia de porcentajes contra objetivo `t_i(s)`:

`MAE = (1/42) Σ_{i=1}^{14} Σ_{s∈A} |share_i(s)-t_i(s)|`.

Algoritmo de estabilización propuesto: generar una propuesta inicial; intercambiar o sustituir signos entre columnas respetando fijos/bloqueos, mejorando una función objetivo que combine MAE, unicidad y restricciones hasta convergencia o límite de ciclos. Informar MAE antes/después, semilla y razón de parada.

## 6. Premios, coste, retorno

- `stake_cents`: coste exacto confirmado de todas las apuestas adquiridas.
- `gross_prizes_cents`: suma real de premios oficialmente publicados por categoría y líneas acertantes.
- `net_result_cents = gross_prizes_cents - stake_cents` (antes de impuestos/comisiones si no se modelan).
- `ROI = net_result / stake` si `stake>0`, con aviso de división no definida cuando `stake=0`.
- `expected_profit = sum_outcomes P(outcome)*payout(outcome) - stake` solo si existe modelo probabilístico y de pagos completos; mostrar incertidumbre y supuesto.

La distribución de premios y el porcentaje de la recaudación asignado por categoría deben extraerse de reglas oficiales **vigentes y versionadas**. La pantalla de estimaciones jamás debe mezclar cuantías calculadas con premios confirmados.

## 7. Márgenes y probabilidades de casas

Si una casa publica cuotas decimales `o1,oX,o2`, probabilidad implícita cruda `u_s=1/o_s`. Una normalización inicial es `p_s = u_s/(u1+uX+u2)`. Es un método simplificado de retirar el margen, no una verdad estadística. Registrar fecha/casa/mercado, términos de uso, grado de calibración, fuente y limitaciones.

## 8. Formatos y reglas que deben quedar configurables

Reglas de participación y categorías, precio de línea, límites por boleto, formatos de validación, recaudación/categorías, plazos, Elige8, modalidades reducidas y tratamientos del Pleno al 15. **Ningún valor de una versión anterior se fija como regla universal.**
