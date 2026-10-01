#!/bin/sh
set -eu

# Called as root inside an unshared mount namespace. Hide WSLg's read-only X11
# socket mount with a disposable private socket directory, then drop privileges.
mount -t tmpfs -o size=1M,mode=1777 tmpfs /tmp/.X11-unix
exec setpriv --reuid=1000 --regid=1000 --clear-groups \
  python3 -B "$(dirname "$0")/study.py" "$@"
