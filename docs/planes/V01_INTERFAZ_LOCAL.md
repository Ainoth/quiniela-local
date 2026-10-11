# v0.1 ejecutable con la experiencia de Quiniela Local

11/10/2026. Se conserva el núcleo comprobado y la descarga integrada; se corrige
la interfaz rechazada por el usuario. No se intentan fases 0.2–1.0 completas.

## Trabajo

- RF-QUI-001/002 y RF-AUD-004: aspecto azul de Quiniela Local, quiniela siempre
  visible a la izquierda, secciones a la derecha, descarga en la cabecera,
  Pleno con casillas 0/1/2/M y navegación anterior/siguiente.
- RF-QUI-003/004: contador de fijos/dobles/triples, coste del borrador en vivo,
  regla de precio demo editable sin alterar versiones anteriores.
- RF-ARC-001: generación perezosa y exportación directa completa sin guardar
  millones de objetos; conservar apuestas exactas para sistemas reducidos.
- RF-AUD-008: estructura src/quiniela_ai_studio con cuatro capas, Python >=3.11,
  rutas estándar mediante platformdirs y compatibilidad de importaciones previas.
- Pruebas del recorrido demo, fixtures de 12 apuestas / 900 céntimos,
  persistencia, import/export, escrutinio, GUI reducida y arranque real.

## Aceptación

Abrir sin red, editar y generar ejemplo, exportar/importar y escrutar con SQLite
persistente. Descargar/importar datos conserva el flujo integrado. La quiniela
sigue visible al cambiar de sección. Datos personales y Android intactos.
Windows preparado sin declarar pruebas nativas. Documento de entrega actualizado.

## Resultado

Completado el incremento v0.1, revisión 0.1.2. 81 pruebas Studio y 32
históricas correctas; arranque Qt X11 y revisión visual a 1024×768.
Wheel/sdist construidos y wheel comprobado fuera del repositorio, incluyendo
los tres módulos compartidos. Acceso de escritorio actualizado.
Instrucciones y límites en [STUDIO_V01_ENTREGA.md](../STUDIO_V01_ENTREGA.md).
La siguiente fase sigue siendo v0.2; Windows requiere prueba nativa.
