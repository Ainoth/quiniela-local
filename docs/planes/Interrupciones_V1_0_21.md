# Interrupciones y Distancias — v1.0.21

## Objetivo y ubicación

Añadir una pestaña independiente **Interrupciones** dentro de Crear quiniela →
Reducciones. SSeguidos y FSSeguidos continúan disponibles. El interruptor
externo está blanco/desactivado al iniciar y es el que incluye sus reglas en
el cálculo. Sus dos paneles conservan Aplicar propio: **Interrupciones** y
**Distancias**.

## Regla matemática

Se evalúan las 13 transiciones `t_i = 1[c_i != c_(i+1)]` de los 14 signos. El
Pleno al 15 no participa. El perfil del ejemplo
`11X21221XX121X` es `(10, 4, 4-4-2)`.

La matriz se interpreta como pares `(total de cambios, racha máxima de unos
consecutivos en el vector de transiciones)`. Una celda verde admite ese par;
blanca lo rechaza; gris indica que la base actual no puede alcanzarlo. Esta
lectura es **original/provisional**, pues el texto/capturas recibidos no
certifican la convención del programa antiguo para cada columna (especialmente
la 0).

Distancias almacena `(total, figura)`, donde figura es la partición descendente
de las rachas máximas de unos del vector de cambios. `3-2-1-1` significa cuatro
bloques de transiciones consecutivas cuya suma es siete. La aplicación de
ambos paneles usa AND; se pueden probar por separado.

## Métodos

- **Manual:** selecciona celdas y figuras alcanzables. Cada panel tiene su
  propio Aplicar, Marca todos e Inicializar.
- **Azar:** muestrea los perfiles alcanzables de la base con semilla guardada.
  Riesgo Mínimo conserva todos los perfiles; Medio y Máximo reducen
  progresivamente la fracción de perfiles únicos. Política original, no
  probabilidad deportiva.
- **Automática:** cuenta perfiles observados en resultados finales reales de
  las temporadas seleccionadas. Recomienda perfiles compatibles con la base,
  priorizando los más frecuentes hasta la cobertura muestral configurada.
  Es descriptiva y no predictiva.

Los datos históricos se cargan desde el recurso integrado existente. La
selección de temporadas se guarda por jornada. No se solicita importar un
fichero para usar esta vista.

## Estado y aceptación

- [x] Dominio puro para perfil exacto y DP de perfiles alcanzables.
- [x] Dos reglas serializables independientes con `tab_index=18`.
- [x] UI compacta de cuatro métodos/paneles reales; controles cuadrados
  accesibles sin tics.
- [x] Integración con el motor, persistencia por sistema y activación externa
  desactivada por defecto.
- [x] Pruebas de ejemplo, DP exhaustivo, separación, modos y restauración.
- [x] Documentación de semántica provisional y advertencia descriptiva.
