# 02 · Arquitectura técnica y dependencias

## 1. Stack inicial recomendado

- **Python 3.11+**, aplicación de escritorio **PySide6/Qt**; SQLite local; `SQLAlchemy`/migraciones `Alembic` cuando proceda; `pydantic` o dataclasses para DTO y validación; `platformdirs` para directorios de usuario.
- Paquetes matemáticos `numpy`, `numba` **solo donde el perfilado lo justifique**. Considerar Rust/PyO3 u OR-Tools en reducciones complejas tras pruebas y con instalación opcional; no exigirlos para el MVP.
- `pytest`, `hypothesis`, `ruff`, un comprobador de tipos (`mypy` o `pyright`), cobertura; CI para Linux/Windows.
- Gráficas Qt/Matplotlib/PyQtGraph según rendimiento, sin integrar web/servidor sin necesidad.
- Distribución para Linux y Windows mediante empaquetadores testados por plataforma. Empaquetado y firma son fases específicas.

## 2. Capas

```
src/quiniela_ai_studio/
  domain/
    rules/            # reglas de juego versionadas, invariantes
    models/           # jornada, sistema, columna, probabilidades
    combinatorics/    # combinaciones, recuentos, distancias
    filters/          # evaluadores puros y registro
    reducers/         # optimización, garantías, verificadores
    scoring/          # probabilidades, rentabilidad, premios
  application/
    use_cases/        # crear, generar, filtrar, reducir, escrutar
    jobs/             # trabajos cancelables, checkpoint, progreso
    ports/            # interfaces de repositorio/proveedor/exportador
    dto/              # contratos entre capas
  infrastructure/
    db/               # SQLite, migraciones
    providers/        # archivos, SELAE/externos autorizados
    serializers/      # JSON nativo, TXT, XML, conectores externos
    files/            # gestión segura de ficheros
    observability/    # logs, auditoría
  ui/
    views/            # 7 secciones de escritorio
    widgets/          # casillas, gráficos, asistentes, progreso
    models/           # modelos de presentación Qt
    workers/          # adaptar trabajos sin bloquear el hilo UI
  resources/
    fixtures/         # datos de demostración no oficiales
```

**Regla de dependencias:** `ui -> application -> domain`; `infrastructure -> application/domain` a través de interfaces. `domain` NO importa `PySide6`, SQLite, HTTP, ML o archivos de interfaz.

## 3. Entidades principales

| Entidad | Campos relevantes | Relación |
|---|---|---|
| `GameRuleset` | id, vigencia, price_cents, modalidades/categorías, fuente, estado_verificación | n:1 a jornada |
| `Season` | id, etiqueta, fechas | 1:n jornadas |
| `Draw` (Jornada) | season_id, ordinal, source_id, status, ruleset_id, hora_límite | 15 partidos |
| `Match` | draw_id, índice 1..15, equipos, fecha/hora, resultado, estado | jornada |
| `MatchProbabilitySnapshot` | p1,pX,p2, fuente, fecha_corte, versión | partidos 1..14 |
| `PublicSelectionSnapshot` | q1,qX,q2, fuente, fecha_corte, versión | partidos 1..14 |
| `Full15Distribution` | matriz 4×4, fuente, timestamp | jornada |
| `Selection` | 14 máscaras binarias 3 bits, dos máscaras 4 bits para P15 | sistema |
| `Column` | 14 signos simples + pareja de marcadores P15 | una apuesta |
| `CombinationSet` | id, draw_id, origen, fuente, hash, modalidad, versión | varias columnas o generador |
| `FilterDefinition` | filter_id, params_schema_version, enabled, order, reserve_group | plan de filtrado |
| `FilterRun` | input_hash, filter_hash, passed, removed, stats | auditoría |
| `ReductionRun` | candidates, budget, seed, goal, result, verification | auditoría |
| `GuaranteeReport` | dominio, método exhaustivo/estimado, cobertura/umbral | reducción |
| `PredictionModelVersion` | data_cutoff, features, métricas, calibración, hash | predicciones |
| `PrizeTable` | jornada, categoría, premio_cents, ganadores, provisional/final | escrutinio |
| `PoolEstimate` | reglas, recaudación, hipótesis, incertidumbre | estimación |
| `AuditEvent` | operación, hora, usuario_local, parámetros, datos, resultado | flujo completo |

