#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 -m unittest -v test_benchmark.py
python3 benchmark.py --seed 123 --difficulty 0.0 --mode headless-perfect >/tmp/control-lab-easy.jsonl
python3 benchmark.py --seed 123 --difficulty 1.0 --mode headless-perfect >/tmp/control-lab-hard.jsonl
xvfb-run -a python3 benchmark.py --seed 123 --difficulty 0.5 --mode gui --smoke-ms 300 --result /tmp/control-lab-gui-result.json
printf 'smoke PASS\n'
