#!/usr/bin/env bash
# Dependencia de X11 de Qt, local al entorno virtual; sin sudo ni cambios de sistema.
set -euo pipefail
STUDIO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
STUDIO_PYTHON="$STUDIO_DIR/.venv-studio/bin/python"
if "$STUDIO_PYTHON" -c 'import ctypes; ctypes.CDLL("libxcb-cursor.so.0")' 2>/dev/null; then exit 0; fi
STUDIO_RUNTIME="$STUDIO_DIR/.venv-studio/qt-runtime"
if [[ -f "$STUDIO_RUNTIME/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH)/libxcb-cursor.so.0" ]]; then exit 0; fi
mkdir -p "$STUDIO_RUNTIME/downloads"
cd "$STUDIO_RUNTIME/downloads"
apt-get download libxcb-cursor0
for STUDIO_DEB in libxcb-cursor0_*.deb; do dpkg-deb -x "$STUDIO_DEB" "$STUDIO_RUNTIME"; done
