#!/bin/sh
set -eu
mode=${1:?normal|optimized}
case "$mode" in normal|optimized) ;; *) exit 2 ;; esac
evidence=/evidence/runs/$mode
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace DISPLAY=:88
export AGENT_INTERFACE_MCP_XVFB_TEST=1
export AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT="$evidence/result.json"
Xvfb :88 -screen 0 1024x768x24 -ac >"$evidence/xvfb-server.log" 2>&1 &
export AGENT_INTERFACE_XVFB_PID=$!
cleanup() { if kill -0 "$AGENT_INTERFACE_XVFB_PID" 2>/dev/null; then kill -TERM "$AGENT_INTERFACE_XVFB_PID" 2>/dev/null || true; fi; wait "$AGENT_INTERFACE_XVFB_PID" 2>/dev/null || true; }
trap cleanup EXIT HUP INT TERM
sleep 0.5
python3 - <<'PY' >"$evidence/keyboard-control.json"
import json
from Xlib import display, X, XK
connection = display.Display()
keycode = connection.keysym_to_keycode(XK.string_to_keysym('a'))
connection.change_keyboard_control(key=keycode,
                                   auto_repeat_mode=X.AutoRepeatModeOff)
connection.sync()
control = connection.get_keyboard_control()
mask = 1 << (keycode & 7)
repeat_enabled = bool(control.auto_repeats[keycode >> 3] & mask)
row = {"global_auto_repeat": int(control.global_auto_repeat),
       "keysym": "a", "keycode": int(keycode),
       "per_key_repeat_enabled": repeat_enabled}
print(json.dumps(row))
if control.global_auto_repeat != X.AutoRepeatModeOn or repeat_enabled:
    raise SystemExit('per-key autorepeat precondition failed')
connection.close()
PY
cd /workspace
test_name=runtime.cli_v1.test_mcp_xvfb_blocked_release_integration.StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb
if [ "$mode" = optimized ]; then
  if python3 -O -m unittest -v "$test_name" >"$evidence/test.log" 2>&1; then rc=0; else rc=$?; fi
else
  if python3 -m unittest -v "$test_name" >"$evidence/test.log" 2>&1; then rc=0; else rc=$?; fi
fi
printf '%s\n' "$rc" >"$evidence/exit-code.txt"
cat "$evidence/test.log"
exit "$rc"