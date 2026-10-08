#!/bin/sh
set -eu
cd "$(dirname "$0")"
REPORT="${1:-/tmp/procedural-ops-facility-gui.json}"
xvfb-run -a ./facility --gui --auto-reference --no-sleep --seed 424242 --difficulty 0.45 --report "$REPORT"
python3 - "$REPORT" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
assert p["success"], p
assert p["state_hash"]
print("GUI_SMOKE_PASS", p["ticks"], p["state_hash"])
PY
