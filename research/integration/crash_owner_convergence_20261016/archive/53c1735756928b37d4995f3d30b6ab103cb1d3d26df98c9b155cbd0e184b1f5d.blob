#!/bin/bash
set -euo pipefail
mount --make-rprivate /
mount -t tmpfs -o size=64m tmpfs /tmp
chmod 1777 /tmp
mkdir -m 1777 /tmp/.X11-unix
auth=$(mktemp)
python3 - "$auth" <<'PY'
import secrets, subprocess, sys
subprocess.run(['xauth','-f',sys.argv[1],'add',':77','MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],check=True)
PY
export XAUTHORITY="$auth"
Xvfb :77 -screen 0 320x240x24 -nolisten tcp -auth "$auth" >/tmp/a31-xvfb.out 2>/tmp/a31-xvfb.err &
xp=$!
cleanup(){ kill -TERM "$xp" 2>/dev/null || true; wait "$xp" 2>/dev/null || true; rm -f "$auth"; }
trap cleanup EXIT
for i in $(seq 1 100); do
  if DISPLAY=:77 python3 -c 'from Xlib.display import Display; d=Display(); print("connected", flush=True); d.close()' >/tmp/a31-connect.out 2>/tmp/a31-connect.err; then break; fi
  if ! kill -0 "$xp" 2>/dev/null; then cat /tmp/a31-xvfb.err; exit 1; fi
  sleep .02
done
cat /tmp/a31-connect.out
cat /tmp/a31-connect.err
