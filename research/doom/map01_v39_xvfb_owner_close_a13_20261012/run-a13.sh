#!/bin/bash
set -eu
ip link set lo up
ln -s /mnt/d/codex-research/v39-xvfb-a09-env-20261012/root/usr/bin/xkbcomp /usr/bin/xkbcomp
trap 'rm -f /usr/bin/xkbcomp' EXIT
su -s /bin/bash user -c 'env PATH=/mnt/d/codex-research/v39-xvfb-a09-env-20261012/root/usr/bin:/usr/bin:/bin LD_LIBRARY_PATH=/mnt/d/codex-research/v39-xvfb-a09-env-20261012/root/usr/lib/x86_64-linux-gnu PYTHONPATH=/mnt/d/codex-research/v39-xvfb-a09-env-20261012/root/usr/lib/python3/dist-packages /usr/bin/python3 /mnt/d/codex-research/agent-interface-win-appserver-launch-a01/research/doom/map01_v39_xvfb_owner_close_a13_20261012/SOURCE/candidate.py --out /mnt/d/codex-research/agent-interface-win-appserver-launch-a01/research/doom/map01_v39_xvfb_owner_close_a13_20261012/results/A13 --display 127.0.0.1:136'
