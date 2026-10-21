# Réplica visual de Reducciones — v1.0.22

## Referencias y alcance

Fuente principal: `PROMPT_CODEX_REPLICA_VISUAL_QUINIELA_v2.md` y las ocho
imágenes de `REFERENCIAS_Y_PROMPT_CODEX_QT.zip`. La guía
`ESPECIFICACION_QT_SELECCION_SIGNOS_SEGUIDOS_v1_0.md` precisa la semántica de
SSeguidos. El prompt v2 prevalece en geometría cuando ambas guías difieren.

| Pantalla | Vista actual | Estado y filtro | Diferencia principal |
|---|---|---|---|
| Cuenta | `MainWindow._install_count_streak_modes` | `count_values`, `allowed_count` | Matriz y selector de temporada desproporcionados; no hay referencia original inequívoca. |
| SSeguidos | `MainWindow._build_sseguidos_modes` | `run_*`, `allowed_run_count` y `allowed_run_figure` | Matriz rectangular y cuatro formularios grandes; faltan escalera, doble lista y piel clásica. |
| FSSeguidos | `MainWindow._build_fssiguedos_modes` | `fss_*`, `allowed_run_figure` | Un spinner único ocupa el lugar de la lista vertical de totales. |
| Interrupciones | `MainWindow._build_interruption_modes` | `interruption_*`, `allowed_interruption_profile` y `allowed_interruption_figure` | Matriz/listas grandes, temporadas en bloque separado; falta el subtab propio de Distancias. |
| Grupo | `MainWindow.build_advanced_conditions` | `advanced_groups`, `AdvancedConditions` | Solo armonización visual: no hay captura original inequívoca. |

## Trabajo

1. Incorporar componentes Qt clásicos reutilizables: fondo ornamental dibujado,
   pastillas de temporada/jornada, bordes en relieve, pestañas y listas compactas.
2. Reconstruir SSeguidos Manual/Automática con proporciones de referencias 01–03
   y conservar los controles conectados a `run_*`.
3. Sustituir el spinner visual de FSSeguidos por una lista vertical de totales,
   conservar la selección por total y cuatro columnas de referencia 04.
4. Compactar Interrupciones y sus figuras según 05–07; añadir Distancias por
   1/X/2/V según 08, con filtro de distancia máxima exacta entre posiciones
   consecutivas de cada familia de signos.
5. Dar a Cuenta/Grupo los componentes compartidos sin atribuirles paridad de
   píxeles que no está documentada.
6. Fotografiar las cinco vistas con referencia y comparar geometría, corregir
   desviaciones; probar generación, activación, persistencia y desactivación.

## Decisión matemática

La distancia de un signo se mide como la diferencia entre índices consecutivos
de sus apariciones entre los 14 partidos. Si aparece menos de dos veces, su
distancia máxima es 0. Para V, X y 2 se consideran la misma familia. Esta
regla implementa la definición explícita del prompt v2; la pantalla original
no permite confirmar todas las convenciones internas de WIN1X2.

## Aceptación

- Controles reales y accesibles, selección blanca/verde y estado persistente.
- La pestaña exterior desactivada no filtra; cada Aplicar se evalúa de manera
  independiente y conserva la configuración al desmarcarse.
- Distancias funciona sobre columnas de 14 signos y no incluye Pleno al 15.
- Tests de dominio/UI y cinco capturas con comparación visual contra referencia.
- Documentación de diferencias visibles pendientes sin declarar paridad donde
  las referencias no alcanzan a mostrar detalles.

## Resultado de la revisión

Los componentes compartidos están en `ui/classic_reductions.py`; la regla
independiente está en `domain/sign_distance.py` y `domain/reduction_rules.py`.
La matriz Cuenta, las figuras FSSeguidos, los bloques de SSeguidos, la matriz
Interrupciones y la vista Distancias siguen conectados al estado real. Se
crearon capturas y mapas de diferencias en
`docs/validacion_visual/reducciones_v1_0_22/` mediante el script reproducible.

La piel ornamental es una aproximación dibujada en Qt. Persisten diferencias
de relieve, tipografía, elementos gráficos y posiciones menores con las
capturas originales. Cuenta/Grupo solo se armonizan porque el paquete no da
una referencia original inequívoca para estas dos vistas.
