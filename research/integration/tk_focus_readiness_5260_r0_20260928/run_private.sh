#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DISPLAY=:196
export DISPLAY
Xvfb "$DISPLAY" -screen 0 1024x768x24 -nolisten tcp >"$HERE/xvfb.log" 2>&1 &
XVFB_PID=$!
WM_PID=
cleanup() {
  if [ -n "$WM_PID" ]; then kill "$WM_PID" 2>/dev/null || true; wait "$WM_PID" 2>/dev/null || true; fi
  kill "$XVFB_PID" 2>/dev/null || true
  wait "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM
i=0
until xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; do
  i=$((i + 1))
  [ "$i" -lt 50 ] || { echo 'STOP: private Xvfb failed to become ready' >&2; exit 20; }
  sleep 0.1
done
setxkbmap -display "$DISPLAY" -layout us
LAYOUT=$(setxkbmap -display "$DISPLAY" -query | awk '$1 == "layout:" {print $2}')
[ "$LAYOUT" = us ] || { echo 'STOP: XKB layout mismatch' >&2; exit 21; }
openbox --sm-disable >"$HERE/openbox.log" 2>&1 &
WM_PID=$!
i=0
until xset -display "$DISPLAY" q >/dev/null 2>&1; do
  i=$((i + 1))
  [ "$i" -lt 50 ] || { echo 'STOP: window manager/display unavailable' >&2; exit 22; }
  sleep 0.1
done
python3 "$HERE/study.py" "$HERE/raw.json"
python3 "$HERE/study.py" --audit "$HERE/raw.json" "$HERE/audit.json"
