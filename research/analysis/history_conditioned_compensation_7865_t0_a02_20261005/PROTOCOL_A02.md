# Issue #7865 — T0 finite compensation-history experiment (A02)

This is a separately numbered freeze after A01 ended `FAIL_HARNESS`. A01's
source and raw output remain unchanged. A02 reuses the exact frozen
`model.py` and `oracle.py` hashes from A01 and changes only the test harness:
the blind-inverse loss assertion now inspects the blind policy's output,
not the pre-policy trace state. No candidate behavior or fixture is changed.

H/T/D/C/U and all seven trace definitions, four policies, and PASS/FAIL gates
are exactly those in `PROTOCOL.md`. A02 passes only if its independent
pre-freeze gate and its single formal container invocation both pass all
seven tests, including 28 exact candidate/oracle rows, the planted lost
update, field-scoped selectivity, fail-closed conflict cases, and two
independent-oracle mutation checks. Any other source change, fixture change,
test failure, or hash mismatch is STOP/FAIL for A02; do not repair and rerun
this allocation.
