#!/bin/sh
set +e
python -B /src/runner.py > /out/runner.stdout 2> /out/runner.stderr
rc=$?
printf '%s\n' "$rc" > /out/runner.exit
exit "$rc"
