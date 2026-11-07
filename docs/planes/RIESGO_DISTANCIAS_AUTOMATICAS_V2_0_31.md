# Recomendaciones de riesgo y Distancias — v2.0.31

## Objetivo

Corregir RF-RED-026 tras la revisión visual: el selector de riesgo debe
recalcular la recomendación al cambiar, y Distancias debe mostrar los cuatro
signos y los valores elegidos en Manual y Automática.

## Trabajo y aceptación

- [x] Medir el riesgo de Distancias sobre perfiles conjuntos 1/X/2/V; mostrar
  cobertura del objetivo y cobertura observada tras proyectar los valores.
- [x] Mostrar las casillas de distancia en Automática y permitir inspeccionar
  qué valores se activaron para cada signo.
- [x] Recalcular al cambiar el riesgo en Automática para Interrupciones y
  Distancias, y reflejar pares/figuras y muestra en el resumen.
- [x] Añadir pruebas deterministas de que los tres riesgos cambian las
  recomendaciones y de que el cálculo conjunto es correcto.
- [x] Actualizar matriz de trazabilidad y changelog.

Las recomendaciones históricas son descriptivas; no predicen resultados ni
garantizan cobertura futura. Los filtros siguen siendo independientes y se
combinan con las demás reducciones activas.
