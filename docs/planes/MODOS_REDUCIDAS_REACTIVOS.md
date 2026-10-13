# Normal y reducidas independientes; selección diferenciada — 13/10/2026

RF-QUI-005/006, RF-GEN-003/005, RF-RED-001/002, RF-PRO-003/008.

1. Mantener dos sistemas independientes por jornada (normal/reducida), sin
   usar el desarrollo normal como base de las reducidas. Guardar modo en
   parámetros, compatible con JSON/SQLite anteriores, sin alterar sus hashes.
2. Reducidas: elegir cualquiera de las seis tablas existentes; construir fijos,
   dobles y triples específicos según porcentajes y posiciones de mayor
   incertidumbre. Respetar bloqueos válidos, permitir ajustes manuales y mostrar
   alternativas de columnas/coste antes de generar. El Pleno multiplica ambas.
3. Normal: barra reactiva 0–10 con agrupación de eventos, sin botón obligatorio.
   No actuar al cargar/restaurar, navegar o estando en Optimizar; no dejar que
   un evento atrasado modifique otra jornada/sistema. Cancelar al cerrar.
4. Diferenciación original opcional 0–10: puntuación log(p) − alpha*log(q),
   alpha=nivel/10, p mercado y q popularidad de Quinielista. Normalizar únicamente
   como pesos para ordenar signos; no tratar pesos como probabilidades reales
   ni valor esperado. q acotado por epsilon para ceros. Solo con ambas fuentes,
   sin inventar datos. Pleno aplica el mismo criterio si hay ambas marginales.
   No se afirma tasa de aciertos superior, premio garantizado o exclusividad.
5. Pruebas: todas las tablas, independencia, reinicio, slider reactivo y navegación,
   fuentes ausentes, bloqueos, Plenos y coste/exportación; preservar apuestas
   normales y versiones antiguas. Ejecutar suites, Ruff básico y Qt nativo.

Límites: se reutilizan las matrices BOE 2009 ya verificadas; no se cambian reglas
oficiales, no se añaden reductores propietarios ni una IA calibrada. Garantía
solo condicional a acertar toda la base indicada, no el premio económico/Pleno.
Popularidad de Quinielista no es el total SELAE y no permite estimar premios.
Las posiciones propuestas son una heurística determinista, modificables por
el usuario. Android no se toca. Documentar, probar y sincronizar el incremento.

Referencia revisada: https://www.eduardolosilla.es/quiniela/ayudas/cuotas distingue
probabilidades de mercado y porcentajes jugados. Se usa únicamente como contexto;
nuestro criterio continuo usa público de Quinielista, no CR propietario ni LAE.
El recuento de aciertos sigue siendo el habitual: se modifica la selección,
no las reglas. Sin backtesting todavía; sería necesario comparar estrategias
con igual presupuesto, datos anteriores al cierre y evaluación fuera de muestra.

Las copias reducidas antiguas se mantienen en Mis Sistemas, pero no se usan
automáticamente como la nueva base independiente. Los archivos originales no
se convierten ni se eliminan; el modo se guarda en parámetros de sistemas nuevos.

Validación del incremento: 179 pruebas Studio y 32 históricas con GUI, Ruff
E9/F/I, self-check y arranque Qt nativo correctos. Inspección de ambos modos a
1024×768; coste de reducida mostrado separado del universo directo, controles
de generación visibles y ajuste manual de posiciones plegado por defecto.
