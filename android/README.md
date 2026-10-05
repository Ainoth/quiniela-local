# Quiniela Local para Android

Aplicación autónoma para Android 10 o posterior. No necesita un ordenador,
Python ni un servidor: descarga los datos directamente desde WIN1X2,
Quinielista y Dataradar.

## Compilar

Con Android SDK 33 instalado:

```bash
export ANDROID_HOME=/ruta/al/Android/Sdk
./gradlew assembleDebug
```

El APK se genera en `app/build/outputs/apk/debug/app-debug.apk`.

Para una versión de distribución firmada se indican `QUINIELA_KEYSTORE` y
`QUINIELA_KEY_PASSWORD` y se ejecuta `./gradlew assembleRelease`. La clave de
firma debe mantenerse fuera del repositorio y conservarse para futuras
actualizaciones.

## Instalar

1. Copiar el APK al teléfono.
2. Abrirlo desde “Mis archivos”.
3. Permitir temporalmente la instalación desde esa fuente si Android lo pide.
4. Instalar y abrir **Quiniela Local**.

La aplicación guarda los TXT en `Descargas/QuinielaLocal` y conserva los
pronósticos en el almacenamiento privado del teléfono.

## Actualización 1.1.0

El APK está firmado con la misma clave que 1.0.0: instalarlo encima de la
versión anterior, **sin desinstalar**, conserva el almacenamiento privado.
La migración mantiene las apuestas bajo la temporada/jornada que figuraba en
la versión anterior. Pulsar **Actualizar datos** para descargar también
calendarios, escrutinios e histórico; después usar **En curso**.

La cabecera persistente identifica temporada, jornada y modo (edición o
consulta). Las flechas recorren las jornadas con partidos publicados; el
selector permite consultar otras temporadas incluidas por WIN1X2. Las jornadas
anteriores y futuras no admiten cambios de signos, condiciones ni generación.
Sí se pueden importar TXT para comprobarlas. La jornada vigente se determina
con horarios reales y escrutinios, no solo por la fecha nominal de la jornada.

Cada desarrollo, base, Pleno, condiciones e importación está asociado a su
temporada/jornada. Los TXT cuyo nombre indica otra jornada se rechazan y se
solicita navegar a esa jornada. Un TXT genérico no contiene esa identificación:
el usuario debe elegir su jornada antes de importarlo.

## Funciones del escritorio trasladadas a Android

| Función visible en escritorio | Android |
| --- | --- |
| Base múltiple 1/X/2 y Pleno 0/1/2/M | Quiniela; selección por color, coste estimado |
| Cobertura progresiva 0–10 | Quiniela; 14 fijos en 0, 3 triples + 7 dobles en 10 |
| Ajustes rápidos 0–10 | Desarrollo; mismas fórmulas y redondeo que Python |
| Variantes, X, 2, seguidos e interrupciones | Desarrollo; límites editables |
| Distancia entre X y comparación de 14 signos | Desarrollo; separación y coincidencias |
| Generación, filtrado y reducción | Desarrollo; probabilidad + diversidad Hamming |
| Análisis del desarrollo | Base/filtradas/finales, coste, medias y masa de probabilidad |
| Columnas más probables (2–100) | Quiniela; con base seleccionada o todos los signos |
| Optimizar presupuesto | Solo columnas del desarrollo generado; conserva el origen |
| Sincronizar resultado con quiniela principal | Unión de signos y coste del desarrollo exacto |
| TXT, copiar y web de validación/pago | Exportación de 14 signos + dos goles del Pleno |
| Históricos de equipos | Pulsar el partido; últimos 40 disponibles por equipo |
| Directo manual/automático, desarrollo/TXT | Resultados; 60 s, validación de jornada/temporada |
| Aciertos actuales, confirmados, máximo y Pleno | Resultados; pendientes no se cuentan como X |
| Escrutinio y premios | Resultado definitivo descargado; sin premios provisionales |
| Listas completas de columnas y aciertos | Paginación de 100; exportación sin recortes |

Esta tabla compara las funciones **expuestas en la interfaz** del escritorio.
Los filtros experimentales del motor Python sin pantalla de configuración
(figuras, grupos, sumas y otros) no se anuncian como funciones disponibles.
La reducción por diversidad no es una reducción con garantía matemática.
El archivo histórico no cubre todos los equipos/competiciones: si no se puede
identificar un equipo con fiabilidad, se avisa en vez de asignarle otro historial.

El premio del Pleno al 15 se suma al de 14 aciertos, no lo sustituye; el total
incluye ambos conceptos, según los premios acumulados que explica
[SELAE](https://www.loteriasyapuestas.es/es/noticias/premios/la-quiniela-reparte-el-mayor-premio-de-esta-temporada-4-4-millones).

Los porcentajes se validan contra temporada, jornada y suma 100. Si el proveedor
no publica porcentajes válidos, se muestran guiones y se bloquean las operaciones
que requieren probabilidades; no se inventa un 40/30/30. Navegar a una jornada
no le asigna los porcentajes de otra. El paquete descargado queda en el móvil;
ni la consulta de los datos guardados ni los cálculos necesitan un servidor propio.

## Pruebas

Desde la raíz del repositorio, con Node 20 y Python 3:

```bash
python3 -m unittest discover -v
node --test android/tests/engine.test.cjs
```

El motor se contrasta con el Python del escritorio: 11 niveles, filtros,
reducción, cambio de jornada, estados de partidos y escrutinios. Para probar la
interfaz con Chromium, instalar Playwright en un entorno de pruebas:

```bash
npm install --prefix /tmp/quiniela-browser-tests playwright
/tmp/quiniela-browser-tests/node_modules/.bin/playwright install chromium
NODE_PATH=/tmp/quiniela-browser-tests/node_modules node android/tests/browser.test.cjs
```

Las pruebas de navegador simulan únicamente el puente nativo y los proveedores;
usan los recursos reales de la app. Cubren generación, presupuesto, exportación,
temporadas/jornadas aisladas, modo consulta, persistencia, aciertos, paginación,
ausencia de repintado con resultados idénticos y diseños a 360/384/412/800 px.
Opcionalmente, `WIN_ARCHIVE=/ruta/actudato.zip` activa una comprobación adicional
del ZIP real del proveedor y consulta los porcentajes de la jornada 11 de
2026-27 (fixture temporal de esta versión). También comprueba navegación,
generación e histórico con esos datos. El lector PRE respeta el campo fijo de
dos caracteres de jornada, incluso cuando está pegado al primer número de
acertantes; hay una regresión específica para los premios de esas filas.
La compilación Android se valida con `./gradlew lintRelease assembleRelease`
y la firma con `apksigner verify`. No sustituyen la comprobación en un S20+ físico.
