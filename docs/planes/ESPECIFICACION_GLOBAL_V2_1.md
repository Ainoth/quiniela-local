# Plan de trabajo — robustez y coherencia de Studio v2.1

## Objetivo

Cerrar brechas verificables de identidad de equipos, aislamiento de errores por
partido, reducciones combinadas y fluidez sin atribuir garantías estadísticas o
de cobertura que los datos no demuestren.

## Fases y aceptación

- [x] **Identidad y adaptadores**: ampliar alias y marcadores de género con
   rechazo de ambigüedad; ESPN/Dataradar conserva partidos confirmados aunque
   una fila sea dudosa. Pruebas deterministas.
- [ ] Añadir asignación manual de alias desde la interfaz y guardarla en
   SQLite para futuras jornadas.
- [x] **Datos parciales**: permitir representar explícitamente partidos sin datos,
   propagar el estado a la UI y evitar que una fila inválida descarte las demás;
   nunca completar probabilidades faltantes con valores inventados.
- [ ] **Filtros**: medir el camino real antes de vectorizar; verificar AND entre
   reducciones, semántica de Distancias/FSSeguidos e invariantes con apuestas
   ponderadas. Acelerar solo con equivalencia demostrada. Medición y ruta rápida
   para filtros neutros implementadas; vectorización de filtros activos pendiente.
- [x] **Persistencia SQLite**: activar WAL cuando SQLite lo permita e indexar
   las relaciones del esquema real.
- [ ] **Carga histórica**: diferir lectura/cálculo hasta que se soliciten.
  Los perfiles repetidos de rachas y conteos ahora se cachean en memoria;
  diferir la carga inicial de temporadas sigue pendiente.
- [ ] **Flujos e interfaz**: revisar el flujo Quiniela/Optimizar/Escrutinio,
   temporadas y barra de progreso contra requisitos RF concretos.
- [ ] **Conectores y modelos**: verificar contratos y disponibilidad por jornada;
   diferenciar datos públicos, cuotas, frecuencias descriptivas y modelos
   calibrados. No añadir EV/xG sin fuentes autorizadas y evaluación retrospectiva.

## Entrega inicial de esta revisión

- RF-DAT-011: alias explícitos y marcadores femeninos seguros.
- RF-DAT-012: una discrepancia de identidad en la alternativa ESPN no invalida
  los otros resultados confirmados.
- RF-STO-003: WAL/NORMAL e índices compatibles con el esquema existente.

## Criterios globales

- Cada fase actualiza pruebas, `docs/12_MATRIZ_TRAZABILIDAD.md` y changelog.
- No se cambia el formato/hashes de sistemas históricos ni datos personales.
- Ningún resultado desconocido se transforma en una probabilidad o predicción.
- Las afirmaciones de rendimiento se acompañan de mediciones reproducibles.
