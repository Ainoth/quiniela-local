# Continuar en casa — desarrollo v1.0.0

Trabajo pausado el 13/10/2026 por petición del usuario. La numeración ya es
v1.0.0, pero este commit es un incremento de desarrollo, no la certificación
de que toda la especificación esté terminada.

## Estado guardado

Motor independiente de optimización por presupuesto, cobertura marginal,
intercambio local y búsqueda exhaustiva limitada. Verificador independiente
de garantías, métricas uniformes/ponderadas y comparación de estrategias.
Interfaz asíncrona con cancelación, revisión antes de aplicar y auditoría.
Pleno manual por defecto y agrupación de boletos por Pleno sin cambiarlo.
Exportación TXT/CSV propia con relectura; no se afirma importación automática
en TuLotero ni se realizan pagos. Android no se ha modificado.

Documentación: `docs/STUDIO_V1_0.md`; plan y diagnóstico anterior:
`docs/planes/V1_OPTIMIZACION.md`.

## Validación realizada antes de pausar

- Suite Studio: 201 pruebas superadas.
- Suite histórica con interfaz: 32 pruebas superadas.
- `./run_studio.sh --self-check` y `--smoke-test`: correctos.
- Ruff para errores E9/F e importaciones I: correcto.
- Instalación editable local actualizada a 1.0.0.

Referencia sintética reproducible con `scripts/benchmark_portfolio.py`:
72 columnas, presupuesto 5 €, seis apuestas de 0,75 € y remanente 0,50 €.
El modo automático obtuvo cobertura ponderada condicional de 13+ del 79,92 %
y de 12+ del 99,44 %, frente al 62,99 % y 89,45 % de la selección anterior
por probabilidad. La distancia media pasó de 1,67 a 3,13. A cambio, la masa
absoluta estimada de 14 bajó de 0,02441 % a 0,01172 %. Son datos de una base
sintética con independencia entre partidos, no una promesa de premio ni una
demostración de optimalidad global. Medición local con tracemalloc: 0,65 s
y unos 56 KB de pico atribuible al cálculo.

## Pendiente antes de declarar una entrega final

- Revisión completa de conformidad con la especificación y de casos límite
  de presupuesto, agrupación, cancelación y entradas numéricas extremas.
- Comprobación visual interactiva de todas las pantallas modificadas.
- Revisar igualdad de cantidades en comparaciones con restricciones de
  agrupación y el registro de ejecuciones canceladas o fallidas.
- El límite temporal acota la búsqueda; la verificación posterior puede
  prolongar el tiempo total. Revisar este comportamiento en universos grandes.
- Validar empaquetado y ejecución nativa en Windows; no probado aquí.
- El valor esperado permanece desactivado sin datos económicos suficientes.
  Las coberturas muestreadas no son garantías matemáticas.

## Recuperar y ejecutar

Desde el repositorio en casa:

```bash
git pull --ff-only
./run_studio.sh
```

Si ya existe un entorno virtual, actualizar su instalación editable con
`python -m pip install -e .` usando el Python de ese entorno. Consultar README
para preparar dependencias en un equipo nuevo.

Los TXT personales están excluidos de Git y permanecen en el equipo original.
Las pruebas opcionales que los utilizan se omiten si no están disponibles;
no se han inventado ni publicado sus contenidos.
