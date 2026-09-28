#!/bin/sh
set -eu
cd "$(dirname "$0")"
make clean all
./test_ops_world
./ops_world --seed 20260928 --family-key 424242 --headless-frames 120 --dump-ppm /tmp/ops-world.ppm --report /tmp/ops-world.json
./ops_world --seed 20260928 --family-key 424242 --bench-frames 1000 \
  --set watcher_count=64 --set required_alerts=0 --set event_rate=0 --set object_count=64
xvfb-run -a ./ops_world --seed 20260928 --family-key 424242 --runtime 1.0 --report /tmp/ops-world-x11.json >/tmp/ops-world-x11.out 2>/tmp/ops-world-x11.err
[ -s /tmp/ops-world.ppm ]
[ -s /tmp/ops-world.json ]
[ -s /tmp/ops-world-x11.json ]
echo "ops-world-v0.2 validity-hardening smoke PASS"
