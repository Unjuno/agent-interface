#!/bin/bash
set -eu
exec > >(tee -a setup.log) 2>&1
printf 'setup_start=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
uname -a
cat /etc/os-release
sudo apt-get update
sudo apt-get install -y xvfb python3-xlib
python3 --version
Xvfb -version 2>&1 | head -1 || true
printf 'setup_complete=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
