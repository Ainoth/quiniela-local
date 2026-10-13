# Pleno al 15: porcentajes y selección múltiple — 13/10/2026

RF-PRO-001/002/008, RF-QUI-002/003, RF-GEN-003/005.

Persistir `ProbabilitySnapshot.pleno_values` opcional: dos marginales de cuatro
valores 0/1/2/M (local y visitante), finitos, normalizados, sin presumir
independencia entre goles. JSON antiguo sin este campo sigue siendo válido.
Leer del XML completo `p_jugados_{g}{L|V}` y `p_bf_{g}{L|V}desc` (alternativa sin
decimales). Rechazar datos parciales/incorrectos, sin fabricar porcentajes.
Mostrar valores junto a las casillas, según la fuente elegida y congelada.

«Cambiar el boleto» también aplica el Pleno si la fuente lo publica. Si no,
mantiene la selección manual con aviso. Heurística propia, no garantía:

| Nivel | Goles local | Goles visitante | Parejas |
|---|---|---|---|
| 0–1 | 1 | 1 | 1 |
| 2–3 | 1 | 2 | 2 |
| 4–5 | 2 | 2 | 4 |
| 6–7 | 2 | 3 | 6 |
| 8 | 3 | 3 | 9 |
| 9 | 3 | 4 | 12 |
| 10 | 4 | 4 | 16 |

Ordenar goles por porcentaje decreciente y desempate 0/1/2/M; conservar orden
canónico en máscaras. El usuario puede corregir después cualquier casilla.
Los bloqueos de los 14 signos no cambian. No se añade un bloqueo del Pleno.
El servicio conserva por defecto parejas exactas importadas; la interfaz pide
explícitamente preselección del Pleno al cambiar el boleto.

La multiplicación ya existía y se mantiene: N columnas × parejas reales del
Pleno × precio por apuesta. Mostrarla explícita; la generación/TXT conservan
cada pareja, sin volver a expandir parejas no cartesianas importadas. Nivel 10
puede producir 3.456 × 16 = 55.296 apuestas, no solo 3.456; límites globales de
generación vigentes y coste visible antes de generar.

Aceptación: valores válidos/ausentes/corruptos, compatibilidad JSON antiguo,
preselección determinista, ampliación por niveles, fuente seleccionada, precio,
persistencia/exportación, preservación sin datos y parejas exactas antiguas.
No predicción de IA, distribución conjunta, calibración ni cambios Android.

RF-QUI-005: Deshacer restaura también parámetros/máscaras anteriores; antes
conservaba parámetros del Pleno nuevo y no recuperaba la selección múltiple.
Prueba explícita de recuperación del Pleno manual tras aplicar la plantilla.

Validación: 162 pruebas Studio y 32 históricas con GUI correctas; Ruff E9/F/I,
self-check y arranque Qt nativo correctos. Inspección visual a 1024×768:
porcentajes junto a casillas y botón Generar dentro de la ventana.
Descarga real 26-27/J13 comprobada: mercado local 33,97/36,68/19,80/9,55 y
visitante 18,18/30,99/26,42/24,41; popularidad se conserva separada.
