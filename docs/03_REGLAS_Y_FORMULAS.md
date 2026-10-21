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

**Premios definitivos (RF-ESC-012).** El desglose usa los importes unitarios
publicados para la jornada en el PRE local y las cantidades de apuestas
guardadas. `subtotal_k = apuestas_k × premio_unitario_k`, para categorías
10–14; el Pleno al 15 se añade como categoría 15 solo si la apuesta acierta
también los 14 signos. El total es la suma de subtotales en céntimos enteros.
No se calcula dinero con resultados parciales ni se infiere que las apuestas
guardadas se hayan validado o cobrado.

Para una columna `c` y resultado oficial `r`: `hits14(c,r)=Σ_{i=1}^{14} 1[c_i=r_i]`.

`full15_hit(c,r)= (hits14(c,r)==14) AND (c.P15 == r.P15)`.

Distancia de Hamming 14-signos: `d14(a,b)=Σ_{i=1}^{14} 1[a_i != b_i] = 14-hits14(a,b)`.

Opcional: distancia total = `d14 + 1[(gH,gA) ≠ (rH,rA)]`, **solo si está explícitamente definido**; no mezclar 14 signos con P15 en el mismo indicador sin etiquetarlo.

En escrutinio parcial, definir `resolved` (partidos finalizados), `hits_fixed` entre resueltos, `unknown=14-|resolved|`; intervalo posible `hits_fixed..hits_fixed+unknown` sobre cada apuesta. Un acierto en el Pleno no se declara definitivo sin el 14 completo.

## 3.1 Cuenta y rachas (RF-FIL-018/019)

La vista de Cuenta informa frecuencias marginales de signos 1/X/2 y perfiles conjuntos (V, X, 2) por temporadas seleccionadas. Estos recuentos describen la muestra observada, no probabilidades predictivas. La selección de perfiles se aplica como igualdad de tupla y se combina con las selecciones individuales activadas.

Los filtros de Cuenta operan únicamente sobre los 14 signos: `V = X + 2`.
Racha `1`, `X` o `2` es la secuencia contigua máxima del signo; Racha `V`
considera X y 2 una misma clase, incluso en secuencias mixtas como `XX22`.
Una figura de longitud `n` cuenta rachas máximas de longitud exactamente `n`;
no cuenta ventanas solapadas dentro de una racha mayor (`1111` es una figura
de longitud 4, no tres figuras de longitud 2). Es una semántica propia y
explícita mientras no se confirme otra convención original.

En **SSeguidos**, el mínimo y máximo manuales son límites opcionales para la
longitud de la racha máxima de cada clase. Si se introduce `1..3`, la racha
máxima de unos debe medir al menos 1 y no más de 3. Un campo vacío omite ese
límite; `Mín.=0` tampoco obliga a que aparezca el signo y `Máx.=0` lo excluye.
La matriz de **Veces** permite conjuntos exactos no contiguos: por ejemplo,
permitir 0, 1, 2 o 3 rachas máximas de longitud 2. No cuenta ventanas
solapadas: `1111` es una racha de longitud 4, no tres pares. Los valores
alcanzables y las figuras se calculan desde la base actual; cambiar la base no
borra en silencio selecciones guardadas.

Una figura es la partición descendente de todas las rachas máximas, como
`3-2-1`; su suma es el número total de signos de esa clase. Para `V`, X y 2 se
combinan en una secuencia. El Pleno al 15 queda excluido. Automática trabaja con
registros finales del histórico integrado que contienen temporada, jornada y
14 signos, y conserva los perfiles conjuntos seleccionados; sus niveles
Mínimo/Medio/Máximo describen cobertura de muestra, no confianza predictiva ni
garantizan resultados futuros. Azar toma 512 muestras uniformes de las
completaciones de la base, con `random.Random(semilla)`; su política de riesgo
es original y provisional, no una convención de WIN1X2.

