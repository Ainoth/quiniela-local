# 06 · IA predictiva, estimación de premios y análisis de rentabilidad

## 1. Distinciones obligatorias

1. **Probabilidad deportiva** `P(resultado)` estima sucesos deportivos.
2. **Porcentaje jugado por el público** `q(signo)` estima preferencias de apostantes.
3. **Probabilidad de obtener un premio** depende de las columnas adquiridas y los resultados.
4. **Importe del premio** depende de reglas, recaudación, otras apuestas ganadoras y datos oficiales.
5. **Valor esperado** combina probabilidades y cuantías, no garantiza ganancia.

Nunca sustituir una magnitud por otra por conveniencia. Si los datos no existen, bloquear la función o marcar «modelo de demostración».

## 2. Programa de datos

- Datos históricos versionados: jornadas, encuentros, competiciones, resultados, local/visitante, horarios, goles, probabilidades/odds con fecha de publicación.
- Antecedentes deportivos disponibles **antes** de cada pronóstico: forma reciente, descanso, situación del equipo, lesiones o alineaciones solo si el proveedor autorizado ofrece histórico fechable.
- Cuotas de casas de apuestas con timestamp y licencia/condiciones aplicables, si se incorporan.
- Porcentajes jugados SELAE con fecha de captura cuando exista fuente autorizada.
- Valores de premio/recaudación: mantener separados `estimado` y `oficial`.
- Cada registro debe contener `observed_at`, `event_time`, `as_of_cutoff` y `source`; rechazar leakage temporal.

## 3. Modelos candidatos

### Baselines obligatorios

- `frequency_baseline_v1`: frecuencias históricas condicionadas por simple separación local/visitante y período, con suavizado.
- `odds_normalized_v1`: probabilidades implícitas de cuotas disponibles y normalizadas.
- `poisson_goals_v1`: modelo de goles para derivar 1/X/2 y P15 con categorías 0/1/2/M, con calibración posterior.

### Alternativas de ML, solo tras baselines

- Regresión logística multinomial / gradient boosting 1X2 con variables conocidas antes de apostar.
- Modelo de goles (Poisson bivariada / otras distribuciones) para P15.
- Ensamblado calibrado y método fallback según calidad de datos.
- Modelos registrados con versión, conjunto de entrenamiento, fecha de corte, features, hiperparámetros, calibración, licencia de datos y hash de artefacto.

Los modelos de lenguaje pueden ayudar a explicar el proceso o la interfaz, pero **no se consideran por sí solos un predictor fiable**. No usar resultados actuales para pronósticos históricos.

## 4. Evaluación rigurosa

- Split temporal: entrenamiento < validación < prueba; ventana deslizante para temporadas consecutivas.
- Puntuación `log loss` (menor mejor), `Brier score` multicategoría (menor mejor), curvas de calibración y tasa de cobertura de predicciones.
- Comparación contra baselines; incertidumbre mediante bootstrap agrupado por jornada/temporada.
- Detectar cambios de distribución entre temporadas y porcentaje de datos faltantes.
- Elige modelo solo si mejora fuera de muestra y no provoca sobreajuste.
- Registrar qué sabía el modelo al cierre de pronósticos de cada jornada (`as_of_cutoff`).
- Para modelo de goles, validar distribución agregada de marcadores, no solo exactitud de favoritos.

## 5. Estimación de acertantes y premios

**Estimación aproximada** bajo hipótesis simplificadas:

`P_public_ticket(w) ≈ ∏_{i=1..14} q_i(w_i) × q15(w.P15)` para la columna exacta w, *siempre que existan probabilidades de selección válidas*.

`Expected_number_of_other_full_hits ≈ N_other_tickets × P_public_ticket(w)`.

Esto ignora correlaciones, estilos de selección de jugadores, boletos múltiples, duplicados y otros detalles. **No es el número esperado de acertantes de 13, 12, 11 o 10**; para esas categorías hay que sumar todas las columnas que cumplen el acierto correspondiente (o estimarlas por una simulación validada) y aplicar condiciones oficiales del P15.

El premio bruto por categoría es una función del fondo asignado a esa categoría y del número de apuestas ganadoras/otros criterios vigentes; ambos pueden ser inciertos hasta el escrutinio oficial. La simulación debe reportar bandas (bajo/medio/alto), método, datos de entrada y momento de estimación.

No fijar 16 %, 7,5 %, 55 % ni repartos históricos en el código sin reglas oficiales de la edición aplicable. Si se adopta un reparto verificado, debe vivir en `GameRuleset` con cita y vigencia, no en funciones.

## 6. Métrica propia de rentabilidad

**Propuesta original**, distinta de cualquier fórmula propietaria:

`EV_per_ticket = Σ_{w∈Ω} P_model(w) × PrizeEstimate(ticket, w) - ticket_cost`.

`EV_ratio = EV_per_ticket / ticket_cost` cuando el coste es positivo. Si los premios son aleatorios por concurrencia de ganadores, integrar también su distribución o usar escenario y rango.

Alternativa de ranking robusto: maximizar `EV_estimate - λ * downside_risk`, donde `λ` depende de preferencia de riesgo y se muestra al usuario. Una puntuación numérica interna no debe presentarse como tasa de retorno asegurada.

Para conjuntos de apuestas, no sumar probabilidades de premio sin tratar solapamientos; calcular payout agregado por escenario. Una columna muy improbable puede tener premio potencial alto pero peor EV que otra.

## 7. Comparador de sistemas y simulaciones

- Generar una misma lista de `w` simulados y aplicar a cada sistema; comparar diferencias emparejadas.
- Guardar escenario, semilla, probabilidades, estimador de premios y modelo.
- Reportar: inversión, media/mediana de premios, pérdidas y ganancias, probabilidad de recuperar coste, peor escenario observado y percentiles.
- Backtesting: solo datos conocidos antes de cada sorteo; sin parámetros recalibrados usando el resultado a evaluar.
- Cuando no hay premio económico histórico oficial: analizar cobertura/aciertos, no inventar rentabilidad monetaria.

## 8. UX de IA explicable

Cada recomendación debe responder:

- Qué información se utilizó (fuente, fecha).
- Qué probabilidad se estimó y con qué modelo.
- Qué alternativas se consideraron.
- Cómo influyó el presupuesto y el perfil conservador/equilibrado/arriesgado.
- Qué reglas descartaron otras columnas.
- Qué se sabe con certeza (coste, recuento) y qué es estimado (probabilidad, premio).

## 9. Seguridad y sesgos

Prohibido indicar o insinuar «quiniela ganadora», «beneficio garantizado» o «el algoritmo aprende a acertar siempre». Mostrar límites de presupuesto y no incentivar persecución de pérdidas. Si la fuente de datos cambia, recalcular calibración antes de declarar predicciones fiables.
