#!/bin/sh
set -eu
src=$(cd "$1" && pwd)
out=$(cd "$2" && pwd)
script=$3
case "$script" in construction.py|formal.py|audit.py) ;; *) exit 2;; esac
exec bwrap --unshare-all --die-with-parent --new-session \
  --ro-bind /usr /usr --symlink usr/lib /lib --symlink usr/lib /lib64 \
  --symlink usr/bin /bin --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$src" /src --bind "$out" /out --chdir /src \
  --clearenv --setenv PATH /usr/bin --setenv PYTHONDONTWRITEBYTECODE 1 \
  /usr/bin/python3 -B "/src/$script"
