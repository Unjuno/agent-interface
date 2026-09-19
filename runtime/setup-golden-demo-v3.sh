#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$root/runtime/.venv"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install --disable-pip-version-check \
  -r "$root/runtime/requirements-golden.txt"
exec "$venv/bin/python" "$root/runtime/golden_desktop_demo_v3.py" doctor
