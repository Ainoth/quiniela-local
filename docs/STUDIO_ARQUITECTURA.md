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
