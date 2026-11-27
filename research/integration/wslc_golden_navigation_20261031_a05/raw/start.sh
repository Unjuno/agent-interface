#!/bin/sh
set -eu
Xvfb :91 -screen 0 1280x800x24 -nolisten tcp -ac > /out/xvfb.log 2>&1 &
export DISPLAY=:91
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/source/research/live_control:/source/research/observation_gating:/source/research/observation_tiles:/source/research/real_apps_v1:/source
sleep 1
openbox --sm-disable > /out/openbox.log 2>&1 &
exec timeout 90s python3 /source/research/live_control/probe_integrated_efficiency_runtime_v1.py
