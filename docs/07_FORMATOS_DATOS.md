# 07 · Archivos, fuentes, integraciones y seguridad

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

## 2. Formato TXT mínimo

Línea de columna propia: `SSSSSSSSSSSSSS;GH;GA`, con 14 caracteres de signos y G `0|1|2|M`. Definir encabezado comentado con versión, jornada y modalidad para no confundir sistemas de diferente jornada. Importar líneas sin cabecera solo con asistente que pida/valide formato; en exportación usar UTF-8 y saltos de línea definidos.

## 3. XML, ASCII legado, AD243, ASD(JSON), NUM

- Crear interfaz `FormatAdapter`, `detect`, `read`, `write`, `validate`, `schema_version`, `capabilities` y conjunto de fixtures.
- **No inventar** la estructura de AD243, ASD u otros formatos propietarios/externos a partir del historial. Solo implementar con especificaciones públicas/licencias y ejemplos auténticos con autorización.
- Conversión reversible en subconjunto común validado; advertir pérdidas de metadatos, Pleno al 15 y apuesta complementaria.
- Tratar codificaciones, decimales/comas, separadores, tamaños límites y cabeceras mal formadas.
- Si un formato no está soportado, presentar «Formato no disponible» sin producir un archivo aparentemente válido.

## 4. Fuentes y conectores externos

Proveedores registrados con identificación, base URL, licencia, limitación de peticiones, formatos, disponibilidad, zona horaria, mecanismo de autenticación y política de caché. Los datos externos pasan por `validate -> normalize -> compare -> stage -> commit`. **Nunca sobrescribir sin más una jornada** ni mezclar porcentajes de distintas horas sin explicarlo.

Conector SELAE: únicamente métodos públicos/permitidos y fuentes oficiales documentadas. Si no existe API abierta y autorizada, proporcionar importación manual o por fichero; no presuponer acceso mediante scraping que pueda violar condiciones de uso.

Conector casas de apuestas: datos bajo sus permisos y condiciones; separar probabilidades implícitas de cuotas y márgenes de los porcentajes SELAE.

## 5. QR y boleto

- `internal_qr`: formato propio con identificador/versionado, útil para importar un sistema a la misma app; **no es validación oficial**.
- `official_qr`: módulo desactivado hasta disponer de especificación, autorización y tests con validadores compatibles; mismo para impresión de formularios oficiales exactos.
- `PDF` y boleto local: claramente «Resumen no validado» hasta confirmación externa.
- Las operaciones de envío a un portal autorizado deben tener vista previa, confirmación explícita, protección frente a dobles envíos, estado `pending|accepted|rejected`, comprobante y auditoría.

## 6. Seguridad y datos personales

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
