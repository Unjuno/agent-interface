#!/usr/bin/env bash
set -u
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
RAW="$SCRIPT_DIR/raw/r01"
DISPLAY_NAME=:177
mkdir -p "$RAW"
if [[ -e /tmp/.X177-lock || -S /tmp/.X11-unix/X177 ]]; then
  printf 'DISPLAY_177_OCCUPIED\n' > "$RAW/preflight.txt"
  exit 20
fi
export DISPLAY="$DISPLAY_NAME"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"
Xvfb "$DISPLAY_NAME" -screen 0 800x600x24 -nolisten tcp -ac > "$RAW/xvfb.log" 2>&1 &
XVFB_PID=$!
printf '%s\n' "$XVFB_PID" > "$RAW/xvfb.pid"
cleanup() {
  if kill -0 "$XVFB_PID" 2>/dev/null; then
    kill "$XVFB_PID" 2>/dev/null || true
    wait "$XVFB_PID" 2>/dev/null || true
  fi
  if kill -0 "$XVFB_PID" 2>/dev/null; then
    printf 'xvfb_alive_after_cleanup=true\n' >> "$RAW/preflight.txt"
  else
    printf 'xvfb_alive_after_cleanup=false\n' >> "$RAW/preflight.txt"
  fi
}
trap cleanup EXIT
READY=0
for _ in $(seq 1 100); do
  if python3 -c 'from Xlib import display; d=display.Display(); d.close()' >/dev/null 2>&1; then
    READY=1
    break
  fi
  if ! kill -0 "$XVFB_PID" 2>/dev/null; then
    break
  fi
  sleep 0.05
done
if [[ "$READY" != 1 ]]; then
  printf 'xvfb_ready=false\npid=%s\n' "$XVFB_PID" > "$RAW/preflight.txt"
  exit 21
fi
printf 'xvfb_ready=true\npid=%s\nexe=%s\ncmdline=' "$XVFB_PID" "$(readlink "/proc/$XVFB_PID/exe")" > "$RAW/preflight.txt"
tr '\0' ' ' < "/proc/$XVFB_PID/cmdline" >> "$RAW/preflight.txt"
printf '\npackage=' >> "$RAW/preflight.txt"
dpkg-query -W -f='${Version}' xvfb >> "$RAW/preflight.txt" 2>&1
printf '\npython=' >> "$RAW/preflight.txt"
python3 --version >> "$RAW/preflight.txt" 2>&1
printf 'python_xlib=' >> "$RAW/preflight.txt"
python3 -c 'from importlib.metadata import version; print(version("python-xlib"))' >> "$RAW/preflight.txt" 2>&1
set +e
python3 "$SCRIPT_DIR/run_live_xres_bystander_r01.py" > "$RAW/runner.stdout.txt" 2> "$RAW/runner.stderr.txt"
STATUS=$?
set -e
printf '%s\n' "$STATUS" > "$RAW/runner.exit"
exit "$STATUS"
