# Boleto estable y resultados completos · v1.0.1

RF-UX-002: conservar la forma de la quiniela al ampliar la ventana; las casillas
no se desplazan ni las filas se estiran. Dar prioridad a los 14 resultados y el
Pleno en Aciertos, con menos altura para la tabla de apuestas.

Implementación: panel izquierdo de ancho fijo, filas de altura constante y
contenido alineado arriba, dejando espacio sobrante al pie. Vista de marcadores
y lista de apuestas separadas por un divisor vertical ajustable; reparto inicial
calculado para mostrar los 15 partidos completos. En pantallas pequeñas se
mantiene desplazamiento sin esconder Generar ni los controles de Pleno.

Aceptación: geometría invariable entre dos tamaños amplios, marcador completo
sin desplazamiento a 1920×975 y 1200×975, selección de apuesta intacta al cambiar
el tamaño, funcionamiento manual y botones accesibles a 1024×768. Sin cambios
en apuestas, cálculos o persistencia. Pruebas: `test_aciertos_layout.py`.

Verificado: 226 pruebas Studio correctas, 2 omitidas por TXT personales ausentes;
32 pruebas históricas correctas. Ruff E9/F/I, diff, self-check y arranque Qt/X11
correctos. Capturas sintéticas revisadas a 1920×975 y 1024×768; el perfil del
usuario no se modifica para estas comprobaciones. El cambio se ve al reabrir.
