# PC Studio: primera entrega de la base funcional

10 de octubre de 2026. Solo escritorio; Android no se modifica.

Esta entrega empieza a implementar la [especificación](ESPECIFICACION_PC.md).
No completa los 15 módulos ni toda la fase 1. Conserva Tkinter y los editores
existentes mientras se separan servicios y almacenamiento; no se presenta como
una migración Qt terminada ni una IA entrenada.

## Cambios utilizables

- Siete secciones: Inicio, Crear Quiniela, Optimizar, Análisis, Escrutinio,
  Mis Sistemas y Configuración. La quiniela compacta queda visible a la izquierda.
- Inicio prioriza crear automáticamente, crear manualmente y consultar premios.
  Se reutilizan los diálogos de generación, condiciones y seguimiento existentes.
- Navegación por jornadas con partidos publicados y temporadas locales;
  «En curso» vuelve a la editable. Anteriores, futuras y finalizadas son de consulta.
  Los últimos horarios y resultados intervienen en identificar la vigente.
- SQLite local con sistemas asociados a temporada/jornada, copias con nombre,
  versiones inmutables, comprobación SHA-256 y recuperación de versiones como copias.
- Conservación del desarrollo de origen. Optimizar selecciona sus columnas y
  restaurar origen recupera las apuestas sin inventar otras. Reabrir el programa
  conserva esa relación. La base visible es la unión, no un desarrollo cartesiano nuevo.
- Análisis compara por partido **modelo deportivo** y **porcentajes jugados**.
  Configuración permite escoger la fuente para el siguiente cálculo.
  Los porcentajes públicos se validan contra temporada, jornada, numeración,
  rangos y suma antes de guardar o utilizar la caché. No se convierten en
  probabilidades deportivas por cambiarles el nombre.
- Guardado de probabilidades normalizadas 0–1 y una captura del origen de generación.
  El modelo sigue siendo la heurística de forma reciente, no una predicción calibrada.
  Sin histórico se identifica el supuesto 40/30/30. No se propone un Pleno 1–1
  automáticamente como si fuera una predicción de goles.
- TXT importado en la jornada seleccionada, exportación JSON con identidad,
  y TXT/copiar/enlace de validación existentes. Los repetidos se conservan como
  apuestas; el formato de edición actual admite un solo Pleno por desarrollo.
  Para varios Plenos se utiliza el escrutador independiente sin perder sus apuestas.
- Lectura PRE por campo fijo de dos caracteres y acumulación de los conceptos
  de 14 y Pleno. Los importes agregados se suman con `Decimal`.
- Si falta el directo de una jornada **no se consulta automáticamente otra**.
  El escrutador captura temporada, jornada y desarrollo, evitando que navegar
  en la ventana principal cambie silenciosamente las apuestas comprobadas.
- Abrir el asistente respeta la base manual y no aplica filtros recomendados
  escondidos. Las barras siguen disponibles para cambios explícitos.
- Acciones del pie accesibles; paneles con scroll, filas adaptables y recuadros
  alineados. Cierre cancela tareas pendientes para evitar errores Tcl al reiniciar.

El precio mostrado cuenta las apuestas seleccionadas a 0,75 €; una sola columna
no se duplica ni se cuenta como dos en silencio. El optimizador mantiene su
mínimo de dos apuestas y 1,50 €. El destino de validación debe comprobarse aparte:
la app no sella apuestas, verifica compras ni confirma importes de una web externa.

## Datos personales y migración

`desktop_data/systems.sqlite3` contiene sistemas y versiones. `desktop_data/` está
excluido de Git. `pronosticos.json` permanece intacto; la primera migración guarda
una copia en `desktop_data/legacy-pronosticos.json` y separa sus selecciones según
las claves de temporada/jornada.

El archivo antiguo no identifica con fiabilidad la jornada de sus columnas de
desarrollo. Por seguridad se conservan como **sin asignar**, sin colocarlas
automáticamente en la vigente. Inicio avisa de ello. En Mis Sistemas, «Asignar
desarrollo antiguo sin jornada» permite confirmar su pertenencia a la jornada
seleccionada, también si es una jornada pasada. La asignación crea una copia
archivada, no modifica el sistema anterior ni habilita edición de pronósticos
pasados. Navega primero a su jornada real; no se fuerza una asignación equivocada.

Los errores de validación no marcan como completada la migración ni sobrescriben
el archivo original. Una versión SQLite posterior a la soportada se rechaza, no
se degrada silenciosamente.

Para probar sin acceder al estado del usuario:

```bash
QUINIELA_STATE_DIR=/ruta/de/pruebas python3 app.py
```

Las pruebas GUI crean sus propios datos, caché y bases temporales.

## Comprobaciones

```bash
python3 -m unittest discover -v
# Con DISPLAY disponible; no usa datos personales ni realiza pagos:
RUN_PC_GUI_TESTS=1 python3 -m unittest discover -v
python3 app.py --check
```

Se comprueban fuentes/caché, PRE, premios acumulados, migración y rollback,
integridad de versiones, separación de jornadas, recuperación del desarrollo,
reinicio, fuente modelo/público, barras y botones de generación, protección de
diálogos abiertos, ausencia de fallback a resultados de otra jornada y diseños
de 1024×678 y 1320×790. También se ha inspeccionado visualmente la ventana reducida.
El sistema operativo de prueba es Linux; no se afirma una validación de un
instalador Windows que aún no se ha construido.

## Pendiente

UI Qt y empaquetado multiplataforma, bloqueos/plantillas completos, importación
JSON/XML, Plenos distintos dentro del editor, auditoría integral de filtros,
procesamiento masivo cancelable, garantías verificadas, IA calibrada, rentabilidad,
simulaciones, peñas, PDF y formatos oficiales/QR. La reducción disponible sigue
siendo heurística: sus probabilidades y estadísticas **no son garantías**.
