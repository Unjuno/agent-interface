#!/bin/sh
set -eu
export DISPLAY=:0
: "${ARENA_AUTOCLOSE:=30}"
xauth -f /tmp/Xauthority add :0 MIT-MAGIC-COOKIE-1 "$X11_COOKIE"
export XAUTHORITY=/tmp/Xauthority
Xvfb :0 -auth /tmp/Xauthority -screen 0 800x600x24 -listen tcp -nolisten unix >/tmp/xvfb.log 2>&1 &
for i in $(seq 1 50); do
  if xdpyinfo -display :0 >/dev/null 2>&1; then break; fi
  sleep 0.1
done
xdpyinfo -display :0 >/dev/null
printf 'evaluator_seed_argv=%s\n' "$ARENA_SEED" >&2
exec python /opt/arena/arena.py --seed "$ARENA_SEED" --difficulty 1.0 --clock fixed --report /evidence/report.json --autoclose "$ARENA_AUTOCLOSE"
