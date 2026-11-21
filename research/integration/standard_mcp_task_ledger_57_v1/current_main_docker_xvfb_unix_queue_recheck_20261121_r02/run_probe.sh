#!/bin/sh
set -eu
mode=${1:?normal or optimized}
case "$mode" in normal|optimized) ;; *) exit 2 ;; esac
packet=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(CDPATH= cd -- "$packet/source" && pwd)
run="$packet/runs/$mode"
mkdir "$run"
export PYTHONDONTWRITEBYTECODE=1
export DISPLAY=:88
export AGENT_INTERFACE_XORG_FENCE_TEST=1
export AGENT_INTERFACE_XORG_HELD_KEY_QUEUE_RESULT="$run/result.json"
Xvfb :88 -nolisten tcp -screen 0 1024x768x24 -noreset >"$run/xvfb-server.log" 2>&1 &
xvfb_pid=$!
cleanup() {
  if kill -0 "$xvfb_pid" 2>/dev/null; then kill -TERM "$xvfb_pid" 2>/dev/null || true; fi
  wait "$xvfb_pid" 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM
sleep 1
cd "$repo"
test_name=runtime.guarded_x11_v1.test_xres_disconnect_fence_integration.XResHeldKeyDisconnectIntegrationTests.test_later_delayed_keypress_after_disconnect_and_independent_release
if [ "$mode" = optimized ]; then
  if python3 -O -m unittest -v "$test_name" >"$run/test.log" 2>&1; then rc=0; else rc=$?; fi
else
  if python3 -m unittest -v "$test_name" >"$run/test.log" 2>&1; then rc=0; else rc=$?; fi
fi
printf '%s\n' "$rc" >"$run/exit-code.txt"
cat "$run/test.log"
exit "$rc"
