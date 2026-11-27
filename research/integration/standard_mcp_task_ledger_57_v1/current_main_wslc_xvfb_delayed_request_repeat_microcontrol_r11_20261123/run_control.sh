#!/bin/sh
set -eu
evidence=/evidence/runs/key-off
export DISPLAY=:88
Xvfb :88 -screen 0 1024x768x24 -ac >"$evidence/xvfb-server.log" 2>&1 &
pid=$!
cleanup() { if kill -0 "$pid" 2>/dev/null; then kill -TERM "$pid" 2>/dev/null || true; fi; wait "$pid" 2>/dev/null || true; }
trap cleanup EXIT HUP INT TERM
sleep 0.5
python3 /evidence/probe_delayed.py >"$evidence/result.json"
cat "$evidence/result.json"