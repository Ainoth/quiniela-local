# Quiniela AI Studio v0.1.0 — escritorio ejecutable

Entrega inicial acotada a partir de `ESPECIFICACION_PC.md`.
La implementación inicial se basó en `ESPECIFICACION_PC.md`; la documentación
original estaba disponible en el paquete `Quiniela_AI_Studio_Codex_v1_0.zip`
y se incorpora ahora al repositorio. Su hoja de ruta es `08_PLAN_VERSIONES.md`.
La matriz T01–T17 siguiente corresponde al plano de PC anterior; no sustituye
la matriz RF de `12_MATRIZ_TRAZABILIDAD.md`, que debe auditarse contra el código.
Hay diferencias pendientes de reconciliar con el encargo original: el paquete
vive en `quiniela_studio/` y declara Python >=3.10, en lugar de
`src/quiniela_ai_studio/` y Python >=3.11. Esta entrega no afirma paridad completa
con Quiniela Local ni cumplimiento íntegro de la especificación original.

## Qué funciona

- Interfaz Qt en español, siete secciones y pie con cantidad/coste real.
- Primera apertura sin conexión con una jornada **sintética de demostración**.
- Lectura local de todas las jornadas publicadas en carpetas WIN1X2 PRE/FEC/Hor,
  campo fijo de jornada, equipos y espacio de nombres de proveedor.
- Importación de jornadas JSON con fuentes deportiva/público diferenciadas.
- Constructor manual: 14 partidos, recuadros 1/X/2, Pleno 0/1/2/M y bloqueos.
- Plantillas 0–10 explícitas; nivel 10 sin bloqueos = 3 triples, 7 dobles y 4 fijos
  = 3.456 columnas. No se incrementa un presupuesto automáticamente.
- Generación cartesiana exacta, progreso/cancelación y límite visible de 100.000.
- Optimización como selección del origen bajo presupuesto, conservando cantidades.
  Orden por probabilidad deportiva bajo independencia, o lexicográfico si falta.
- SQLite con migración numerada, claves externas, versiones inmutables, auditoría
  y copia consistente. Fuente/precio se congelan en cada sistema.
- Restaurar la versión anterior mediante una nueva versión (Ctrl+Z).
- TXT y JSON completos, cantidades/repetidos visibles; exportación sin límite de
  100 filas. TXT sin identidad se vincula a la jornada elegida en la cabecera.
- Escrutinio manual de escenarios con pendientes y lectura de premios PRE
  definitivos. 14 y Pleno se acumulan como conceptos separados cuando corresponde.
- Recuperación conservadora de pronósticos antiguos con copia del original.
  Las columnas globales se guardan **sin asignar**, no se mezclan con la jornada vigente.

## Instalación en Linux Mint

Python 3.10 o posterior. En Mint 22.3 se ha probado con Python 3.12.3.
Desde la carpeta del proyecto:

```bash
./run_studio.sh
```

En una instalación nueva el lanzador crea `.venv-studio` e instala las dependencias.
Si falta soporte para `venv`, instalarlo con el gestor de paquetes de Mint
(paquete `python3-venv`). La primera instalación necesita Internet; los siguientes
arranques, datos locales y cálculos no lo necesitan.

Qt/X11 necesita `libxcb-cursor0`. El lanzador comprueba su presencia; si falta,
descarga el paquete de la distribución y lo extrae **solo dentro de `.venv-studio`**,
sin sudo. Como alternativa se puede instalar `libxcb-cursor0` desde el gestor de
paquetes. El arranque Python/console detecta la biblioteca local y vuelve a
iniciarse con su ruta antes de cargar Qt.

Instalación manual:

```bash
python3 -m venv .venv-studio
.venv-studio/bin/python -m pip install -e '.[test]'
./run_studio.sh
```

El acceso directo nuevo **Quiniela AI Studio** abre esta versión. El acceso
**Quiniela Local** y `python3 app.py` conservan la aplicación anterior.

## Windows preparado

Código, SQLite y formatos independientes del sistema; lanzador `.bat` incluido.
Windows no se ha ejecutado en este equipo Linux: esta entrega no afirma una
validación nativa ni incluye un EXE autónomo.

1. Instalar Python 3.10 o posterior con `py` y pip.
2. Descomprimir/copiar el proyecto.
3. Ejecutar `run_studio.bat` (primer arranque necesita Internet).

O desde PowerShell:

```powershell
py -3 -m venv .venv-studio
.\.venv-studio\Scripts\python.exe -m pip install -e ".[test]"
.\.venv-studio\Scripts\python.exe -m quiniela_studio
```

El wheel Python de esta entrega se instala mediante `pip install archivo.whl`.
Qt se obtiene como dependencia nativa para cada plataforma; el wheel no es un
EXE ni un paquete con Python y Qt embebidos. Antes de redistribuir un instalador
embebido, revisar licencias y avisos de Qt/PySide y sus componentes.

## Comprobar que funciona

```bash
./run_studio.sh --self-check
.venv-studio/bin/python -m pytest -q
python3 -m unittest -q
./run_studio.sh --data-dir /tmp/studio-prueba --smoke-test
```

