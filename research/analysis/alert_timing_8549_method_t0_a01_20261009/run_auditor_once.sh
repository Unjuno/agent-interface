#!/bin/sh
set +e
mkdir -p raw/first-outcome
python3 auditor.py --protocol protocol.json --fixture fixture.json --raw raw/first-outcome/candidate.json \
  --output raw/first-outcome/audit.json \
  > raw/first-outcome/auditor.stdout.txt 2> raw/first-outcome/auditor.stderr.txt
rc=$?
printf '%s\n' "$rc" > raw/first-outcome/auditor.exit.txt
exit "$rc"
