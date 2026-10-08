# A02 run log

## Construction (pre-freeze)

- Host: macOS 27.0 arm64, CPython 3.14.5.
- `python3 -m unittest -v test_model.py`: 8 tests passed. The full 481-schedule construction output matched the independently implemented oracle row-for-row. This was construction validation; the formal candidate entrypoint and formal auditor entrypoint were not invoked.
- `python3 -m py_compile candidate.py auditor.py test_model.py`: passed.
- Network-deny boundary probe under `/usr/bin/sandbox-exec -p '(version 1) (deny network*) (allow default)'`: loopback connect returned `PermissionError(EPERM)`, confirming the sandbox denies networking.
- Formal candidate: NOT RUN at freeze time.
- Formal auditor: NOT RUN at freeze time.

## Formal run

Append the single candidate and conditional single auditor invocation, exact exit statuses, SHA-256 values, and first disposition here after the frozen run. Do not alter or retry the formal outputs.
