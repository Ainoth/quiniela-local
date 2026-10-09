# Índice del proyecto de escritorio

Documentación de la implementación local; complementar con la especificación original incluida abajo.

- [Especificación de PC](ESPECIFICACION_PC.md): objetivo completo, arquitectura,
  módulos, contratos matemáticos, fases y pruebas T01–T17.
- [Entrega v0.1](STUDIO_V0_1.md): implementación disponible, instalación, uso,
  pruebas y matriz de cumplimiento. No equivale a finalizar la fase 1 completa.
- [Arquitectura y formatos](STUDIO_ARQUITECTURA.md): módulos, SQLite, fuentes,
  reglas, formatos de archivo y ampliaciones.
- [Registro de validación](STUDIO_VALIDACION.md): evidencias Linux, pruebas,
  medidas, empaquetado y límites de verificación de Windows.

---

# Mapa de documentación — orden de lectura para Codex

| Archivo | Propósito |
|---|---|
| `01_ESPECIFICACION_FUNCIONAL.md` | 15 módulos y requisitos funcionales codificados |
| `02_ARQUITECTURA.md` | Separación de capas, interfaces, persistencia, flujos, rendimiento |
| `03_REGLAS_Y_FORMULAS.md` | Dominio, combinatoria, probabilidades, importes, escrutinio |
| `04_CATALOGO_FILTROS.md` | Inventario experto de filtros, semánticas propuestas y dependencias |
| `05_REDUCCION_Y_GARANTIAS.md` | Definiciones de cobertura, reductores y verificación |
| `06_IA_RENTABILIDAD.md` | Datos/modelos, evaluación, estimación de premios y métricas |
| `07_FORMATOS_DATOS.md` | Esquemas, fuentes, import/export, SELAE/ASD/QR y seguridad |
| `08_PLAN_VERSIONES.md` | Sprints funcionales ordenados por dependencias |
| `09_PLAN_PRUEBAS.md` | Casos de prueba, invariantes, regresión y rendimiento |
| `10_UX_UI.md` | Navegación, experiencia y pantallas propuestas |
| `11_RIESGOS_PENDIENTES.md` | Ambigüedades, derechos, normas, decisiones pendientes |
| `12_MATRIZ_TRAZABILIDAD.md` | Cobertura de funciones e identificación de entrega |
| `13_GLOSARIO.md` | Terminología para usuarios principiantes y desarrolladores |
| `14_FIXTURES_REFERENCIA.md` | Casos sintéticos con resultados numéricos esperados para Codex |

## Regla de lectura

No cargues todos los documentos en cada interacción si no es necesario. Para una tarea de filtros, lee `03`, `04`, `09` y la matriz. Para reducción, lee `03`, `05`, `09`. Para datos externos, lee `07`, `11`. `AGENTS.md` es el mapa mínimo y el contrato de trabajo.

- [PC Studio Tkinter](PC_STUDIO_FASE1.md): entrega integrada desde GitHub;
  convive con la interfaz Qt durante la comprobación de paridad.

- [Fusión de escritorio v0.1.1](STUDIO_FUSION.md): datos, marcador, recuperación
  de sistemas, filtros básicos y límites de paridad.
