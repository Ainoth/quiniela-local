# 07 · Archivos, fuentes, integraciones y seguridad

## Matrices locales del generador Normal (v1.0.8)

El importador de probabilidades admite UTF-8 CSV/TXT con cabecera
`number,home,away,p1,px,p2,source,captured_at` (separador coma, punto y coma,
tabulación o barra vertical), 14 filas ordenadas y una sola fuente/fecha. Los
valores pueden expresarse como fracciones cuya suma es 1 o porcentajes cuya
suma redondeada está entre 99 y 101. Las columnas de equipo y jornada se validan
contra el boleto abierto antes de guardar. Se admite una columna opcional `kind`
(`classification`, `form5`, `history` o `custom`).

La forma JSON versionada usa `schema: "quiniela_ai_studio.probabilities"`,
`version: 1`, `round_key`, `source`, `captured_at`, `kind` y `matches`: una lista
ordenada de 14 objetos `{number, home, away, p1, px, p2}`. Las columnas 1/X/2
para reutilizar se importan como líneas de 14 signos, CSV con columna
`signs14`/`column`/`columna`, o JSON `schema:
"quiniela_ai_studio.columns"`, `version: 1`, `columns: [{"signs14": "…"}]`.
Archivos con pleno de 16 signos se rechazan con mensaje explícito, no se recorta
el Pleno silenciosamente. El tamaño máximo de importación es 20 MiB.

Los formatos X2_2003/Covadonga no tienen parser hasta disponer de una
especificación abierta verificable. En el manual WIN1X2 se citan rutas de
fuentes históricas como `X2_2003\\Fuentes\\datos\\f\\covadonga.txt`; esa
referencia no define el esquema de columnas ni concede equivalencia. No se
registran como disponibles datos que no estén instalados o importados.

## 1. Formato JSON propio v1

Definir esquema JSON y validar rigurosamente:

```json
{
  "schema": "quiniela_ai_studio.selection",
  "version": 1,
  "draw_id": "DEMO-2026-01",
  "demo": true,
  "ruleset_id": "demo-v1",
  "picks14": ["1", "1X", "2", "X", "1X2", "1", "1", "X", "2", "1", "X", "1", "1", "2"],
  "full15": [["0", "1"], ["1", "1"]],
  "unit_price_cents": 75,
  "metadata": {"author": "local", "algorithm": "manual", "seed": null}
}
```

**El precio 75 del ejemplo es sintético y no una afirmación sobre la tarifa actual**. Los valores del esquema deben provenir de `GameRuleset` verificado o de demo. `full15` representa parejas explícitas (sin multiplicar combinaciones inadvertidamente). La información de versión y modalidad es obligatoria. Añadir checksum opcional en contenedores exportados, pero no inferir autenticidad oficial del JSON.

Para columnas concretas, otra variante `quiniela_ai_studio.columns` con `columns: [{"signs14":"1X...","full15":["0","M"]}]`; se especificará la longitud exacta 14 y sin signos múltiples en `signs14`.

## 2. TXT clásico de apuestas

La exportación escribe una apuesta por línea, sin cabecera ni separadores: 14
signos `1`, `X` o `2`, seguidos por los dos signos del Pleno (`0`, `1`, `2` o
`M`, local y visitante). Cada línea tiene 16 caracteres; las copias se repiten
en líneas separadas. Ejemplo estructural: `1X2…(14 signos)…10`. Se exige que
cada apuesta tenga el Pleno completo. Esta salida conserva la disposición del
archivo clásico mostrado por el usuario.

La importación también reconoce registros antiguos de 14 signos sin Pleno,
pero eso no cambia el formato de exportación.

## 3. Formato TXT mínimo futuro

Línea de columna propia: `SSSSSSSSSSSSSS;GH;GA`, con 14 caracteres de signos y G `0|1|2|M`. Definir encabezado comentado con versión, jornada y modalidad para no confundir sistemas de diferente jornada. Importar líneas sin cabecera solo con asistente que pida/valide formato; en exportación usar UTF-8 y saltos de línea definidos.

## 4. XML, ASCII legado, AD243, ASD(JSON), NUM

- Crear interfaz `FormatAdapter`, `detect`, `read`, `write`, `validate`, `schema_version`, `capabilities` y conjunto de fixtures.
- **No inventar** la estructura de AD243, ASD u otros formatos propietarios/externos a partir del historial. Solo implementar con especificaciones públicas/licencias y ejemplos auténticos con autorización.
- Conversión reversible en subconjunto común validado; advertir pérdidas de metadatos, Pleno al 15 y apuesta complementaria.
- Tratar codificaciones, decimales/comas, separadores, tamaños límites y cabeceras mal formadas.
- Si un formato no está soportado, presentar «Formato no disponible» sin producir un archivo aparentemente válido.

## 5. Fuentes y conectores externos

La descarga de porcentajes de Quinielista identifica la petición por número de
jornada, sin parámetro de temporada. Por ello solo se usa para la jornada en
curso; para temporadas pasadas se conserva el porcentaje ya guardado o se
importan datos ligados explícitamente a esa jornada. Al validar equipos, se
tolera la marca `W` de Quinielista antes de `(F)` (por ejemplo, `Badalona
W.(F)` frente a `Badalona (F)`); cualquier otra diferencia de identidad sigue
siendo un error.

