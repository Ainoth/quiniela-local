# Validación visual de Reducciones v1.0.22

Las imágenes `*_manual.png` y `*_automatica.png` muestran únicamente el lienzo
clásico con una jornada de demostración en una base SQLite temporal. No son
capturas de datos ni configuración del usuario. Se generan con:

```bash
QT_QPA_PLATFORM=offscreen .venv-studio/bin/python scripts/capture_classic_reductions.py
```

| Vista | Resultado | Comparación al original |
|---|---|---|
| SSeguidos Manual | [captura](sseguidos_manual.png) | [superposición](sseguidos_manual_overlay.png) · [diferencia](sseguidos_manual_diff.png) |
| SSeguidos Automática | [captura](sseguidos_automatica.png) | [superposición](sseguidos_automatica_overlay.png) · [diferencia](sseguidos_automatica_diff.png) |
| FSSeguidos Manual | [captura](fsseguidos_manual.png) | [superposición](fsseguidos_manual_overlay.png) · [diferencia](fsseguidos_manual_diff.png) |
| Interrupciones Manual | [captura](interrupciones_manual.png) | [superposición](interrupciones_manual_overlay.png) · [diferencia](interrupciones_manual_diff.png) |
| Distancias Manual | [captura](distancias_manual.png) | [superposición](distancias_manual_overlay.png) · [diferencia](distancias_manual_diff.png) |

El script escala cada lienzo manteniendo su relación de aspecto y recorta el
exceso central hasta el tamaño exacto de la referencia. La superposición es
50 % original y 50 % captura; el mapa de diferencias muestra distancia RGB
absoluta por píxel. Son instrumentos de revisión, no un porcentaje de
equivalencia: los datos de la jornada, la resolución de fuente, las fuentes
tipográficas y los controles nativos Qt difieren.

Se verificó que las cuatro columnas, las matrices escalonadas, las listas
blancas y la jerarquía de cabecera/modos/subpestañas ocupan áreas similares.
Siguen siendo diferencias visibles el escudo/imagen de fondo original, su
ornamentación en relieve, algunos tamaños y posiciones de rótulos, la forma
de los botones y el contenido de las listas, que depende de la base demo.
SSeguidos Manual es proporcionalmente algo más ancho que la referencia. Cuenta
([Manual](cuenta_manual.png), [Automática](cuenta_automatica.png)) y
[Grupo](grupo.png) se armonizaron con la misma piel; no existe una referencia
original inequívoca para afirmar paridad de píxeles.