Prueba desde la interfaz:

1. En **Inicio**, pulsa **Probar ejemplo de 6 columnas**.
2. Al terminar, el pie muestra **6 apuestas y 4,50 €**, Pleno M1.
3. En **Optimizar**, escribe **1,50 €** y selecciona apuestas del origen:
   quedan **2 apuestas por 1,50 €**. El origen sigue guardado como versión anterior.
4. En **Mis Sistemas**, exporta TXT: hay 2 líneas de 16 signos. El JSON conserva
   jornada, base, bloqueos, cantidades y fuentes congeladas.
5. Cierra y abre: el sistema y su versión siguen guardados en DEMO/J01.
6. En **Crear Quiniela**, crea otro sistema, aplica nivel 10: base = 3.456.
   Un partido bloqueado conserva sus signos al aplicar plantillas.

Para datos reales: **Configuración → Importar carpeta WIN1X2 / Datosg**.
En este equipo existe `/home/toni/Documentos/Datosg`; no se lee ni se modifica
sin elegirla expresamente. Los porcentajes `.mdb` no se convierten en deportiva.
La ausencia de fuentes aparece como **Sin datos**.

Con FEC local, solo la fecha nominal de hoy se considera editable; jornadas
históricas y futuras son de consulta. No se inventa una hora oficial de cierre.
La política es conservadora y falta integrar un calendario/cierre autorizado.
Una jornada marcada en curso deja de ser editable al vencer su fecha nominal.

## Datos, recuperación y rollback

- Linux: `~/.local/share/quiniela-ai-studio/studio.sqlite3` (respeta XDG_DATA_HOME).
- Windows: `%LOCALAPPDATA%\QuinielaAIStudio\studio.sqlite3`.
- `--data-dir RUTA` permite un perfil aislado para pruebas o copias.
- **Configuración → Crear copia de seguridad SQLite** produce un archivo nuevo.
- Para restaurar: cerrar Studio, copiar la copia sobre `studio.sqlite3` en ese
  perfil y volver a abrir. Conservar una copia del archivo reemplazado.
- Los pronósticos históricos no se migran al arrancar. La recuperación copia
  el original y solo atribuye selecciones cuya jornada ya existe en SQLite.
  Las selecciones parciales se recuperan como borradores: posiciones no guardadas
  usan el fijo 1 y deben revisarse; no se generan apuestas automáticamente.
- El desarrollo global queda en `migration-.../sin-asignar.json`, con copia
  del original; la asignación explícita de esas columnas sigue pendiente.
- Rollback de aplicación: utilizar el lanzador anterior. Sus datos no se modifican.
  No abrir una base de esquema posterior con v0.1: se rechaza explícitamente.

## Matriz v0.1 frente al plano completo

| Prueba original | Estado v0.1 | Evidencia / pendiente |
|---|---|---|
| T01 | Parcial | Ejemplo 6; tamaño universo y codificación ternaria; no generación masiva 4.782.969 |
| T02 | Parcial | Versiones, reinicio, separación y migración conservadora; asignación interactiva de globales pendiente |
| T03 | Parcial | Plantillas 0–10 y bloqueos; barra adicional de ajustes rápidos pendiente |
| T04 | Parcial | Validación de probabilidades y tipos; validación en proveedores online pendiente |
| T05 | Pendiente | Catálogo completo de filtros en fase 2 |
| T06 | Cubierto en selección | Subconjunto exacto, presupuesto y origen conservado; reducción por cobertura pendiente |
| T07 | Pendiente | Verificador independiente y certificados en fase 2 |
| T08 | Parcial | Probabilidad única, ceros y cantidades; sucesos de 10–13 y uniones avanzadas pendientes |
| T09 | Cubierto en lector nuevo | Jornada 2, acertantes 7 e importes 10 caracteres; registro con campos pegados |
| T10 | Parcial | Conceptos acumulables, pendientes y sin importes inventados; directo automático pendiente en Qt |
| T11 | Pendiente | Monte Carlo en fase 3 |
| T12 | Parcial | TXT/JSON y cantidades; XML y taller en fases posteriores |
| T13 | Pendiente | Modelos entrenados y backtesting en fase 3 |
| T14 | Pendiente | Peñas y reparto en fase 4 |
| T15 | Parcial | Qt 1024×768, controles y modelo sin reset idéntico; validación manual escalada/Windows pendiente |
| T16 | Parcial | Cancelación, copias y recuperación local; descargas/caché de red pendientes en Qt |
| T17 | Parcial | Tests y wheel portátil, arranque real Mint; paridad y prueba nativa Windows pendientes |

## Próxima fase

Antes de ampliar filtros/IA, completar las partes de fase 1: calendario y cierre,
proveedores autorizados/caché, directo Qt, asignación explícita de globales,
ajustes rápidos, navegación/archivo y paridad con las funciones de la app anterior.
Después: motor masivo, reductor y garantías. El nombre AI Studio no significa
que v0.1 tenga un modelo entrenado ni una rentabilidad predicha.
