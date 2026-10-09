# Escritorio integrado v0.1.1

10/10/2026. AI Studio es la interfaz principal; el lanzador Tkinter se conserva
para funciones que todavía no han alcanzado paridad. Android queda fuera.

## Qué se ha integrado

| Función | Procedencia y resultado |
|---|---|
| Jornadas, nombres y horarios | Lector WIN1X2 Qt mejorado con archivos en mayúsculas, calendario, finales y jornada pendiente |
| Descargar datos | Adaptador de Quiniela Local, ejecutado en segundo plano dentro de Qt |
| Importar Datosg / ZIP | Copia propia, validación y revisión antes de aplicar; no altera la carpeta original |
| Porcentajes jugados XML | Adaptador compartido, validación de temporada/jornada/orden/equipos; fuente pública separada |
| Marcador | Adaptador de Quiniela Local; consulta manual, caché por jornada y comprobación offline |
| Premios guardados | Lector PRE Qt por campos fijos; acumulación 14 + Pleno en céntimos |
| Sistemas anteriores | Todas las versiones SQLite identificadas se recuperan como copias; originales y hashes comprobados |
| Filtros básicos | Motor puro anterior: variantes, X, 2, rachas, distancia X y coincidencias con referencia |
| Restaurar origen | Recupera columnas exactas antes de filtros/presupuesto; cantidades y Plenos conservados |
| Constructor / almacenamiento | Qt: bloqueos, plantillas, versiones, auditoría y TXT/JSON; fuentes/precio congelados |

## Uso

1. Abre **Quiniela AI Studio** desde el escritorio.
2. Inicio → **Descargar / actualizar datos**, o **Importar datos locales**.
3. Revisa las jornadas y equipos; pulsa **Importar datos revisados**.
4. **En curso** lleva a la jornada pendiente identificada por el calendario.
5. Crea un sistema nuevo. Si ya existe, **Actualizar fuentes del sistema** crea
   una versión con las fuentes actuales, conservando apuestas y precio.
6. Para ordenar con los porcentajes jugados, elige la fuente **Público** en Crear
   Quiniela. Esa fuente expresa popularidad; nunca se presenta como deportiva.
7. Configuración → **Recuperar sistemas SQLite de Quiniela Local**: elige
   `desktop_data/systems.sqlite3`. Primero deben estar importadas sus jornadas.
   La base original no se modifica y repetir la importación no duplica las copias.
8. Escrutinio → **Actualizar marcador**, **Ver directo guardado** o **Premios
   guardados**. Una jornada ausente en el proveedor no provoca consultar otra.
9. Optimizar → activa y revisa los filtros. Las versiones previas se conservan;
   **Restaurar desarrollo de origen** recupera las apuestas anteriores.

El directo no concede premios económicos. Los resultados pendientes no son X;
los confirmados y máximo posible se calculan por apuesta. El Pleno provisional
se muestra como provisional y no se usa como categoría definitiva.

La cancelación de red espera a terminar la petición en curso (timeout de hasta
30 s); la ventana sigue respondiendo. Cerrar cancela y cierra cuando termina.
Una descarga inválida, descartada o cancelada conserva los datos anteriores.
Si solo fallan los porcentajes, se puede importar el calendario con el aviso;
se conserva la fuente pública anterior únicamente si los equipos coinciden.
Las fuentes manuales existentes se omiten y se explican en la revisión.

## Límites y pendientes

- Filtros expertos (figuras/grupos/valoraciones), historial deportivo y generador
  heurístico antiguo aún requieren integración independiente. El núcleo básico
  aquí no declara paridad completa ni IA entrenada.
- Consulta del marcador bajo acción manual; el refresco periódico automático
  anterior queda pendiente. La caché conserva la última consulta válida.
- Calendario local y último día conocido permiten edición local; falta una
  fuente autorizada de cierre oficial. Exportar no confirma validación/pago.
- Los sistemas antiguos no guardan identidad completa de equipos/fuentes.
  Se vinculan mediante su temporada/jornada ya importada, con revisión explícita;
  sus probabilidades originales quedan como metadatos, sin crear un modelo nuevo.
- Sistemas de jornadas no importadas se omiten con aviso; importar esas jornadas
  y repetir recupera sus copias. No se asignan globales de identidad desconocida.
- Linux probado; Windows preparado, sin prueba nativa. El wheel requiere Python
  y Qt; no es un EXE autónomo. No se ha modificado Android ni los APK.

## Requisitos y comprobación

RF-JOR-001/002/005/007/008, RF-PRO-002/008, RF-ESC-001/004,
RF-FIL-001/002/005, RF-ARC-001, RF-AUD-001/002/007/008: cobertura parcial con
pruebas en `test_integration.py`, `test_filters_integration.py` y `test_ui.py`.
La matriz original conserva los requisitos completos; estas evidencias no
certifican las fases restantes.

```bash
QT_QPA_PLATFORM=offscreen .venv-studio/bin/python -m pytest -q
RUN_PC_GUI_TESTS=1 python3 -m unittest discover -q
./run_studio.sh --data-dir /tmp/studio-fusion-prueba --smoke-test
.venv-studio/bin/ruff check --select F quiniela_studio data_updater.py tests/studio
.venv-studio/bin/python -m build --outdir artifacts/studio-fusion
```

SQLite migra de esquema 1 a 2 con una copia previa automática. Para volver a
v0.1 hay que cerrar la app y restaurar esa copia, conservando también una copia
del esquema 2. El lanzador Tkinter utiliza su propia base y sigue disponible.
