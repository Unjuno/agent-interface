#!/bin/sh
set +e
mkdir -p raw/first-outcome
python3 candidate.py --protocol protocol.json --fixture fixture.json --output raw/first-outcome/candidate.json \
  > raw/first-outcome/candidate.stdout.txt 2> raw/first-outcome/candidate.stderr.txt
rc=$?
printf '%s\n' "$rc" > raw/first-outcome/candidate.exit.txt
exit "$rc"
