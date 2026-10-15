#!/usr/bin/env bash
set -eu
OUT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-6/outputs/x11-xtest-device-cross-client-a01
BASE=/home/user/x11-xtest-device-cross-client-a01-20261005
INPUT="$OUT/inputs"
mkdir -p "$BASE/deps" "$BASE/overlay/upper" "$BASE/overlay/work" "$BASE/setup/a05" "$BASE/results"
for pkg in "$INPUT"/*.deb; do dpkg-deb -x "$pkg" "$BASE/deps"; done
cp "$BASE/deps/usr/bin/xkbcomp" "$BASE/overlay/upper/xkbcomp"
chmod 755 "$BASE/overlay/upper/xkbcomp"
# No packages are installed. Xvfb starts only inside a private mount namespace.
unshare --user --map-root-user --mount --propagation private bash -s -- "$BASE" <<'NS'
set -eu
BASE=$1
mount --make-rprivate /
mount -t tmpfs -o mode=1777 tmpfs /tmp/.X11-unix
mount -t overlay overlay -o "lowerdir=/usr/bin,upperdir=$BASE/overlay/upper,workdir=$BASE/overlay/work" /usr/bin
stat -c '%a %U %G %n' /tmp/.X11-unix > "$BASE/setup/a05/private-socket-dir.txt"
LD_LIBRARY_PATH="$BASE/deps/usr/lib/x86_64-linux-gnu:$BASE/deps/lib/x86_64-linux-gnu" "$BASE/deps/usr/bin/Xvfb" :87 -screen 0 640x480x24 -nolisten tcp -ac -fp built-ins > "$BASE/setup/a05/Xvfb.log" 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT
ready=0
for n in $(seq 1 50); do
  if [ -S /tmp/.X11-unix/X87 ]; then
    if DISPLAY=:87 python3 -c 'import ctypes,sys; x=ctypes.CDLL("libX11.so.6"); x.XOpenDisplay.restype=ctypes.c_void_p; x.XOpenDisplay.argtypes=[ctypes.c_char_p]; d=x.XOpenDisplay(None); print("XOpenDisplay",bool(d)); sys.exit(0 if d else 1)' >> "$BASE/setup/a05/connectivity.txt" 2>&1; then ready=1; break; fi
  fi
  sleep 0.1
done
[ "$ready" = 1 ] || { cat "$BASE/setup/a05/Xvfb.log"; exit 21; }
kill "$pid"; wait "$pid" || true
trap - EXIT
printf 'setup=PASS_NO_INPUT\nserver_pid=%s\n' "$pid" > "$BASE/setup/a05/result.txt"
NS
# The shared distro socket directory must remain unmodified after namespace exit.
stat -c '%a %U %G %n' /tmp/.X11-unix > "$BASE/setup/a05/shared-socket-dir-after.txt"
printf 'candidate_runs=0\ninput_events=0\npackage_install=0\n' > "$BASE/setup/a05/receipt.txt"
cat "$BASE/setup/a05/result.txt" "$BASE/setup/a05/connectivity.txt" "$BASE/setup/a05/private-socket-dir.txt" "$BASE/setup/a05/shared-socket-dir-after.txt" "$BASE/setup/a05/receipt.txt"




