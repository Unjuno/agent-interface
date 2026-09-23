# #1764 A3 temporal-contract monitor compilation

Decision: **PASS_TEMPORAL_CONTRACT_MONITOR_COMPILATION_A3_SCOPED**

Formal1 / reruns0 / replacements0 / tuning0.

## Exact exhaustive result

- generated traces: **1,062,624**
- complete prefix checks: **5,144,980**
- primary candidate/reference mismatches: **0**
- independent audit recomputed mismatches: **0**
- retained #1719 same-timestamp P counterexample: PENDING in candidate, primary reference and independent reference
- corruption controls: **6/6**
- reachable typed outcomes: exact
- descending timestamps: UNKNOWN
- monitor state shape: fixed 8 fields, independent of trace length

## What A3 establishes

Under the frozen one-shot discrete timestamp-fragment semantics, four representative temporal contracts compile to constant-memory deterministic monitors:

- A_THEN_B_WITHIN(delta)
- P_CONTINUOUS_FOR(tau)
- C_NOT_BEFORE_D
- AFTER_X_NO_Y_FOR(horizon)

Same-timestamp event fragments are not assigned false strict ordering. P predicate false/true fragments at one timestamp remain ordered transitions with zero elapsed duration; false resets continuity immediately.

The A3 formal source is A2-derived. Candidate monitor is byte-identical to #1719/#1743. Primary/independent reference semantics and generators are A2-identical; the scientific change is only the accounting decision gate from #1719's mismatch-truncated 5,144,928 runtime prefixes to the full combinatorial corpus count 5,144,980.

## Provenance

#1719 remains the immutable first formal oracle-integrity failure.
#1743 remains the immutable A2 accounting-gate failure with semantic mismatch0.
A3 is a fresh allocation; no predecessor rerun or result relabeling occurred.

Exact RESULT SHA-256: `26d1bd2b9cc65430d5ddb1c84cd4cc1b94a6d1759ee7e413aa838b3d14e7a904`.
Exact AUDIT SHA-256: `5ee694c6201b910105827c337534003ab162a354f7b3f251891e3a270942605d`.

## Limits

This is a semantic monitor theorem, not live backend evidence. It assumes timestamped fragments are delivered, clock identity is coherent, predicate changes are represented, and each monitor instance owns one obligation. It makes no model, token, runtime latency, GUI, human-tempo or product claim.

The next empirical rung is one private live event-stream transfer with explicit clock/evidence provenance and no semantic-authority escalation.
