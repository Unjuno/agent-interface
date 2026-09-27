#!/bin/sh
set +e
python -B /src/audit.py /evidence/raw.json /input/schedule.json /audit-out/audit.json > /audit-out/audit.stdout 2> /audit-out/audit.stderr
result=$?
printf '%s\n' "$result" > /audit-out/audit.exit
exit "$result"
