# 09 · Plan de verificación, regresión y pruebas

## Generadores Normal v1.0.8 (RF-NOR-001..003)

La regresión ejecutable está en `tests/studio/test_normal_generation.py`,
`test_normal_generation_files.py` y `test_normal_generator_ui.py`: top-K contra
enumeración exhaustiva, desempate explícito 1<X<2, 7T/7D = 279.936, 6T/6D
con dos fijos, rango C.P. en logaritmos, 20.000 posiciones terminadas de las
100.000 primeras, concatenación/unión/intersección, fuentes distintas, salida
cancelable, importación y auditoría. Qt verifica matriz de 14 filas, conteos,
normalización, persistencia por jornada, fuentes/edición manual y terminaciones
gráficas. Revisión visual realizada a 1600×950; la sección permite scroll
horizontal en ventanas estrechas.

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

### RF-FIL-018/019 · Cuenta, rachas y datos históricos

### RF-UX-019 / RF-FIL-025 · Panel Cuenta v1.0.24

- Las frecuencias de 1/X/2 suman exactamente 14 por cada jornada incluida.
- Los perfiles conjuntos cuentan las tuplas (V, X, 2) reales y el filtro admite únicamente perfiles elegidos.
- La distancia entre equis funciona con la pestaña Cuenta activa; apagada, no interviene.
- La pantalla conserva temporadas compactas junto a Distribución Signos y usa cuadrados accesibles sin tics.

### RF-ESC-012 · Premios definitivos en Aciertos v1.0.27

- Usar un PRE sintético ligado a la jornada: dos copias de 14 + Pleno y tres
  apuestas de 13 deben producir tres subtotales y un total exacto.
- Comprobar que la vista se actualiza al abrir Aciertos sin marcador en directo
  y que la actualización parcial posterior no sustituye el PRE definitivo.
- Verificar premio cero, resultado parcial, PRE de equipos distintos y cambio
  de jornada sin importe anterior.

### RF-UX-021 · SSeguidos compacto v1.0.26

- Validar el fondo plano, el tamaño del lienzo por modo y la selección de
  temporadas en dos columnas.
- Ejecutar `test_sseguidos_three_modes_compact_panels_filter_and_share_state`
  y `test_sseguidos_automatic_keeps_joint_profiles_and_is_not_a_duplicate_filter`
  para comprobar que los cambios visuales no alteran el filtrado.

### RF-UX-020 · Composición clásica Cuenta v1.0.25

- Comparar Cuenta > Manual con la imagen de referencia descargada; verificar el orden matriz/Figuras/distribución, el fondo blanco de Figuras y la alineación de temporada, FILTROS y tabla de diez sumas.
- Confirmar filas 0–15, fila 15 inhabilitada, las cuatro acciones inferiores, Aplicar general y aplicación independiente de Figuras.
- Cambiar una temporada desde Manual y desde Automática; en ambos sentidos el selector se sincroniza y las estadísticas se recalculan con `results14`.
- Confirmar que el filtro existente de distancia X conserva su comportamiento. Las celdas de sumas/reserva/media permanecen vacías e inhabilitadas mientras la semántica original no esté definida.
- Revisar captura lado a lado y superposición al 50 % en `docs/validacion_visual/cuenta_v1_0_25/`.


- Para cada columna, verificar V=X+2 en los 14 partidos y excluir P15.
- Verificar longitudes máximas de 1/X/2/V; `XX22` forma una racha V de 4.
- Con rachas máximas exactas, `1111` cuenta como una figura de longitud 4,
  no como tres pares solapados; comprobar frecuencias 0..14.
- Azar con mismo desarrollo y semilla produce exactamente las mismas casillas,
  reglas y cantidad admitida; riesgo más alto no inventa valores no observados.
- Automática conserva perfiles conjuntos, empates deterministas y temporadas;
  rechaza fixtures sintéticos y datos mal formados sin modificar el historial.
- Desactivar Cuenta/Racha mantiene la configuración, ignora la regla en el
  cálculo y permite reactivarla. El Pleno no altera los conteos.

### RF-UX-015 / RF-FIL-021 · SSeguidos v1.0.19

- Manual, Azar y Automática comparten límites, frecuencias y figuras; Cuenta
  conserva su matriz y sus tres métodos.
