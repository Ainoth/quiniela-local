# SSeguidos · v1.0.19

## Objetivo y trazabilidad

RF-UX-015 / RF-FIL-021: alinear Reducciones → SSeguidos con
`ESPECIFICACION_QT_SELECCION_SIGNOS_SEGUIDOS_v1_0.md`: tres métodos que editan
una misma configuración, rachas máximas, matriz de frecuencias exactas y
figuras como particiones de rachas máximas.

## Trabajo

- [x] Leer la especificación y conservar el filtro/tab serializado Racha.
- [x] Presentar Manual, Azar y Automática en paneles Qt compactos con cuadrados
  accesibles blanco/verde y temporadas reales en una cuadrícula compacta.
- [x] Añadir al dominio límites mínimo/máximo opcionales, cantidades permitidas
  de rachas exactas por longitud y figuras exactas por total.
- [x] Enumerar de forma determinista las frecuencias y figuras alcanzables desde
  la base actual; reflejar los conteos históricos reales disponibles.
- [x] Generar propuestas Azar reproducibles desde la base y Automática desde
  resultados finales históricos conjuntos; etiquetar su procedencia y riesgo.
- [x] Preservar sistemas antiguos, valores al desactivar condiciones y demás
  pestañas; inicializar SSeguidos sin afectar Cuenta/Racha/Grupo.
- [x] Verificar reglas matemáticas, persistencia, modos Qt y filtrado efectivo.

## Criterios de aceptación

- Una racha es máxima y no solapada; V agrupa X/2 y excluye el Pleno 15.
- Una casilla `(longitud=k, veces=n)` permite exactamente n rachas máximas de
  longitud k; los valores seleccionados pueden ser discontinuos.
- `min_run` y `max_run` distinguen vacío de cero. Las tres páginas comparten el
  mismo estado, el filtro es único y solo se usa al activar SSeguidos.
- Cambiar la base nunca elimina en silencio selecciones incompatibles.
- Cuenta conserva sus tres métodos y el histórico continúa cargándose desde los
  datos integrados, sin exigir importación desde SSeguidos.
