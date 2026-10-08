# A03 result — FAIL_METHOD

The candidate ran once on the frozen 72-case fixture and exited 0. It emitted
72 rows. The independent auditor ran once and independently reconstructed the
base result as `PASS`, but the allocation-level gate is **FAIL_METHOD** because
only five of six frozen corruption controls were rejected.

The failed control is specifically a no-op mutation: the auditor sets row 0's
label to `NONE`, but row 0 is already the current-only `NONE` case. The
mutation-control harness therefore reports `wrong_label: false`. This is not
evidence that candidate labels are correct under all corruptions; the frozen
gate requires all six controls. Do not repair and rerun this allocation. Any
future validation must be a new additive allocation with a fresh freeze.

The other five controls (source hash tamper, ambiguous identity pick, authority
escalation, dropped history event, forked lineage pick) were rejected. Base
audit was PASS; rows=72. Formal invocation counts are candidate=1, auditor=1,
retries=0. Exact outputs and stdout are retained beside this report.

Scope is only the authored deterministic method fixture. No natural retrieval,
model, GUI, cost, task effect, latency, runtime, or product result is established.
