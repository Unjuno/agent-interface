#!/bin/sh
set +e
python -B /src/runner.py /input/schedule.json /out/raw.json > /out/runner.stdout 2> /out/runner.stderr
result=$?
printf '%s\n' "$result" > /out/runner.exit
exit "$result"
