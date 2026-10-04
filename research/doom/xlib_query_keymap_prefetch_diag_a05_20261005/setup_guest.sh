#!/bin/bash
set -euo pipefail
printf 'setup_start=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
id
if [ "$(id -u)" -ne 0 ]; then
  echo 'STOP: setup must run as root' >&2
  exit 91
fi
printf 'setup_uid=%s\n' "$(id -u)"
cat /etc/os-release
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y xvfb=2:21.1.12-1ubuntu1.8 python3-xlib=0.33-2
python3 --version
dpkg-query -W -f='${Package}=${Version}\n' xvfb python3-xlib
python3 - <<'PY'
from Xlib import display
print('python-xlib=' + display.__file__)
PY
printf 'setup_complete=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
