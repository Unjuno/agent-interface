#!/bin/sh
set +e

python -B -m unittest -v test_protocol > /out/tests.stdout 2> /out/tests.stderr
rc=$?
printf '%s\n' "$rc" > /out/tests.exit
if [ "$rc" -ne 0 ]; then
    printf '%s\n' STOP_TESTS > /out/allocation_decision
    exit "$rc"
fi

python -B -c 'import ast, pathlib; [ast.parse(p.read_text()) for p in pathlib.Path("/src").glob("*.py")]; print("PASS_PYTHON_AST")' > /out/python_syntax.stdout 2> /out/python_syntax.stderr
rc=$?
printf '%s\n' "$rc" > /out/python_syntax.exit
if [ "$rc" -ne 0 ]; then
    printf '%s\n' STOP_SOURCE_SYNTAX > /out/allocation_decision
    exit "$rc"
fi

for script in /src/formal_entry.sh /src/audit_entry.sh /src/manifest_entry.sh; do
    sh -n "$script"
    rc=$?
    name=$(basename "$script" .sh)
    printf '%s\n' "$rc" > "/out/${name}_syntax.exit"
    if [ "$rc" -ne 0 ]; then
        printf '%s\n' STOP_SHELL_SYNTAX > /out/allocation_decision
        exit "$rc"
    fi
done

python -B /src/probe_baseline.py > /out/construction_probe.stdout 2> /out/construction_probe.stderr
rc=$?
printf '%s\n' "$rc" > /out/construction_probe.exit
if [ "$rc" -ne 0 ]; then
    printf '%s\n' STOP_BASELINE_PROBE > /out/allocation_decision
    exit "$rc"
fi

python -B /src/runner.py > /out/runner.stdout 2> /out/runner.stderr
rc=$?
printf '%s\n' "$rc" > /out/runner.exit
if [ "$rc" -ne 0 ]; then
    printf '%s\n' STOP_OR_RUNNER_GATE > /out/allocation_decision
    exit "$rc"
fi

python -B /src/independent_audit.py > /out/audit.stdout 2> /out/audit.stderr
rc=$?
printf '%s\n' "$rc" > /out/audit.exit
if [ "$rc" -ne 0 ]; then
    printf '%s\n' STOP_INDEPENDENT_AUDIT > /out/allocation_decision
    exit "$rc"
fi

python -B /src/manifest_probe.py > /out/manifest.stdout 2> /out/manifest.stderr
rc=$?
printf '%s\n' "$rc" > /out/manifest.exit
if [ "$rc" -ne 0 ]; then
    printf '%s\n' STOP_MANIFEST_VERIFIER > /out/allocation_decision
    exit "$rc"
fi

printf '%s\n' PASS_AUDIT_BOUNDARY_REPAIRED_SCOPED > /out/allocation_decision
exit 0
