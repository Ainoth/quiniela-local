# 09 · Plan de verificación, regresión y pruebas

## 1. Pirámide y herramientas

- Unitarias para reglas, importes, conteos, filtros y distribuciones de probabilidad.
- Basadas en propiedades (`hypothesis`) para invariantes algebraicos con estrategias pequeñas.
- Integración para SQLite, export/import, proveedores simulados, jobs y checkpoints.
- UI smoke tests (Qt con runner headless si se puede) en Linux y Windows; manuales para flujos gráficos.
- Rendimiento: benchmark repetible en hardware descrito. Reglas de aceptación con tiempo/memoria medidos; no prometer tiempos absolutos universales.
- Seguridad: ficheros maliciosos, JSON gigante, XML inseguro, errores de red, secretos/logs, importaciones corruptas.

## 2. Casos de aceptación por ID

| Test | Entrada | Resultado esperado |
|---|---|---|
| T-DOM-001 | 14 fijos, un P15 | 1 columna |
| T-DOM-002 | 1 doble, 13 fijos, un P15 | 2 columnas |
| T-DOM-003 | 2 triples, 1 doble, 11 fijos, un P15 | 18 columnas |
| T-DOM-004 | 14 triples, un P15 | 4.782.969 columnas sin generar todas en memoria |
| T-DOM-005 | 14 triples, 16 marcadores P15 | 76.527.504 columnas potenciales |
| T-DOM-006 | Selección vacía, signo ilegal o P15 incompleto | error claro sin datos guardados a medias |
| T-DOM-007 | Doble como `1X` y `X1` | misma selección canónica, sin duplicar |
| T-DOM-008 | Mapeo P15 `0,1,2,M` | 16 marcadores individuales posibles |
| T-ESC-001 | 14 signos acertados + P15 correcto | `hits14=14`, `full15_hit=true` |
| T-ESC-002 | 13 signos acertados + P15 correcto | `hits14=13`, `full15_hit=false` |
| T-ESC-003 | 14 signos acertados + P15 incorrecto | 14 sí, Pleno no |
| T-ESC-004 | 5 partidos sin finalizar | aciertos posibles [h,h+5] |
| T-CST-001 | N=18, precio demo 75 céntimos | coste=1.350 céntimos |
| T-CST-002 | precio 0 o negativo sin modo explícito | error de configuración o política controlada |
| T-CST-003 | precio/cantidad grande | sin overflow, sin float |
| T-PRO-001 | p1+pX+p2 !=1 | valida, corrige solo mediante política explícita |
| T-PRO-002 | probabilidad cero | ranking sin `log(0)` incontrolado |
| T-PRO-003 | P15 4x4 con suma 1 | acepta y etiqueta modelo |
| T-FIL-001 | filtros desactivados | no alteran columnas |
| T-FIL-002 | dos filtros duros intercambiados | mismo conjunto final |
| T-FIL-003 | filtro imposible | detecta condición inviable |
| T-FIL-004 | 25 columnas, 10 descartadas por primer fallo | conservadas+descartadas=25 |
| T-FIL-005 | 2 reservas fallan con tolerancia 1 | columna rechazada |
| T-GAR-001 | `S=Ω` para n=2, k=2 | cobertura=100 % garantizada |
| T-GAR-002 | una columna para n=2, Ω=9, k=2 | cobertura=1/9, no garantizada |
| T-GAR-003 | aumenta S sin eliminar anteriores | cobertura no decrece |
| T-GAR-004 | aumenta k | cobertura no crece |
| T-RED-001 | misma entrada + semilla | mismo resultado y hash |
| T-RED-002 | presupuesto K | resultado <=K columnas únicas |
| T-RED-003 | cancelación a mitad | solución parcial marcada, sin corrupción |
| T-FIL-006 | condición IF THEN A falsa | pasa independientemente de B |
| T-ARC-001 | serializar y deserializar JSON | equivalencia de picks14 y P15 |
| T-ARC-002 | fichero corrupto/desconocido | error explícito sin pérdida del proyecto |
| T-ARC-003 | export TXT con 2 P15 | dos líneas correctas, no una truncada |
| T-ARC-004 | archivo de tamaño excesivo | aviso o procesamiento streaming |
| T-PER-001 | 14 triples | aplicación no materializa 4,8 M filas en memoria |
| T-UX-001 | iniciar UI sin red | modo demo operativo, etiqueta visible |
| T-UX-002 | abrir filtro sin datos necesarios | botón de ejecución desactivado y causa explicada |
| T-AUD-001 | generar + filtrar + reducir | ID, semilla, versiones y conteos trazables |
| T-DAT-001 | reiniciar app tras guardar | proyecto se recupera sin pérdida |
| T-DAT-002 | migración de schema fallida | conserva respaldo/restaura |
| T-AI-001 | backtest | features posteriores a cutoff nunca utilizadas |
| T-AI-002 | modelo nulo/fallido | no inventa predicciones; fallback visible |
| T-AI-003 | evaluación | compara log loss/Brier y calibración con baseline |
| T-SEC-001 | tokens en logs/JSON exportado | ausentes |
| T-SEC-002 | formato oficial no soportado | no exporta falso archivo compatible |

