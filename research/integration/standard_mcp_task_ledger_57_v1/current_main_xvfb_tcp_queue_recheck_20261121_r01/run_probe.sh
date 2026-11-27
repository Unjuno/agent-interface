#!/bin/sh
set -eu

mode=${1:-}
case "$mode" in
  normal) python_mode=normal ;;
  optimized) python_mode=optimized ;;
  *) echo "usage: $0 normal|optimized" >&2; exit 2 ;;
esac

packet=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(CDPATH= cd -- "$packet/../../../.." && pwd)
cd "$repo"
run="$packet/runs/$mode"
if [ -e "$run" ]; then
  echo "refusing to overwrite frozen run: $run" >&2
  exit 2
fi
mkdir -p "$run"
temp=$(mktemp -d "/tmp/issue57-xvfb-tcp-88-$mode.XXXXXX")
authority="$temp/Xauthority"
cookie=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
xauth -f "$authority" add 127.0.0.1:88 MIT-MAGIC-COOKIE-1 "$cookie"

if [ -e /tmp/.X88-lock ] || [ -S /tmp/.X11-unix/X88 ]; then
  echo "display :88 is already occupied" >&2
  exit 2
fi

Xvfb :88 -nolisten unix -listen tcp -screen 0 1024x768x24 \
  -auth "$authority" -noreset >"$run/xvfb-server.log" 2>&1 &
xvfb_pid=$!
cleanup() {
  if kill -0 "$xvfb_pid" 2>/dev/null; then
    kill -TERM "$xvfb_pid" 2>/dev/null || true
  fi
  wait "$xvfb_pid" 2>/dev/null || true
  rm -f "$authority"
  rmdir "$temp" 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM
sleep 1

export DISPLAY=127.0.0.1:88
export XAUTHORITY="$authority"
export AGENT_INTERFACE_XORG_FENCE_TEST=1
export AGENT_INTERFACE_XORG_HELD_KEY_QUEUE_RESULT="$run/result.json"
test_name=runtime.guarded_x11_v1.test_xres_disconnect_fence_integration.XResHeldKeyDisconnectIntegrationTests.test_later_delayed_keypress_after_disconnect_and_independent_release
if [ "$python_mode" = optimized ]; then
  if python3 -O -m unittest -v "$test_name" >"$run/test.log" 2>&1; then rc=0; else rc=$?; fi
else
  if python3 -m unittest -v "$test_name" >"$run/test.log" 2>&1; then rc=0; else rc=$?; fi
fi
printf '%s\n' "$rc" > "$run/exit-code.txt"
cat "$run/test.log"
exit "$rc"
