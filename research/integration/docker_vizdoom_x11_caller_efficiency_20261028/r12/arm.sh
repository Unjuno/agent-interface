#!/bin/bash
set +e
Xvfb :91 -screen 0 1280x1024x24 -cc 4 -nolisten tcp >/tmp/xvfb.log 2>&1 &
xvfb_pid=$!
sleep 0.5
export DISPLAY=:91
export PYTHONPATH=/workspace
cd /tmp
python3 /evidence/run.py --arm "$ARM" --pair "$PAIR" --out "/evidence/arms/pair${PAIR}-${ARM}"
status=$?
kill "$xvfb_pid" 2>/dev/null
wait "$xvfb_pid" 2>/dev/null
exit "$status"
