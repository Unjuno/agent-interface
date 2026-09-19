#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python="$root/runtime/.venv/bin/python"
if [[ ! -x "$python" ]]; then
  python="$(command -v python3)"
fi
if [[ $# -eq 0 ]]; then
  set -- run
fi
exec "$python" "$root/runtime/golden_desktop_demo_v2.py" "$@"
