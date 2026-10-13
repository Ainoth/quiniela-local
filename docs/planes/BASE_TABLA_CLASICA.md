# Quiniela base con tabla clásica · v1.0.1

RF-UX-004: recuperar el formato de la imagen del usuario con partido, hora,
porcentajes y signos alineados. Filas alternas y tamaño fijo, manteniendo
bloqueos y el Pleno múltiple/manual/automático de la app actual.

La hora se presenta como día y HH:MM desde el calendario guardado. Modelo %
muestra la fuente deportiva; Jugado % la popularidad. Nunca se mezclan las dos
ni se fabrican valores si faltan. Nombres, fechas y procedencia completos en
ayuda contextual. La base conserva sus datos y apuestas exactos.

Aceptación: geometría estable, porcentaje visible y fiel a la fuente congelada,
cambio de fuente sin modificar apuestas fuera del constructor, falta de datos
señalada, Pleno compacto y botones/porcentajes alineados. Vista revisada con
clubes de la imagen y calendario ficticio explícito; pruebas de datos y selección
en `test_aciertos_layout.py`, Pleno y bloqueos en la suite existente.