El dominio de `Column` es inmutable. `CombinationSet` puede representarse por almacenamiento físico **o** descripción compacta + generador reproducible. No asumas que todas las columnas caben en RAM.

## 4. Puertos obligatorios (interfaces)

- `DrawProvider`: `get_draw`, `get_results`, `get_prizes`, `get_source_metadata`.
- `ProbabilityProvider`: `get_snapshot(draw_id, cutoff)` con información de procedencia.
- `ProjectRepository`: CRUD, migraciones, transacciones y restauración.
- `CombinationReader/Writer`: streams tipados y esquemas versionados.
- `Filter`: `validate(params, context)`, `evaluate_batch(columns, context)->mask`, `explain(column, context)`.
- `Reducer`: `optimize(candidate_source, objective, seed, cancellation, progress)->result`.
- `CoverageVerifier`: `verify(candidate_set, domain, k, method)->report`.
- `PrizeEstimator`: `estimate(snapshot, assumptions)->distribution`.
- `ModelPredictor`: `predict(draw, cutoff)->PredictionBundle`.
- `AuditSink`: `record(event)` sin secretos ni resultados internos sensibles.

**Errores explícitos:** `InvalidGameRule`, `InvalidSelection`, `MissingData`, `StaleData`, `InsufficientPermissions`, `UnsupportedFormat`, `UnverifiedProvider`, `CancelledJob`, `ResourceLimitReached`.

## 5. Flujo de datos

1. Cargar jornada y reglas verificadas o demo.
2. Cargar pronósticos manuales o distribución predictiva con procedencia.
3. Generar `CombinationSet` conceptual de columnas candidatas.
4. Filtrar en pipeline sobre **lotes**, registrando supervivientes y eliminaciones.
5. Reducir u ordenar con objetivo medible, producir conjunto materializado (normalmente pequeño).
6. Verificar garantías de manera independiente del algoritmo reductor.
7. Exportar / imprimir / almacenar sin realizar ninguna apuesta por defecto.
8. Escrutar cuando hay resultados y registrar estado provisional/final.
9. Evaluar retrospectivamente sin fuga temporal de datos.

## 6. Memoria, CPU, UI y cancelación

- Operaciones sencillas síncronas; operaciones grandes en workers con mensajes de progreso, estado de cancelación y resultados parciales seguros.
- Generador streaming `Iterator[Column]`; chunk size configurable, iteradores deterministas para reanudar cuando sea posible.
- Nunca bloquear hilo de interfaz; errores de workers llegan a vista y registro.
- Deduplicación con representaciones compactas, sorted files, bases de datos/particiones o hash según escala; monitorizar tiempo y RAM.
- Estimar de antemano el tamaño y advertir antes de operaciones masivas.
- Especificar y fijar una política de `max_materialized_rows`; las operaciones combinatorias grandes trabajan como pipelines.

## 7. Rutas y portabilidad

- Configuración, logs y SQLite en directorios del usuario resueltos con `platformdirs`; carpetas de exportación elegidas por diálogo.
- Scripts para crear `.venv` y ejecutar sin depender de `/home/toni`, `/home/ajordan` u otra ruta fija.
- Primer inicio: comprobar versión de base, datos demo, permisos, directorios y opción de copia de seguridad.
- Exportación portable de proyecto y configuración *sin secretos*; migraciones versionadas y reversibles donde sea viable.

## 8. Registro y observabilidad

Dos niveles: (a) **historial humano** («se filtraron 18.400 de 25.000 columnas por estas reglas») y (b) log técnico con identificador de proceso y errores. Incluir ID de algoritmo, semilla, versión de código, hash de conjunto y advertencias. No guardar tokens, credenciales ni datos privados de peñas en logs de diagnóstico sin consentimiento.

## 9. Contrato de compatibilidad

Versionar esquemas de persistencia, formatos de archivo y reglas de juego por separado. Las migraciones se prueban contra proyectos anteriores. Nunca cambiar silenciosamente la definición de un filtro existente: crear una revisión semántica y migración explícita.