## 3. Pruebas matemáticas de propiedad

- Conteo exacto vs enumeración para 1..5 posiciones generalizadas.
- Cada columna generada satisface una única opción permitida por posición y su P15 pertenece a las parejas elegidas.
- Generadores únicos no emiten duplicados; si se piden más columnas que combinaciones posibles, fallan con causa explícita.
- `d(a,b)=d(b,a)`, `0<=d<=14`, `d(a,a)=0`, desigualdad triangular para distancia de Hamming.
- `hits14(a,b)=14-d14(a,b)` en signos únicos.
- Filtrado sobre lotes vs filtrado escalar produce mismo conjunto; independencia del chunk size.
- Con filtros duros puros, aplicar en cualquier orden conserva resultado, no necesariamente los descartes asignados por filtro.
- Añadir columnas a S no puede reducir la cobertura; aumentar k no puede aumentarla.
- Export/import conserva IDs de jornada, reglas y parejas P15; las conversiones con pérdida son detectadas.

## 4. Pruebas de rendimiento y escala

Benchmark con n candidatos `[10^3,10^4,10^5,10^6]`, filtros simples y combinaciones múltiples; registrar tiempo, RAM pico, CPU, versión de Python, librerías, OS y CPU. `14 triples` debe permitir consulta rápida del contador y preview limitada sin volcado completo. Cancelación del pipeline no deja escritura parcial no declarada; exportaciones grandes deben poder emitirse en streaming.

Fijar umbrales de rendimiento numéricos **solo después de medir hardware objetivo y baseline**, documentando degradación aceptable. Si un cálculo exacto sobre todo Ω supera recursos, avisar y ofrecer cálculo limitado/estimado con etiqueta apropiada.

## 5. Pruebas UX de usuario real

- En menos de unos pasos razonables (medir mediante pruebas de usabilidad, no prometer tiempo), un principiante localiza una jornada y marca la quiniela.
- Presupuesto y coste visibles antes de exportar.
- Estado «demo», «estimado», «oficial» y «pendiente» inequívocos.
- Porcentaje de filtros eliminados y explicación de causa accesibles sin abrir logs técnicos.
- Mensajes sin jerga sin definir; ayuda contextual para CB, reservas, garantías y EV.
- Redimensionado, accesibilidad de teclado y alto contraste.

## 6. Criterios CI

CI mínima: `ruff check .`, `pytest -q`, test de import de paquete, prueba de esquema, validación de enlaces internos docs y revisión de `pyproject.toml`. Añadir herramientas de tipos y GUI cuando el proyecto las configure. **No inventar porcentaje de cobertura**: publicar cobertura real y objetivos progresivos; núcleo matemático con cobertura particularmente alta y pruebas de propiedad.
