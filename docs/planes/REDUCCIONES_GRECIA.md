# Plan: reductores de WIN1X2 en Quiniela AI Studio

## Objetivo y alcance

Adaptar al escritorio Qt la organización visual del manual `win1x2.pdf` y sus
17 pasos de condiciones (2–18), sin copiar código, marcas de reductores,
garantías ni recursos visuales de terceros. Mantener el boleto fijo como
referencia y representar los grupos como una matriz compacta de partidos por
número y columnas seleccionables 1/X/2. Los nombres de los equipos solo aparecen
en el boleto base.

La navegación tendrá una única sección **Reducciones** con 17 pestañas internas,
una por familia del manual. Las condiciones que ya existen (conteo de signos,
rachas, interrupciones, referencia/coincidencias, grupos individuales, relación
entre grupos y tolerancia) se moverán o enlazarán a su pestaña correspondiente;
no habrá una segunda implementación con controles duplicados. Optimizar seguirá
siendo el único lugar para escoger una cartera con presupuesto sin garantía de
cobertura. La pestaña Reducciones será para imponer condiciones y crear/verificar
una reducción condicionada.

## Decisión de algoritmo

Motor propio **Atenea** de cobertura, con bitsets de resultados, ganancia
marginal determinista y mejora por intercambios. Modos del mismo motor (no
reductores paralelos): **Hermes** prioriza velocidad; **Atenea** añade
intercambios y reinicios reproducibles; **Artemisa** intenta búsqueda exacta
acotada y solo certifica el óptimo cuando termina. El recorte por presupuesto
usa la misma función y se comparte con Optimizar en lugar de duplicar su selector.

Universo y promesa visibles en cada informe: resultados admitidos por la base,
por condiciones activas, o universo completo solo si se enumera explícitamente.
La cobertura del Pleno se informa por separado. Una reducción se etiqueta como
garantía únicamente si la verificación exhaustiva sobre el universo declarado
confirma que cada resultado alcanza el umbral. En universos muestreados solo se
declara cobertura observada/estimada. Algoritmos, límites, semilla y hash se
versionan. No se afirma equivalencia con Atenea, Súper-Reductor u otros motores
del manual WIN1X2.

Fundamento algorítmico consultado: cobertura es una función submodular monótona;
el greedy para cardinalidad fija tiene el límite clásico 1−1/e, y set-cover es
NP-difícil en general. Referencias primarias registradas en la decisión: Chvátal
(1979), DOI 10.1287/moor.4.3.233; Nemhauser, Wolsey y Fisher (1978), *Mathematical
Programming* 14, 265–294. Las garantías de aproximación matemáticas no implican
garantías deportivas.

## Mapa de pestañas y deduplicación

| Paso / pestaña | Familia | Reutilización/semántica |
|---|---|---|
| 2. Recuento | Variantes, X, 2, figuras y distribución ponderada | Reutiliza `BasicFilters`; suma ponderada original versionada |
| 3. Rachas | Signos seguidos, longitudes y figuras de rachas | Reutiliza máximos actuales; añade rangos con semántica explícita |
| 4. Cambios y distancias | Interrupciones, seguidas y distancia entre signos | Reutiliza cambios/distancia actuales |
| 5. Repeticiones | Coincidencias con resultado anterior o enfrentamiento | Requiere fuente histórica identificada; sin datos queda desactivada |
| 6. Parejas | Patrones/frecuencias y parejas relacionadas | Motor de patrones parametrizado; política de solape declarada |
| 7. Tríos | Patrones/frecuencias y tríos relacionados | Mismo contrato de patrones, sin duplicar lógica |
| 8. Cuartetos | Patrones/frecuencias y relacionados | Mismo contrato de patrones |
| 9. Quintetos | Patrones/frecuencias y relacionados | Mismo contrato de patrones |
| 10. Coincidencias | Igualdad entre partidos y signos iguales | Reutiliza referencia existente; vínculos de partidos declarados |
| 11. Grupos individuales | Conteos, aciertos, rachas, cambios, figuras, aciertos agrupados | Evoluciona `AdvancedConditions`; matriz compacta 1/X/2 |
| 12. Grupos relacionados | Aciertos/figuras, repeticiones, sumas y diferencias | Reutiliza relaciones/tolerancia existentes; sin UI repetida |
| 13. Frecuencia de aciertos | Rangos por aciertos, sumas, diferencias, escaleras y orden probabilístico | Grupos/columnas explícitos; probabilidades solo si hay snapshot |
| 14. Sumas y valoraciones | Sumas/rangos/productos/coeficiente | Pesos finitos y procedencia visible; nunca presentados como ROI |
| 15. Columnas | Suma, eliminación y diferencia entre columnas/bloques | Opera sobre apuestas generadas/importadas |
| 16. Si… entonces | Implicación acotada entre dos grupos | Intervalos tipados/validados y tolerancia compartida |
| 17. Reservas | Tolerancia a fallos y niveles | Un solo contador global compartido, sin duplicar tolerancias |
| 18. Reducción Atenea | Umbral 13/12/11/10, porcentaje o presupuesto | Un motor con selector de umbral, universo explícito y verificador común |