**FSSeguidos** es una condición aparte de SSeguidos: para un signo y un total
seleccionado conserva únicamente una o varias particiones exactas de las
rachas máximas, por ejemplo `3-2-1-1` para siete variantes. Cada partición
suma el total elegido y sus partes están en orden descendente. La base limita
las figuras disponibles; Automática solo recomienda figuras que también son
alcanzables. Cada signo puede activarse por separado y el interruptor exterior
de FSSeguidos gobierna todo el conjunto. En Manual se conservan selecciones al
cambiar el total, pero solo se aplica el total visible. La regla usa
`tab_index=17`, sin alterar los índices de los filtros anteriores. El Pleno
queda excluido.

## 3.2 Interrupciones y Distancias (RF-FIL-023)

Para una columna `c=(c_1,...,c_14)`, la transición `t_i` vale 1 si
`c_i != c_(i+1)` y 0 si son iguales, para `i=1..13`. El total de
interrupciones es `I=Σt_i`. Se agrupan los bloques máximos consecutivos de
unos del vector `t`, se ordenan de mayor a menor y se muestran como figura.
Así, `11X21221XX121X` produce `I=10`, racha máxima 4 y figura `4-4-2`.
El Pleno al 15 no interviene.

La interpretación actual de la matriz Manual/Automática es seleccionar el par
`(I, R)`, donde `R` es la racha máxima de transiciones consecutivas. La pantalla
Distancias selecciona pares `(I, figura)` exactos. Son filtros separados y,
cuando ambos están activados, se combinan mediante AND. Esta correspondencia de
la matriz es **original/provisional**: el material disponible no confirma la
semántica histórica precisa de cada columna, en particular la columna 0.

La vista derecha de figuras lleva el rótulo histórico «Distancias», pero su
regla es una partición de interrupciones. La nueva **subpestaña Distancias**
(RF-FIL-024) es otro filtro: para `s∈{1,X,2,V}`, se toman las posiciones
ordenadas `p_1<...<p_n` donde aparece el signo, con `V={X,2}`, y se mide
`D_s=max(p_(i+1)-p_i)`; si `n<2`, `D_s=0`. Cada bloque activo acepta solo los
valores seleccionados, de 0 a 13. El 14 se muestra inhabilitado como referencia
visual clásica. La alcanzabilidad se calcula exactamente desde la base mediante
programación dinámica. Es una convención **original/provisional**, no una
afirmación sobre el código interno de WIN1X2. La pestaña exterior Interrupciones
gobierna tanto los cambios como estas distancias y está apagada por defecto.

Azar muestrea perfiles alcanzables de forma reproducible por semilla; Automática
ordena perfiles observados compatibles con la base por frecuencia en las
temporadas seleccionadas. Los niveles de riesgo son políticas originales de
cobertura de muestra, no probabilidades de acierto. Ninguno inventa datos.

## 4. Probabilidad de una columna

`p_i(1)+p_i(X)+p_i(2)=1` para cada partido. Pleno: `Σ_{a,b ∈ G} p15(a,b)=1`.

**Modelo básico aproximado, con independencia explícita:**

`P(c) ≈ (product_i p_i(c_i)) × p15(c.P15)`.

Este producto puede estar mal calibrado porque los marcadores, signos y acontecimientos están correlacionados. Almacenarlo como `probability_model='independence_v1'`, con fuente/fecha de cada vector y límites de precisión. Para ordenar columnas, usar log-probabilidad: `log P(c) = sum_i log p_i(c_i) + log p15(c.P15)`; manejar probabilidades cero como `-∞`.

En el generador Normal v1.0.8, **C.P.** ordena únicamente la columna 1/X/2 de
14 partidos: `log C.P.(c) = Σ(i=1..14) log p_i(c_i)`. No incluye Pleno al 15;
el modo actual de ranking puede filtrar ese C.P. por un intervalo inclusivo.
Los empates se resuelven lexicográficamente por signo `1 < X < 2`, de izquierda
a derecha. El ranking y sus umbrales trabajan en logaritmos, aunque la interfaz
muestre el intervalo como probabilidad entre 0 y 1.

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
