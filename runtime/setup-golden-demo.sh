#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="$root/runtime/.venv"
install_dependencies() {
  if [[ -e "$venv" ]]; then
    printf '%s\n' 'runtime/.venv already exists; inspect or remove it explicitly before setup.' >&2
    return 2
  fi
  python3 -m venv "$venv"
  "$venv/bin/python" -m pip install --disable-pip-version-check -r "$root/runtime/requirements-golden.txt"
}
if [[ "${1:-}" == "--install-dependencies" && $# -eq 1 ]]; then
  install_dependencies
else
  printf '%s\n' 'This setup downloads pinned Python dependencies for the checked-out runtime source.' 'To authorize, pass --install-dependencies.' 'It does not download runtime source, a model, Chrome, Codex, or a Docker image.' >&2
  exit 2
fi
exec "$venv/bin/python" "$root/runtime/golden_desktop_demo.py" doctor
