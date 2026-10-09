# Fusión de escritorio — 10/10/2026

Objetivo: AI Studio como interfaz principal, reutilizando los adaptadores de
Quiniela Local. Android queda fuera; el lanzador Tkinter se conserva como respaldo.

## Incremento ejecutable

1. RF-JOR-001/005/007/008: importar carpeta Datosg o ZIP WIN1X2, descargar datos
   en segundo plano, previsualizar cambios, validar y aplicar en una transacción.
   Conservar instantáneas de sistemas, datos manuales y caché anterior si falla.
2. RF-PRO-002/008: importar porcentajes públicos del adaptador existente,
   validar temporada/jornada/numeración y distinguirlos de probabilidad deportiva.
3. RF-ESC-001/004: integrar el marcador existente, pendientes y confirmados,
   con caché por jornada y sin convertir un directo en premio definitivo.
4. RF-ARC-001 / RF-AUD-001: recuperar sistemas SQLite Tkinter como copias con
   apuestas exactas; no atribuir columnas sin jornada ni tocar la base original.
5. Integración visual: actualizar datos desde Inicio y Configuración, conservar
   constructor Qt, bloqueos, versiones, import/export y optimización.

## Criterios de aceptación

- Carpeta y ZIP sintéticos generan las mismas jornadas; case-insensitive.
- Paquetes inseguros, datos inválidos o cancelaciones no cambian la base activa.
- Actualizar datos no modifica las versiones ni apuestas guardadas.
- Descargar y consultar directo no bloquean Qt; cerrar espera de forma segura.
- Fallos parciales de porcentajes se explican; no se sustituyen por valores inventados.
- Consulta offline recupera los últimos datos aprobados.
- Migración SQLite es de solo lectura, idempotente y preserva cantidades/Plenos.
- Tests Studio, regresión Tkinter, arranque Qt real, diff-check y wheel verificados.

La paridad de filtros expertos y modelos entrenados no se declarará por importar
adaptadores. Se documentará lo integrado y lo que aún use el lanzador anterior.

## Resultado del incremento

Implementados los cinco puntos, junto con filtros básicos compartidos,
restauración de origen, selección explícita de fuente pública y actualización
versionada de fuentes. La documentación de uso y límites está en
`docs/STUDIO_FUSION.md`; filtros expertos/modelo histórico siguen pendientes.
