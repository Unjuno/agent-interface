#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
mkdir -p results
for path in results/A02 results/xvfb.log results/xvfb.exit \
  results/candidate.stdout results/candidate.stderr results/candidate.exit; do
  if [ -e "$path" ]; then
    printf 'STOP: result path already exists: %s\n' "$path" >&2
    exit 21
  fi
done
if [ -e /tmp/.X11-unix/X98 ]; then
  printf '%s\n' 'STOP: display socket :98 already exists' >&2
  exit 22
fi
Xvfb :98 -screen 0 640x480x24 -nolisten tcp -ac >results/xvfb.log 2>&1 &
xvfb_pid=$!
ready=0
for _ in $(seq 1 50); do
  if [ -S /tmp/.X11-unix/X99 ]; then ready=1; break; fi
  if ! kill -0 "$xvfb_pid" 2>/dev/null; then break; fi
  sleep 0.1
done
if [ "$ready" -ne 1 ]; then
  kill -TERM "$xvfb_pid" 2>/dev/null || true
  wait "$xvfb_pid"
  printf '%s\n' "$?" >results/xvfb.exit
  printf '%s\n' 'STOP: private Xvfb did not become ready within 5 seconds' >&2
  exit 20
fi
PYTHONPATH=experimental_source DISPLAY=:98 \
  python3 candidate.py --display :98 --out results/A02 \
  >results/candidate.stdout 2>results/candidate.stderr
candidate_rc=$?
printf '%s\n' "$candidate_rc" >results/candidate.exit
kill -TERM "$xvfb_pid" 2>/dev/null || true
wait "$xvfb_pid"
xvfb_rc=$?
printf '%s\n' "$xvfb_rc" >results/xvfb.exit
exit "$candidate_rc"
