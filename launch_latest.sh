#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Refresh this checkout before each launch so the desktop shortcut follows main.
if command -v git >/dev/null 2>&1; then
    if ! GIT_TERMINAL_PROMPT=0 timeout 20s git -C "$APP_DIR" pull --ff-only --quiet origin main; then
        if command -v notify-send >/dev/null 2>&1; then
            notify-send "Quiniela AI Studio" "No se pudo actualizar desde GitHub; abriré la última versión local." || true
        fi
    fi
fi

exec "$APP_DIR/run_studio.sh" "$@"
