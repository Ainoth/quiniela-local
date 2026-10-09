# 05 · Reducción de apuestas y verificación de garantías

## 1. Terminología de dominio

- `B`: universo de resultados pronosticados por el sistema base (producto de máscaras, o universo expresamente seleccionado).
- `C`: conjunto de apuestas candidatas, normalmente las columnas del sistema filtrado.
- `S ⊆ C`: columnas elegidas para jugar; en modo **externas** se permite `S⊆E` para un universo candidato `E` mayor, solo por elección explícita.
- `w`: un resultado ganador concreto de los 14 partidos, perteneciente al universo de análisis `Ω`.
- `h(c,w)`: aciertos de los primeros 14 entre columna `c` y resultado `w`.
- `k`: umbral de aciertos (0..14).
- `K`: presupuesto máximo en columnas: `floor(budget_cents/price_cents)`, considerando complementos.

Es fundamental indicar al usuario **sobre qué universo se garantiza cobertura**: resultados contenidos en la base, resultados filtrados o todos los 3^14 resultados. No son equivalentes.

## 2. Funciones de cobertura

Para un conjunto de apuestas `S` y un resultado `w`:

`best_hits(S,w)=max_{s∈S} h(s,w)`.

`covered_k(S,w)= 1[best_hits(S,w)>=k]`.

Cobertura porcentual exacta sobre universo finito `Ω`:

`coverage_k(S,Ω)= Σ_{w∈Ω}covered_k(S,w) / |Ω|`, solo cuando `|Ω|>0`.

Garantía de al menos un premio de umbral k sobre universo Ω:

`guarantee_at_least_one_k = min_{w∈Ω} covered_k(S,w) = 1`.

Mínimo de apuestas con `>=k` aciertos sobre universo Ω:

`min_prizes_k(S,Ω)=min_{w∈Ω} #{s∈S:h(s,w)>=k}`.

`exactly_k` y `at_least_k` NO son lo mismo; reportar ambas con etiquetas propias si se implementan. No declarar una garantía absoluta basándose solo en simulación Monte Carlo.

## 3. Probabilidad ponderada de cobertura

Si el usuario proporciona modelo predictivo `P(w)` (conjunto de eventos mutuamente excluyentes y normalizados):

`weighted_coverage_k(S,Ω)=Σ_{w∈Ω}P(w)*covered_k(S,w) / Σ_{w∈Ω}P(w)`.

Esta métrica es **probabilística**, no garantía. Si los pesos no son válidos se suspende el cálculo. Las probabilidades fuera del universo Ω quedan explicitadas como masa excluida.

## 4. Pleno al 15 y garantías

Un conjunto que cubre resultados de los 14 partidos no garantiza acertar la pareja de goles del partido 15. Reportar dos análisis:

- `hits14` sobre Ω14.
- `full15` sobre Ω14×Ω15, con `full15_hit` verdadero solo al acertar 14 y la pareja P15.

Si el dominio es gigante, el verificador puede usar demostración algorítmica, partición exhaustiva con checkpoint o reportar **cota inferior observada** sin afirmar garantía matemática no probada.

## 5. Reductor original propuesto

### Objetivo A — Set cover discreto

Minimizar `|S|` sujeto a `best_hits(S,w)>=k` para cada `w∈Ω`, y a las restricciones de presupuesto y candidatas. Problema combinatorio NP-difícil en variantes relevantes. Para pequeño Ω, usar solver exacto opcional; para dominios grandes, heurísticas.

### Objetivo B — presupuesto fijo

Maximizar `coverage_k(S,Ω)` o `weighted_coverage_k` con `|S|<=K`, y opcionalmente métricas de diversidad/rentabilidad. **El resultado no tiene por qué ofrecer garantía completa.**

### Algoritmos originales

1. `greedy_coverage_v1`: seleccionar la candidata con máxima ganancia marginal de resultados aún no cubiertos; desempate determinista por índice/hash/semilla.
2. `local_search_v1`: swaps y sustituciones tras greedy, conservando la mejor solución, con límite de tiempo/iteraciones.
3. `random_restart_v1`: varias semillas, informe de dispersión de resultados; no usar aleatoriedad no reproducible.
4. `exact_small_v1`: solver exacto cuando el universo sea pequeño y coste asumible, para construir oráculos matemáticos.

Versionar la estrategia y no llamarla REDWIN/007R/TRADICIONAL. Es legítimo ofrecer nombres propios, pero sin suplantar marcas o equivalencias.

## 6. Internas, externas y ajuste exacto

- `internas`: las elegidas deben pertenecer a `B`/`C` según contrato declarado.
- `externas`: pueden pertenecer al universo elegible `E` fuera del sistema base, útil para cobertura pero contraintuitivo; explicar siempre.
- `exact_count`: una restricción de cardinalidad. Si `K` excede el número de candidatas únicas, no inventar columnas/duplicar silenciosamente: ofrecer explícitamente recalcular con universo mayor o reducir la petición.
- Cuando no se puede conseguir k-cobertura, informar porcentaje logrado, límites y razón de parada.

## 7. Verificador independiente y certificados

Cada reducción guarda:

- versión y parámetros; universo Ω y su cardinalidad; hash de candidatos y salida; semilla y algoritmo;
- comprobación separada de todas las columnas elegidas, sus duplicados y su pertenencia;
- `coverage_k` exacta o estimada **con método**; `min_prizes_k` si exacto;
- si es parcial/Monte Carlo, intervalo de confianza y ausencia de garantía absoluta.

La interfaz debe mostrar «Garantía comprobada sobre X resultados» o «Cobertura estimada con Y simulaciones», nunca una etiqueta ambigua de «100 %».

## 8. Referencias de pruebas

1. Si `S=Ω={1X2}^{n}` para n reducido, la cobertura exacta para k=n es 100 %.
2. Si S tiene una única columna y Ω contiene resultados diferentes, no hay garantía de k=n.
3. Para n=2 y universo de 9 posibles resultados, seleccionar todas las 9 columnas asegura exactamente 2 aciertos en todos los casos.
4. Las métricas `coverage_k` son monótonas no decrecientes cuando se añaden apuestas.
5. Para S fijo, `coverage_k` es no creciente al aumentar k.
6. Todas las columnas seleccionadas deben respetar el presupuesto en céntimos.
7. Repetir con misma semilla/configuración produce exactamente la misma salida e informe.
8. Cada informe presentado como exacto debe poder reproducirse con enumeración exhaustiva en pequeños dominios.

## 9. Dependencias

Se necesita el modelo formal de columna (v0.1), filtros (v0.2), un generador de escenarios y oráculo de garantías. La reducción no debe implementarse como una pantalla monolítica: motor, verificador y UI separados.
