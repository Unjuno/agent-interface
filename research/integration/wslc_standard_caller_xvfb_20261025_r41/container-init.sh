#!/bin/bash
set -euo pipefail
mkdir -p /tmp/stage
cp -a /stage/. /tmp/stage/
chmod +x /tmp/stage/bin/Xvfb /tmp/stage/bin/python3.12 /tmp/stage/bin/xauth /tmp/stage/bin/xkbcomp
cp /tmp/stage/bin/xkbcomp /usr/bin/xkbcomp
exec env PYTHONHOME=/tmp/stage LD_LIBRARY_PATH=/tmp/stage/lib PYTHONDONTWRITEBYTECODE=1 /tmp/stage/bin/python3.12 -B /repo/research/integration/wslc_standard_caller_xvfb_20261025_r41/run-container.py