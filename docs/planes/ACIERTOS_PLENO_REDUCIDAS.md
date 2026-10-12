# Aciertos automáticos, Pleno múltiple y reducidas — 0.1.8

RF-ESC-001/002/003, RF-JOR-007, RF-QUI-002/003/004, RF-RED-001/003/009.
Encargo explícito amplía el alcance: incremento acotado, sin declarar completas
las fases v0.3/v0.5 ni integración de sellado.

- Comprobación: marcador de 15 partidos, aciertos/fallos/pendientes por apuesta,
  Pleno visible y separado de la categoría de 14. Actualización al abrir la
  sección y cada 60 s, con una petición a la vez, caché y errores no modales.
- Pleno múltiple: selección independiente de goles por equipo; expandir todas
  las parejas y contar/cobrar cada apuesta. Persistencia/JSON/TXT y límite global.
- Pestaña Reducidas: seis tablas BOE enlazadas por el artículo SELAE indicado por el usuario; elección explícita de partidos, combinaciones
  adicionales al directo, Plenos múltiples y aplicación opcional como copia.
- Verificación exhaustiva sobre universos de las tablas: cardinalidad, cobertura mínima verificada por tabla, condicionada a acertar la base, mapeo de dobles, combinación extra y P15.
- No aplicar tablas a conjuntos ya filtrados como si mantuvieran garantías.
  La pestaña genera una copia desde el boleto y lo explica antes de aplicar.

Fuentes: página de reducidas indicada por el usuario; norma 18.2 y 23 del PDF
actualmente enlazado desde normativa SELAE; BOE-A-2009-12204 para las matrices del artículo, no como fuente de vigencia
ni de reglas de Pleno actuales. La resolución BOE ha dejado de estar vigente.
El catálogo se etiqueta con esta procedencia; no es un formato de sellado.
Se observaron diferencias de transcripción entre matrices 2009 y el PDF 2019;
no se afirma identidad con todas las matrices del PDF 2019. La sexta matriz
del artículo tiene mínimo matemático verificado de 9, no se promete 12/13.

Resultado: incremento 0.1.8 implementado. 120 pruebas Studio y 32 históricas
correctas, matrices verificadas exhaustivamente y QA Qt/X11. Proveedor real
validado contra identidad de jornada, sin leer apuestas personales. Pleno
siempre visible; copia reducida opcional. No se declaran fases completas,
Windows nativo ni formato de sellado autorizado.
