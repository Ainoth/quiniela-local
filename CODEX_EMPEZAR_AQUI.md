# Prompt inicial para pegar en Codex

Copia el texto siguiente en Codex después de abrir la carpeta del proyecto.

---

Quiero que desarrolles **Quiniela AI Studio** siguiendo la documentación de este repositorio. Lee `AGENTS.md`, `README.md` y `docs/00_INDICE.md`; después consulta los documentos técnicos necesarios. El historial de Quiniwin es una referencia de funcionalidades, NO una fuente de algoritmos o protocolos que se puedan copiar.

**ENCARGO DE ESTA SESIÓN: entregar la versión v0.1 ejecutable**, con este recorrido completo:

1. Crear el proyecto Python con estructura `src/quiniela_ai_studio/{domain,application,infrastructure,ui}`, `tests/`, `pyproject.toml`, `README.md` actualizado, scripts de instalación/ejecución para Linux y guía Windows; usar Python >=3.11 y PySide6.
2. Implementar entidades y validaciones de Jornada, Partido, Pronóstico 1/X/2, Pleno al 15 con 0/1/2/M, Selección múltiple y Columna concreta. Separar juego base y complemento Elige8, que queda preparado pero no implementado en v0.1.
3. Crear un **modo demo offline** con una jornada FICTICIA y señalizada como tal; permitir al usuario crear/editar 14 pronósticos y un pleno al 15, con fijos, dobles y triples.
4. Calcular cantidad exacta de columnas y coste a partir de un precio de apuesta guardado en una configuración de reglas versionada (no es necesario asumir una tarifa oficial). Usar enteros en céntimos.
5. Generar las apuestas al directo con iteración perezosa (sin materializar todo el universo); enseñar una vista limitada y exportar TXT/JSON propio con esquema documentado. Incorporar progreso y cancelación donde proceda.
6. Implementar un escrutinio **offline** sencillo a partir de resultados introducidos manualmente; distinguir correctamente los aciertos de 14 y la condición del Pleno al 15. No calcular premios económicos no comprobados.
7. Guardar/cargar proyecto localmente en SQLite; que no se pierda el trabajo al cerrar. Mantener auditoría de las acciones clave, con fecha, parámetros y resultados.
8. Diseñar UI clara en español con secciones Inicio, Crear Quiniela, Optimizar (placeholder explícito), Análisis (placeholder), Escrutinio, Mis Sistemas y Configuración. Los apartados futuros deben indicar «Pendiente de desarrollar», no fingir que funcionan.
9. Añadir pruebas unitarias y de integración para contar combinaciones, 1/X/2, pleno, persistencia, coste, exportación e importación; cubrir entradas inválidas, vacías, sin pleno y cifras grandes.
10. Entregar instrucciones simples de instalación, ejecución y prueba en Linux Mint, sin rutas fijas, y notas de Windows. Si no puedes ejecutar la GUI en tu entorno, prueba el dominio y documenta la limitación.

**Criterios de aceptación v0.1:** aplicación que se inicia en un entorno limpio, jornada demo visible, edición completa de pronósticos, combinaciones y costes matemáticamente correctos, exportación/importación de ida y vuelta, escrutinio básico correcto y tests reproducibles. Nada de apuestas reales ni scraping.

Antes de implementar, revisa que las decisiones estén alineadas con la arquitectura y redacta un plan breve. Implementa realmente la v0.1, ejecuta las pruebas disponibles y registra lo que queda para v0.2; no te limites a proponer una arquitectura.

---

## Prompts para las sesiones siguientes

Una vez terminada y probada cada versión, pide a Codex:

`Continúa con la siguiente versión pendiente de docs/08_PLAN_VERSIONES.md. Lee AGENTS.md, verifica el estado real del código, escribe plan, implementa criterios de aceptación, añade pruebas, ejecuta comprobaciones y actualiza la matriz de trazabilidad y CHANGELOG. No rompas lo ya implementado.`

**Importante:** el contenido de este paquete es documentación para Codex. No incluye un ejecutable ya construido.
