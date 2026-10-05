#!/usr/bin/env bash
set -eu
OUT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-6/outputs/x11-xtest-device-cross-client-a01
BASE=/home/user/x11-xtest-device-cross-client-a01-20261005
mkdir -p "$BASE/results/a01"
if [ -e "$BASE/results/a01/invocation.marker" ]; then echo 'formal run path already invoked' >&2; exit 90; fi
: > "$BASE/results/a01/invocation.marker"
set +e
unshare --user --map-root-user --mount --propagation private bash -s -- "$BASE" "$OUT" <<'NS'
set -eu
BASE=$1
OUT=$2
mount --make-rprivate /
mount -t tmpfs -o mode=1777 tmpfs /tmp/.X11-unix
mount -t overlay overlay -o "lowerdir=/usr/bin,upperdir=$BASE/overlay/upper,workdir=$BASE/overlay/work" /usr/bin
stat -c '%a %U %G %n' /tmp/.X11-unix > "$BASE/results/a01/private-socket-dir.txt"
export LD_LIBRARY_PATH="$BASE/deps/usr/lib/x86_64-linux-gnu:$BASE/deps/lib/x86_64-linux-gnu"
export DISPLAY=:87
"$BASE/deps/usr/bin/Xvfb" :87 -screen 0 640x480x24 -nolisten tcp -ac -fp built-ins > "$BASE/results/a01/Xvfb.log" 2>&1 &
pid=$!
cleanup() { kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; }
trap cleanup EXIT
ready=0
for n in $(seq 1 50); do
  if [ -S /tmp/.X11-unix/X87 ] && python3 -c 'import ctypes,sys; x=ctypes.CDLL("libX11.so.6"); x.XOpenDisplay.restype=ctypes.c_void_p; x.XOpenDisplay.argtypes=[ctypes.c_char_p]; d=x.XOpenDisplay(None); print("XOpenDisplay",bool(d)); sys.exit(0 if d else 1)' > "$BASE/results/a01/preflight.txt" 2>&1; then ready=1; break; fi
  sleep 0.1
done
[ "$ready" = 1 ] || { printf 'candidate_runs=0\nrun_status=STOP_XVFB_PREFLIGHT\n' > "$BASE/results/a01/wrapper_exit.txt"; cat "$BASE/results/a01/Xvfb.log" >&2; exit 21; }
set +e
python3 -B "$OUT/candidate.py" --out "$BASE/results/a01/raw.json" > "$BASE/results/a01/candidate.stdout.txt" 2> "$BASE/results/a01/candidate.stderr.txt"
rc=$?
set -e
printf 'candidate_runs=1\ncandidate_exit=%s\n' "$rc" > "$BASE/results/a01/wrapper_exit.txt"
exit "$rc"
NS
rc=$?
set -e
printf 'run_wrapper_exit=%s\n' "$rc" > "$BASE/results/a01/run_wrapper_exit.txt"
# Preserve the private-namespace output even when the candidate exits nonzero.
cp -a "$BASE/results/a01/." "$OUT/results/a01/"
stat -c '%a %U %G %n' /tmp/.X11-unix > "$OUT/results/a01/shared-socket-dir-after.txt"
find /tmp/.X11-unix -maxdepth 1 -mindepth 1 -printf '%f\n' | sort > "$OUT/results/a01/shared-socket-entries-after.txt"
exit "$rc"
