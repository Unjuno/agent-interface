#!/bin/sh
set -eu
cd "$(dirname "$0")"
make clean all
./core_tests
python3 -m unittest -v tests/test_facility.py
./gui_smoke.sh /tmp/procedural-ops-facility-gui.json
./facility --benchmark 1000 --seed 1000 --difficulty 0.45 > /tmp/procedural-ops-facility-benchmark.json
./facility --render-benchmark 1000 --seed 424242 --difficulty 0.45 > /tmp/procedural-ops-facility-render.json
cat /tmp/procedural-ops-facility-benchmark.json
cat /tmp/procedural-ops-facility-render.json
