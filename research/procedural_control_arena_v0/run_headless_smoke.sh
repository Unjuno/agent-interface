#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m unittest -v test_engine.py
# GUI import/creation smoke only; a benchmark episode needs an external controller.
timeout 3s xvfb-run -a python3 arena.py --seed 424242 --difficulty 0.25 --clock fixed --report /tmp/procedural-control-arena-smoke.json || code=$?
if [[ ${code:-0} -ne 0 && ${code:-0} -ne 124 ]]; then
  exit "$code"
fi
printf 'GUI smoke reached the bounded timeout as expected; no oracle controller was attached.\n'
