#!/bin/sh
set +e
python -B -m unittest -v test_audit_hardened.py > /out/tests.stdout 2> /out/tests.stderr
test_rc=$?
printf '%s\n' "$test_rc" > /out/tests.exit
if [ "$test_rc" -ne 0 ]; then exit "$test_rc"; fi
python -B run_probe.py --legacy-source /input/legacy_audit.py --archive-base64 /input/RAW_AND_AUDIT.zip.base64 > /out/probe.json 2> /out/runner.stderr
runner_rc=$?
printf '%s\n' "$runner_rc" > /out/runner.exit
if [ "$runner_rc" -ne 0 ]; then printf 'not_run\n' > /out/audit.exit; exit "$runner_rc"; fi
python -B independent_audit.py /out/probe.json /input > /out/audit.stdout 2> /out/audit.stderr
audit_rc=$?
printf '%s\n' "$audit_rc" > /out/audit.exit
exit "$audit_rc"
