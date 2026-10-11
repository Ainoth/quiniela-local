# Recuperación de Ajustes rápidos — 0.1.6

RF-FIL-002/009, PC T03. La petición es la barra de condiciones de Quiniela Local,
no Cobertura progresiva del boleto. Retirar la barra equivocada de Optimizar y
mantener la barra de creación. Recuperar límites de X+2, X, 2, cambios entre
signos y rachas de 1/X/2. No convertir cambios entre signos en distancia entre X.

Decisión: la barra histórica endurecía condiciones al aumentar el nivel. La
instrucción del usuario prevalece: 0 usa los límites estrictos y 10 admite todas
las apuestas de origen. No importar el tope histórico 200/50 columnas como
regla de garantía; aquí se filtran apuestas exactas con los límites visibles.
Mover la barra cambia condiciones, no apuestas; Aplicar confirma el resultado.
Reaplicar un nivel más amplio toma el desarrollo de origen para poder recuperar
apuestas sin regenerar ni alterar el boleto por una plantilla.

Aceptación: pruebas de límites históricos, niveles anidados, 10 neutro,
serialización versión 2, condiciones activadas automáticamente, boleto intacto
al mover barra, recuperación de apuestas al subir a 10, error sin perder datos.

Resultado: 94 pruebas Studio correctas, Ruff F en el conjunto y Ruff completo
en filtros y nuevas pruebas. Captura Qt/X11 revisada con datos sintéticos.
Documentación y paquete 0.1.6 actualizados. Sin nuevo algoritmo de garantía.
