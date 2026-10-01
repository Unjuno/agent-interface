#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 -m unittest -v test_engine.py
xvfb-run -a python3 gui_smoke.py
python3 -m py_compile engine.py arena.py test_engine.py gui_smoke.py
printf 'arena-v1 construction smoke PASS\n'
