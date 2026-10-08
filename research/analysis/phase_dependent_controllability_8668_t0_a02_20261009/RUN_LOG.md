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

### Formal A02 run — first and only execution

- Recorded UTC: 2026-10-08T20:48:58.239661+00:00
- Candidate: invoked once under network-deny `sandbox-exec`; exit 0; 1364320 bytes, SHA-256 `7cab3b4c4bab70ae56e46c7bff2396d94158d7cf9ac3883317fffb6281e8d4c5`; stderr 0 bytes.
- Independent auditor: invoked once under the same network-deny sandbox; exit 0; 1455 bytes, SHA-256 `1c43e952cf98530a123a013da425b031c56c19709abd366af5f9c06e0d87d51a`; stderr 0 bytes. Formal retries: 0.
- Raw schedules: 481; independent oracle: 481; structural/row errors: 0; five mutation controls rejected.
- Decision: `SUPPORT_FOR_PHASE_REFINEMENT_SCOPED`; method gate: `PASS_METHOD_SCOPED`. Safe-removal opportunities: 228 overall, including 114 with a retry requested.
- First disposition retained as emitted; no candidate or auditor rerun.
