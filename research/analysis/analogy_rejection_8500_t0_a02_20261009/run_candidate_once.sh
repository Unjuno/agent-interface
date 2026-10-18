#!/bin/sh
set +e
mkdir -p raw/first-outcome
python3 candidate.py --dir . > raw/first-outcome/candidate.stdout.txt 2> raw/first-outcome/candidate.stderr.txt
rc=$?
printf '%s\n' "$rc" > raw/first-outcome/candidate.exit.txt
exit "$rc"
