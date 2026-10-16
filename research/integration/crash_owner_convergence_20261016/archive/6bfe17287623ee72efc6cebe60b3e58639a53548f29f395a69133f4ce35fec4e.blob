#!/bin/bash
set -euo pipefail
mount --make-rprivate /
mount -t tmpfs -o size=64m tmpfs /tmp
chmod 1777 /tmp
mkdir -m 1777 /tmp/.X11-unix
stat -c '%a %U:%G %n' /tmp/.X11-unix
Xvfb -displayfd 1 -screen 0 320x240x24 -nolisten tcp -ac >/tmp/a28-preflight.out 2>/tmp/a28-preflight.err &
xp=$!
for i in $(seq 1 100); do
  if [ -s /tmp/a28-preflight.out ]; then break; fi
  if ! kill -0 "$xp" 2>/dev/null; then cat /tmp/a28-preflight.err; exit 1; fi
  sleep .02
done
test -s /tmp/a28-preflight.out
cat /tmp/a28-preflight.out
kill -TERM "$xp"
rc=0
wait "$xp" || rc=$?
echo "xvfb_exit=$rc"
