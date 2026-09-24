#!/usr/bin/env bash

set -u

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${WIN1X2_DATA_DIR:-$(dirname -- "$APP_DIR")/Datosg}"

if command -v git >/dev/null 2>&1 && git -C "$APP_DIR" remote get-url origin >/dev/null 2>&1; then
    git -C "$APP_DIR" pull --ff-only --quiet || true
fi

export WIN1X2_DATA_DIR="$DATA_DIR"
exec python3 "$APP_DIR/app.py"
