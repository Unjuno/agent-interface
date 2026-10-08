#!/bin/sh
set -eu
cd /facility
./core_tests
python3 -m unittest -v tests/test_facility.py
xvfb-run -a ./facility --gui --auto-reference --no-sleep --seed 424242 --difficulty 0.45 --report /tmp/gui.json
python3 - <<'PY'
import json
p=json.load(open('/tmp/gui.json'))
assert p['success'],p
print('CONTAINER_GUI_PASS',p['state_hash'])
PY
./facility --benchmark 250 --seed 1000 --difficulty 0.45
./facility --render-benchmark 250 --seed 424242 --difficulty 0.45
python3 sweep.py --axis episode_deadline_ticks --values 600,10800 --difficulty 0.45 > /tmp/sweep.json
cat /tmp/sweep.json
