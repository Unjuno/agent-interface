#!/bin/sh
set +e
python -B /src/runner.py /out/raw.json > /out/runner.stdout 2> /out/runner.stderr
runner_rc=$?
printf '%s\n' "$runner_rc" > /out/runner.exit
if [ "$runner_rc" -ne 0 ]; then
  printf 'not_run\n' > /out/audit.exit
  exit "$runner_rc"
fi
python -B /src/audit.py /out/raw.json /src > /out/audit.stdout 2> /out/audit.stderr
audit_rc=$?
printf '%s\n' "$audit_rc" > /out/audit.exit
exit "$audit_rc"
