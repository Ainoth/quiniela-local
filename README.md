# Quiniela Local

Aplicación local y sin registro que lee directamente los datos instalados por
WIN1X2. No modifica sus bases de datos ni necesita conexión a Internet.

## Funciones de esta primera versión

- Detecta la temporada y la jornada vigente.
- Lee los 15 partidos y horarios desde `Datosg/PRE*.txt` y `Datosg/Hor*.txt`.
- Traduce códigos mediante `Datosg/WEQUIPOS.TXT`.
- Calcula una orientación 1/X/2 con hasta ocho resultados recientes de cada
  equipo y una pequeña corrección por ventaja local.
- Guarda automáticamente el pronóstico del usuario.
- Exporta una quiniela legible en formato de texto.
- Valida y copia los 14 signos más el marcador del Pleno al 15.
- Abre la web oficial de TULOTERO para introducir, revisar y confirmar la
  apuesta manualmente.

La probabilidad mostrada es un modelo sencillo, no una garantía ni una
recomendación de apuesta. Cuando no existe historial suficiente, se usa una
estimación neutral.

TULOTERO no publica una API para que aplicaciones de terceros carguen apuestas.
Por seguridad, Quiniela Local no guarda credenciales ni realiza compras: copia
el pronóstico y abre la web oficial, donde el usuario debe verificar y confirmar.

## Ejecución

```bash
python3 quiniela_local/app.py
```

Si la aplicación no está dentro de la carpeta de WIN1X2, indica la carpeta de
datos de esta forma:

```bash
WIN1X2_DATA_DIR=/ruta/a/WIN1X2/Datosg python3 app.py
```

Para comprobar únicamente la lectura de datos:

```bash
python3 quiniela_local/app.py --check
```

`update_and_run.sh` actualiza el repositorio con un avance rápido desde GitHub
y abre la aplicación. Si no hay conexión, utiliza la última versión local.
