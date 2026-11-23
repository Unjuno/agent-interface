#!/bin/sh
set -eu
mode=${1:?normal|optimized}; condition=${2:?baseline|global_off|key_off}
case "$mode" in normal|optimized) ;; *) exit 2 ;; esac
case "$condition" in baseline|global_off|key_off) ;; *) exit 2 ;; esac
evidence=/evidence/runs/$mode/$condition
export DISPLAY=:88
Xvfb :88 -screen 0 1024x768x24 -ac >"$evidence/xvfb-server.log" 2>&1 &
pid=$!
cleanup() { if kill -0 "$pid" 2>/dev/null; then kill -TERM "$pid" 2>/dev/null || true; fi; wait "$pid" 2>/dev/null || true; }
trap cleanup EXIT HUP INT TERM
sleep 0.5
cd /workspace
if [ "$mode" = optimized ]; then python3 -O /evidence/probe_control.py "$condition" >"$evidence/result.json"; else python3 /evidence/probe_control.py "$condition" >"$evidence/result.json"; fi
cat "$evidence/result.json"