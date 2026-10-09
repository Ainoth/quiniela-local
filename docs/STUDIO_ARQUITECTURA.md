# Arquitectura y formatos de Studio v0.1

```text
ui.py (Qt) → services.py → domain.py / engine.py
                    ↓
                 storage.py (SQLite) / files.py
                    ↑
                 providers.py (WIN1X2 local)
```

- `domain.py`: entidades inmutables y validación; sin Qt/red/disco.
- `engine.py`: combinatoria, plantillas, probabilidad, selección y escrutinio.
- `services.py`: creación y versiones; aplica edición protegida y evita resultados obsoletos.
- `storage.py`: esquema SQLite 1; rounds, systems, versions y audit, claves externas.
- `files.py`: escritura atómica de TXT y JSON versionado.
- `providers.py`: PRE por campos fijos, equipos/calendario/horarios y recuperación.
- `demo.py`: datos sintéticos explícitos para probar offline.
- `ui.py`: siete secciones, modelo de tablas virtualizado y eventos Qt.
- `__main__.py`: CLI, perfil, autocomprobación, prueba de arranque y soporte X11.

Todas las operaciones de DB se hacen en el hilo principal. La generación acotada
se ejecuta en un QThread con entradas inmutables, evento de cancelación comprobado
cada 256 columnas y señales Qt. v0.1 no pretende resolver CPU masiva por ese hilo:
la fase 2 deberá mover CPU intensiva a procesos/núcleo nativo y procesar por bloques.
No se aplican estructuras incompletas ni resultados de una revisión obsoleta.
El refresco de tablas idénticas no hace reset; cambios de celdas mantienen selección.

## Contratos de v0.1

- 14 signos por columna; Pleno aparte como 2 valores 0/1/2/M.
- Cada apuesta incluye cantidad; coste = suma(cantidad) × precio congelado.
- Todo sistema tiene ID, revisión, jornada, base, bloqueos, apuestas exactas y hash.
- Cada revisión conserva `round_snapshot`: datos, precio, reglas y fuentes de origen.
- Public y sport nunca se mezclan. Valores normalizados, finitos, suma 1 ± 1e-6.
- La masa P14 suma columnas únicas; el coste/premio sí incluye cantidades.
- El cero de probabilidad produce logP = -infinito.
- Reducir presupuesto nunca crea columnas ajenas al desarrollo.
- PRE: jornada [0:2], acertantes [2:44] en bloques de 7, importes [44:104]
  en bloques de 10, signos [104:118], Pleno hexadecimal [118].
- Dinero siempre en céntimos; PRE se convierte con Decimal.

## JSON

Un sistema exportado contiene:

```json
{"format":"quiniela-studio","version":1,"round":{},"system":{}}
```

Las estructuras completas son `dataclasses.asdict(Round)` y
`dataclasses.asdict(SystemVersion)`; `files.read_system` las valida. No ejecutar
expresiones de archivos. Máximo 20 MiB por importación.

Una jornada para importar desde Configuración contiene:

```json
{"format":"quiniela-studio-round","version":1,"round":{}}
```

Para generar un ejemplo válido completo (en el directorio que elijas):

```bash
.venv-studio/bin/python -c 'import json; from dataclasses import asdict; from quiniela_studio.demo import demo_round; print(json.dumps({"format":"quiniela-studio-round","version":1,"round":asdict(demo_round())},ensure_ascii=False,indent=2))' > jornada-demo.json
```

El JSON propio no afirma compatibilidad con ASD ni QR oficiales.
TXT: 16 signos por línea al exportar; 14 o 16 al importar; repetidos se agregan
como cantidad si la opción visible está marcada. P15 faltante bloquea TXT.

## Política de datos

No hay lectura/red/migración implícita de datos personales al arrancar.
La importación local valida los registros antes de guardar las jornadas.
No cambia las bases de WIN1X2. Identidad de equipo: `win1x2:temporada:código`;
la competición específica todavía debe reforzarse antes del modelo histórico.
No se importan heurísticas o `.mdb` como probabilidad deportiva.

El paquete utiliza Python y PySide6. Documentación primaria consultada para
instalación y despliegue:
[Qt for Python — Getting Started](https://doc.qt.io/qtforpython-6/gettingstarted.html),
[Deployment](https://doc.qt.io/qtforpython-6/deployment/index.html).

## Integración v0.1.1

`integration.py` adapta `data_updater.py` y `live_results.py`, compartidos con
Tkinter; no importa `app.py` ni crea ventanas Tk. `filters.py` usa únicamente el
motor puro `quiniela_engine.FilterConfig`. El wheel incluye esos tres módulos.
`ui.DataTask` realiza E/S en un QThread, con entradas capturadas y señales.
Los resultados pasan por revisión y aplicación en el hilo principal.

SQLite esquema 2 añade `settings` para selección, caché de datos y marcador por
jornada. La migración desde esquema 1 crea antes una copia `*-pre-v2-*.sqlite3`.
La transacción de importación conserva versiones existentes y actualiza juntos
jornadas, auditoría y directorio de caché. Las carpetas `data-cache/datos-*` son
copias independientes: errores/cancelación/descarte eliminan solo la preparación
propia, nunca datos de WIN1X2 o de la versión anterior. Las cachés antiguas aprobadas
se conservan; no hay purga automática en esta entrega.

La jornada actual es la primera pendiente publicada cuyo último día conocido
no ha vencido; las horas y resultados PRE complementan la fecha nominal.
`editable_until` limita la edición local al último día del calendario. No es
una hora oficial de cierre ni confirma que un canal acepte apuestas.

Los porcentajes requieren temporada, jornada, 15 posiciones y equipos en el
orden esperado. `TEAM_ALIASES` documenta equivalencias nominales explícitas
(acentos/puntuación y abreviaturas comprobadas); no se usa búsqueda difusa.
Un XML sin identidad de equipos se rechaza. El público no alimenta deportiva
ni la distribución del Pleno. La opción pública de ranking se llama popularidad.

Las copias SQLite Tkinter se leen en `mode=ro`; se verifican hashes y jornada.
Cada versión se copia como sistema separado de revisión 1, conservando parámetros
originales (incluido desarrollo de origen). No se reconstruyen columnas desde
la base ni se inventan fuentes de probabilidad a partir de datos actuales.
Los borradores parciales se etiquetan; los fijos 1 provisionales deben revisarse.
El precio histórico fijo de esa app se conserva a 75 céntimos y se identifica
como referencia del software anterior, sin afirmar vigencia oficial.
