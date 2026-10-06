#!/bin/sh
set +e
mkdir -p results/A01
python3 src/candidate.py --source src/input_owner_v10.py --out results/A01/output --cycles 30 > results/A01/candidate.stdout 2> results/A01/candidate.stderr
status=$?
printf '%s\n' "$status" > results/A01/candidate.exit
exit "$status"