- Los campos vacíos de mínimo/máximo se guardan como vacíos; el valor `0` se
  conserva como límite explícito. Restaurar una configuración mantiene ambos.
- Para cada signo y longitud, el DP de frecuencias exactas y figuras coincide
  con enumeración exhaustiva en bases pequeñas; `1111` cuenta como una racha de
  longitud 4, no como tres pares.
- Automática usa un filtro conjunto y rechaza perfiles que no pertenecen a la
  muestra histórica elegida. Azar con la misma semilla repite la propuesta.
- Desactivar SSeguidos conserva la regla sin aplicarla; activarla la incorpora.
  Aplicar guarda cambios aunque el número de apuestas no cambie.
- Paneles `1/X/2/V`, celdas blanco/verde, temporadas compactas y botones
  accesibles son controles Qt reales; Reducciones no muestra importación.

### RF-UX-016 / RF-FIL-022 · FSSeguidos v1.0.20

- Para 7 variantes, `3-2-1-1` admite la columna con rachas 3, 2, 1 y 1, y
  rechaza otra partición del mismo total como `4-3`.
- FSSeguidos está desactivada por defecto y no filtra hasta activar la pestaña
  exterior y el control del signo. Desactivarla conserva total y selección.
- El total y las selecciones múltiples se recuperan tras guardar; cambiar el
  total conserva las figuras anteriores y solo aplica el total visible.
- Azar repite perfiles con la misma semilla. Automática usa resultados finales
  de temporadas seleccionadas y no recomienda figuras imposibles en la base.

### RF-UX-017 / RF-FIL-023 · Interrupciones v1.0.21

- `11X21221XX121X` produce 10 cambios, racha máxima 4 y figura `4-4-2`;
  `12X22X11221111` produce 7 cambios y figura `3-2-1-1`.
- El DP de perfiles alcanzables coincide con enumeración exhaustiva sobre una
  base pequeña y restringida.
- La matriz `(total, racha)` y Distancias `(total, figura)` filtran de forma
  independiente; habilitar ambos combina las reglas por intersección AND.
- Sin activar la pestaña exterior, ninguna regla se aplica. Desactivarla
  conserva estado y no filtra; guardar/restaurar conserva cuadrados y métodos.
- Azar repite el resultado con la misma semilla. Automática usa solo signos
  finales reales por temporada seleccionada.

### RF-UX-018 / RF-FIL-024 · réplica visual y Distancias v1.0.22

- Distancia máxima `1/X/2/V`: casos con cero, una y varias apariciones;
  programación dinámica frente a enumeración exhaustiva en una base pequeña.
- Selecciones de cuatro bloques independientes, Aplicar propio, pestaña exterior
  desactivada y persistencia tras reabrir; fila 14 visible pero inhabilitada.
- Capturas de cinco vistas originales, imágenes finales reescaladas sin deformar,
  superposición y mapa de diferencias en `validacion_visual/reducciones_v1_0_22`.
- Cuenta Automática conserva la matriz visible junto a temporadas y riesgo;
  Grupo no pierde la edición de sus condiciones.

### RF-ARC-009 · Mis Sistemas v1.0.23

- Abrir desde la tabla una reducción Hermes guardada con el verificador dentro
  de `reduction_verification.coverage`; el resumen debe mostrar estado y mínimo.
- Mantener compatibilidad con el informe plano de otras reducciones y abrir
  copias incompletas indicando cobertura no verificada, sin alterar apuestas.

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
# RF-ESC-013 · Escrutinio publicado con PRE provisional

`tests/studio/test_published_scrutiny.py` reproduce los resultados y premios
publicados de la J14 2026-27 y rechaza fecha/jornada, equipo, marcador o
importe contradictorio. La prueba Qt
`test_published_page_cache_displays_real_j14_prize_when_pre_is_provisional`
comprueba el total de 2,22 € de una apuesta de 11 aciertos guardada.

# RF-ESC-014 y RF-UX-022 · Tarjetas de Escrutinio

Las pruebas Qt comprueban el borrado inmediato del premio al cambiar de
sistema desde Mis Sistemas, el desglose de seis categorías y total propio,
y el nombre Escrutinio manteniendo el índice 4 de navegación.
