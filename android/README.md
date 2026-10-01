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

## Instalar

1. Copiar el APK al teléfono.
2. Abrirlo desde “Mis archivos”.
3. Permitir temporalmente la instalación desde esa fuente si Android lo pide.
4. Instalar y abrir **Quiniela Local**.

La aplicación guarda los TXT en `Descargas/QuinielaLocal` y conserva los
pronósticos en el almacenamiento privado del teléfono.
