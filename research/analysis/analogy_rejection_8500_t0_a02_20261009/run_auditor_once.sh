#!/bin/sh
set +e
mkdir -p raw/first-outcome
python3 audit.py --dir . > raw/first-outcome/auditor.stdout.txt 2> raw/first-outcome/auditor.stderr.txt
rc=$?
printf '%s\n' "$rc" > raw/first-outcome/auditor.exit.txt
exit "$rc"
