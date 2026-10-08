#!/bin/sh
set +e
python -B /src/independent_audit.py > /audit/audit.stdout 2> /audit/audit.stderr
rc=$?
printf '%s\n' "$rc" > /audit/audit.exit
exit "$rc"
