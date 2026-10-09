#!/usr/bin/env bash
set -euo pipefail
STUDIO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$STUDIO_DIR"
if [[ ! -x .venv-studio/bin/python ]]; then
  python3 -m venv .venv-studio
  .venv-studio/bin/python -m pip install -e '.[test]'
fi
if command -v apt-get >/dev/null && [[ "${QT_QPA_PLATFORM:-}" != "offscreen" ]]; then
  bash scripts/prepare_linux_qt.sh
fi
exec .venv-studio/bin/python -m quiniela_studio "$@"