Son las 17 pestañas internas exactas de los pasos 2–18. Los umbrales 13/12/11/10
son objetivos dentro de Reducción Atenea, no cuatro reductores duplicados.

Además, la reducción por tramos se implementa como vista de resultados por
presupuesto/valoración cuando no duplique el filtro de sumas existente. División,
eliminación manual y borrar duplicados permanecen como acciones de gestión del
desarrollo, no filtros automáticos.

## Fases y criterios de aceptación

### Fase A — Arquitectura, UI y motor de condiciones

- RF-FIL-015: catálogo tipado y serializable de reglas nuevas, dominio sin Qt.
- RF-UX-007: pestañas estilo WIN1X2 en un `QTabWidget` compacto/scrollable,
  panel azul, matriz de grupos con 14 filas numeradas, columnas de grupo y
  botones 1/X/2; boleto de nombres fijo al lado.
- RF-FIL-016: activar/desactivar condiciones en vivo, coste/apuestas, filtros
  combinados con AND y resumen legible por condición.
- Migración compatible; se evita persistir filtros repetidos.

### Fase B — Filtros simples/intermedios

Conteos/figuras, rachas, cambios, distancias, repeticiones si hay resultados,
patrones, coincidencias, grupos por máscaras, grupos relacionados y reservas.
Oráculos independientes y tablas pequeñas exhaustivas.

### Fase C — Patrones/valoraciones y expresiones

Parejas–quintetos, sumas/productos/rangos ponderados, frecuencias relacionadas,
IF/THEN acotado e importación CSV. Expresiones seguras y validación previa.

### Fase D — Atenea y garantías

Cobertura por bitsets, greedy Hermes, mejora por swaps Atenea, búsqueda exacta
acotada y verificador independiente. Cancelación, progreso, semilla, auditoría y
exportación de informe. No se afirma garantía si no hay comprobación exhaustiva.

### Fase E — Integración, UX y documentación

Comparación con Optimizar sin duplicar selector de presupuesto; tramos únicamente
si añaden una operación distinta. Actualizar guía, catálogo, matriz, changelog,
datos de ejemplo y validación visual Qt en Linux. Windows queda pendiente de
ejecución nativa explícita.

## Verificación mínima

- Las reglas desactivadas no cambian el desarrollo; permutar orden de filtros
  duros conserva el conjunto final.
- Oráculo independiente contra enumeración completa para 1–6 partidos.
- Las selecciones no duplican apuesta+Pleno; coste exacto en céntimos.
- Para `n=2`, todas las 9 columnas cubren cualquier resultado al 2; una columna
  no garantiza 2/2 sobre las 9.
- Greedy y local search son deterministas con la misma semilla; no se llaman
  óptimo/global si la prueba exacta no termina.
- Pruebas UI: navegación por pestañas, selección 1/X/2 de grupo, tolerancia,
  restauración y no repetición de equipos.
- Suite completa, Ruff, `git diff --check` y smoke test Linux; preservar los TXT
  personales y algoritmos/versiones de datos anteriores.
