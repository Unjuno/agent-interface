#!/bin/bash
set -eu
Xvfb :99 -screen 0 1024x768x24 -nolisten tcp -ac >/tmp/xvfb.log 2>&1 &
xvfb_pid=$!
trap 'kill "$xvfb_pid" 2>/dev/null || true' EXIT
export DISPLAY=:99
ready=0
for i in $(seq 1 120); do
  if xdpyinfo -display :99 >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.25
done
if [ "$ready" -ne 1 ]; then
  cat /tmp/xvfb.log
  exit 42
fi
openbox >/tmp/openbox.log 2>&1 &
printf '%s\n' 'X_DISPLAY_READY'
printf '%s\n' '{"op":"finish"}' | /usr/bin/python3 \
  /repo/research/live_control/session_v4.py \
  --app chromium --seed 992924 --out /evidence/ready-gate-03 \
  --chromium /usr/bin/chromium
