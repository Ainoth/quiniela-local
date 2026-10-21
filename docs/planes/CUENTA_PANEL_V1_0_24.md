# Cuenta: panel de figuras e histórico v1.0.24

## Objetivo

Completar la subpestaña Cuenta según la referencia WIN1X2, dejando tres zonas
compactas: recuentos V/X/2, figuras conjuntas (Veces/V/X/2) y distribución
histórica 1/X/2 con temporadas a su lado. Debajo se presenta Filtros.

## Decisiones

- Cuenta sigue siendo propietaria de los recuentos `V = X + 2`, `X` y `2` en
  los catorce partidos. El Pleno queda excluido.
- Los perfiles de Figuras son tuplas conjuntas `(V, X, 2)` contadas sobre el
  histórico final realmente seleccionado. La tabla contiene las tuplas
  observadas en ese histórico; los cuadrados V/X/2 siguen permitiendo definir
  manualmente cantidades aunque una tupla no aparezca en la tabla. Su cuadrado
  Aplicar crea una regla `allowed_profile`; apagado conserva la elección y
  excluye esa condición. El panel se comparte al cambiar de método, evitando
  duplicar controles y mantener una sola selección.
- Distribución Signos cuenta resultados `1/X/2` de esas mismas temporadas y
  muestra cantidades y porcentajes descriptivos, sin inferir el siguiente
  resultado.
- Temporadas permanecen en Automática, a la derecha de Distribución Signos.
  Las estadísticas cambian en el momento en que se modifica la selección.
- Filtros muestra la separación entre equis ya existente. Usa un solo control
  cuadrado visible y el mismo `BasicFilters`; puede actuar desde Cuenta o desde
  Cambio si esa pestaña se vuelve visible en otra fase.
- La piel ornamental se omite únicamente en Cuenta; se conserva el fondo
  oscuro estándar de la aplicación.

## Requisitos y comprobación

- RF-UX-019: reconstruir el panel Cuenta compacto con Figuras, Distribución,
  Temporadas en su posición, controles de aplicación y la zona Filtros.
- RF-FIL-025: filtrar perfiles conjuntos exactos V/X/2 y habilitar la distancia
  entre equis desde Cuenta, conservando reglas, modo y activación exterior.
- Pruebas: tabla histórica y porcentajes totalizan 14 por jornada; perfil
  `(V,X,2)` admite únicamente las columnas coincidentes; la distancia filtra
  cuando Cuenta está activa y permanece inerte cuando su pestaña está apagada.
