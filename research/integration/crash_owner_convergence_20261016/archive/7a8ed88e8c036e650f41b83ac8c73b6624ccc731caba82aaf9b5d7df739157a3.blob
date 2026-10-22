#!/bin/bash
set -euo pipefail
mount --make-rprivate /
mount -t tmpfs -o size=64m tmpfs /tmp
chmod 1777 /tmp
mkdir -m 1777 /tmp/.X11-unix
cd /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-5/work/v15-owner-integration-20261012
export PYTHONPATH=research/live_control
export V15_OWNER_OUT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-5/work/v15-owner-integration-20261012/research/doom/v39_v15_xvfb_shared_key_source_a33_20261012/results/A01
python3 -B research/doom/v39_v15_xvfb_shared_key_source_a33_20261012/candidate.py
