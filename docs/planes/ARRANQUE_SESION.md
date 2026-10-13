# Arranque con elección de quiniela · v1.0.1

RF-QUI-010: al abrir, preguntar si se continúa la última quiniela. Sí abre el
sistema guardado sin crear revisiones; No crea una quiniela normal independiente
de la jornada actual. Conservar todas las anteriores y los modos Normal/Reducidas.

Implementación: registrar el último sistema abierto en ajustes portables,
mostrar la pregunta una vez desde el arranque gráfico y mantener `--smoke-test`
automático. Datos actuales en caché permiten crear sin red; si faltan, descargar
asíncronamente y crear tras validar/importar. Un fallo deja todas las quinielas
guardadas; no presenta una jornada antigua como actual. Un perfil solo demo
permanece explícitamente ficticio.

Aceptación: clic real Sí/No, hashes anteriores intactos, nueva sin apuestas ni
Pleno, restauración de reducida aun existiendo normal, primera sesión demo,
descarga de jornada ausente y conservación ante error de red. Pruebas:
`tests/studio/test_startup.py` y regresión de las suites existentes.

Verificación local: 223 pruebas Studio correctas, 2 omitidas por TXT personales
no disponibles; 32 históricas correctas. Las 6 pruebas nuevas incluyen ambos
botones de la pregunta real. Ruff E9/F/I y diff correctos; self-check y arranque
Qt/X11 automático comprobados con un perfil temporal. Diálogo revisado
visualmente; el cambio se activa en la siguiente apertura del software.
