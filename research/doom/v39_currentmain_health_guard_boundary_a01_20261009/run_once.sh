#!/bin/bash
set -u
cd "$(dirname "$0")"
mkdir -p results
PYTHON=/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
if ! command -v sandbox-exec >/dev/null 2>&1; then
    printf '%s\n' 'sandbox-exec unavailable; STOP before candidate invocation' > results/STOP.json
    exit 2
fi
if sandbox-exec -p '(version 1) (deny network*) (allow default)' \
    "$PYTHON" candidate.py > results/candidate.stdout.json 2> results/candidate.stderr; then
    status=0
else
    status=$?
fi
printf '%s\n' "$status" > results/candidate.exit
exit "$status"
