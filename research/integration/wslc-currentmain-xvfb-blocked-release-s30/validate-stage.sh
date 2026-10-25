#!/usr/bin/env bash
set -euo pipefail
asset="$1"
stage="$asset/stage"
deps="$asset/deps"
repo="$asset/repo"
xkb="$asset/xkb"
env PYTHONHOME="$stage" LD_LIBRARY_PATH="$stage/lib" PYTHONPATH="$deps:$repo" PYTHONDONTWRITEBYTECODE=1 "$stage/bin/python3.12" -B - <<'PY'
import importlib.metadata as m, sys
import mcp, PIL, Xlib
import runtime.cli_v1.test_mcp_xvfb_blocked_release_integration
print("python", sys.version.split()[0])
print("mcp", m.version("mcp"))
print("Pillow", PIL.__version__)
print("Xlib", Xlib.__file__)
print("runner_imports=pass")
PY