Proveedores registrados con identificación, base URL, licencia, limitación de peticiones, formatos, disponibilidad, zona horaria, mecanismo de autenticación y política de caché. Los datos externos pasan por `validate -> normalize -> compare -> stage -> commit`. **Nunca sobrescribir sin más una jornada** ni mezclar porcentajes de distintas horas sin explicarlo.

Conector SELAE: únicamente métodos públicos/permitidos y fuentes oficiales documentadas. Si no existe API abierta y autorizada, proporcionar importación manual o por fichero; no presuponer acceso mediante scraping que pueda violar condiciones de uso.

Conector casas de apuestas: datos bajo sus permisos y condiciones; separar probabilidades implícitas de cuotas y márgenes de los porcentajes SELAE.

## 6. QR y boleto

- `internal_qr`: formato propio con identificador/versionado, útil para importar un sistema a la misma app; **no es validación oficial**.
- `official_qr`: módulo desactivado hasta disponer de especificación, autorización y tests con validadores compatibles; mismo para impresión de formularios oficiales exactos.
- `PDF` y boleto local: claramente «Resumen no validado» hasta confirmación externa.
- Las operaciones de envío a un portal autorizado deben tener vista previa, confirmación explícita, protección frente a dobles envíos, estado `pending|accepted|rejected`, comprobante y auditoría.

## 7. Seguridad y datos personales

- Tokenstore/secretos en almacén seguro del sistema si se necesitan; jamás dentro de ficheros exportados o logs.
- No almacenar credenciales SELAE o de casas de apuestas por defecto.
- Peñas: gestionar datos de participantes con políticas de minimización, borrado, copia y cifrado si es necesario.
- Exportaciones con nombre no ambiguo, guardado atómico, prevención de path traversal y tamaños máximos configurables.
- Toda conexión de red es visible en Configuración e identificable por proveedor y permisos.

## 7. Copias, trazabilidad y actualizaciones

- Mantener versión de esquema y migraciones reproducibles.
- Antes de migración irreversible, generar copia con nombre versionado y pedir confirmación si corresponde.
- Cada importación conserva huella hash, procedencia y posibles errores, sin duplicar secretamente columnas.
- Cada informe económico incluye «estimado/oficial», momento del dato y descripción de supuestos.
## 8. Resultados históricos para estadísticas de Cuenta/Racha (v1.0.9)

El CSV histórico integrado admite `season,round,results14` y campos opcionales
`score_01`…`score_15`, cada uno como marcador `goles_local-goles_visitante`.
El mismo esquema puede importarse desde CSV UTF-8 o JSON como lista de objetos,
o un objeto `{ "results": [...] }`. La app lo carga al iniciar y fusiona los
datos importados por temporada/jornada; un marcador importado debe producir el
mismo signo publicado. Los marcadores adicionales completan jornadas existentes.
`results14` es una cadena de exactamente 14 caracteres de `1`, `X`, `2`. Cada
pareja temporada/jornada debe ser única. Se rechazan ficheros/filas marcados
como demo o `synthetic_final`; no se asignan identidades de partido ni se
deducen resultados ausentes. La fuente (nombre del fichero), temporada,
jornada, resultado y marcadores disponibles quedan almacenados localmente para
poder explicar la muestra estadística. Este esquema abierto no se presenta como formato oficial
de SELAE ni como compatibilidad con bases propietarias históricas.

## 9. Marcador en directo alternativo (v1.0.16)

### Escrutinio publicado con PRE provisional (v1.0.28)

Cuando los 15 marcadores están finalizados y el PRE aún no contiene el reparto,
el adaptador `infrastructure/published_scrutiny.py` consulta una página pública
de resultados y premios. Es un espejo secundario, identificado en la tarjeta,
no un canal oficial de validación de apuestas. Antes de aceptar importes,
comprueba fecha, temporada, jornada, equipos y orden de los 15 partidos,
marcadores, signos, Pleno y seis categorías. Guarda el escrutinio verificado
en configuración local con la identidad de la jornada. Si falta algún dato
o la página no responde, no calcula dinero. El PRE definitivo local mantiene
prioridad cuando está disponible.

La fuente primaria del marcador es Quinielista/Dataradar. Si no conecta, no
devuelve una jornada interpretable o deja sin marcador partidos cuyo horario
ya pasó, el adaptador consulta el scoreboard
JSON público de ESPN en `esp.1` (Primera), `esp.2` (Segunda) y `esp.w.1` (Liga F),
en `https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard?dates=YYYYMMDD`,
usando las fechas del calendario local. Solo asigna el evento cuando coinciden
fecha, local y visitante; los nombres femeninos llevan `(F)` solo en la interfaz.
El campo `state` distingue `pre`, `in` y `post`: los valores 0–0 de eventos `pre`
se ignoran. La fuente se guarda con la caché del marcador y se muestra en Aciertos.

Cuando hay datos de las dos fuentes, se conservan los resultados primarios y se
completan solo los partidos vacíos con resultados ESPN validados. ESPN es un
respaldo público no oficial para la quiniela, no una fuente de SELAE.
Si una competición no está cubierta o sus equipos no se emparejan de forma exacta,
la fila queda sin marcador. No se buscan por nombre parcial ni se completan scores
faltantes con otras fuentes sin validar la identidad.
