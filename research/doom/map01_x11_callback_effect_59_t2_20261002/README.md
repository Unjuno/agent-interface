# Issue #59 T2 — callback-state effect boundary

Tests whether W autorepeat `KeyPress` events delivered to the new focused
client cause a specified client-owned state transition. Unlike T1, this records
the event handler's before/after counter and links each counter increment to
one unique raw X11 event. The counter is deliberately synthetic and is not
evidence of a real application's semantic effect.

See `PLAN.md`, `FREEZE.json`, and `REPORT.md`; raw events, callback rows, audit,
run receipt, stdout/stderr, and hashes are retained under `results/formal-01/`.
