# 10 · Guía de interfaz, experiencia y accesibilidad

## 1. Filosofía

App visual y moderna, sin exceso de opciones, que presente primero las tareas que importan: preparar, optimizar, comprobar. Diseño similar a un panel de control profesional, con navegación lateral o pestañas; no replicar la interfaz ni activos gráficos del programa de referencia. Texto y ayuda en español.

## 2. Siete secciones

1. **Inicio**: jornada, partidos, estado de carga, resumen de últimas acciones y tres acciones («Crear», «Abrir», «Escrutar»).
2. **Crear Quiniela**: casillas 1/X/2, casillas de goles P15, selectores fijo/doble/triple, coste en vivo, presupuesto, asistente automático cuando haya modelo.
3. **Optimizar**: modos «Básico» (presupuesto, objetivo) y «Experto» (filtros, reservas, CB, reducción, cobertura, parámetros).
4. **Análisis**: probabilidades deportivas, porcentajes públicos, desviaciones, estadísticas, rentabilidad y simulaciones con fuentes visibles.
5. **Escrutinio**: progreso de partidos, apuestas, aciertos, premios posibles/definitivos, importación de otras combinaciones.
6. **Mis Sistemas**: historial, plantillas, exportaciones, informes, peñas y comparación de estrategias.
7. **Configuración**: proveedores/credenciales, reglas/versiones, límites de presupuesto, backups, logs y diagnósticos.

## 3. Comportamientos específicos

- No presentar 40 filtros en una misma ventana. Filtros por categorías, buscador, presets y acordeón «Avanzado».
- Mostrar coste, cantidad de apuestas y status de datos junto al botón de ejecutar/guardar.
- Mostrar métricas antes/después: columnas, coste, filtros, cobertura (exacta o estimada) y probabilidades.
- En cálculos largos: barra, etapa, tiempo transcurrido (real si disponible), cancelar; **no fabricar tiempos estimados**.
- Al cancelar: estado `cancelado`, conjuntos parciales seguros, informe reproducible y opción reiniciar.
- Pantalla de auditoría legible: «El programa observó esto → eligió estas opciones → descartó estos sistemas → porque…».
- Números y porcentajes sin truncar; etiquetas con unidades y tooltip opcional, nombres completos en informes.
- Confirmaciones antes de borrar proyectos, resetear BD, importar sobreescribiendo o enviar apuestas reales.
- Dialogo de importación con validación previa, número de columnas y P15 detectados, formato de origen y problemas.
- Para el modo demo, encabezado «DATOS DE EJEMPLO — NO CORRESPONDEN A UNA JORNADA REAL».

## 4. Pantallas clave y estados

**Constructor**: tabla de partidos con tres toggles por partido, marcador P15 separado, panel resumen («fijos/dobles/triples, columnas, coste»), acciones guardar/generar/exportar.

**Filtros**: lista con estado, nombre, resumen del intervalo, botón detalles; vista de supervivientes. La selección de reservas se explica como tolerancia a reglas concretas.

**Reducción**: objetivo de coste y umbral k, selector del universo Ω (advertencia), número candidato, algoritmo, botón de verificación independiente; al finalizar informe exacto/estimado.

**Escrutinio**: progreso deportivo y categoría de aciertos; nunca mostrar premio monetario definitivo si no está publicado.

**Análisis**: dos ejes comparables P deportiva y % jugado, historia del origen, fecha y modelo; rentabilidad con incertidumbre explícita.

## 5. Accesibilidad y portabilidad

- Navegación teclado, foco visible, contraste suficiente y etiquetas accesibles.
- No depender solo de colores; texto, iconos y tabla complementaria.
- Tamaño de ventana mínimo razonable y diseño que se adapte; evitar puntos suspensivos en cifras económicas.
- Ajuste de escalado UI; tema oscuro/claro; persistencia de preferencia.
- Atajos documentados; ayuda contextual con ejemplos de categorías de premio y diferencia entre garantía y probabilidad.
- Linux Mint Cinnamon y Windows: respetar apariencia nativa, no usar rutas absolutas incrustadas.

## 6. Preparación del flujo automático

Futuro asistente en 4 pasos: (1) datos y fecha; (2) presupuesto y riesgo; (3) vista previa de propuestas; (4) verificación y exportación. Debe funcionar con predicción inactiva mostrando «Generador estadístico no disponible; utilice modos manual/aleatorio», no con resultados inventados.
