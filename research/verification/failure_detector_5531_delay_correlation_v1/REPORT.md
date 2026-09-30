# Issue #5531 T4 — STOP: independent replay mismatch

## Disposition

`STOP_AUDIT_REPLAY_MISMATCH`. The exact formal runner was invoked once and exited 0, but the pre-frozen independent raw-only auditor was invoked once and exited 1 with `errors=["replay_mismatch"]`. Therefore **no experimental gate is accepted and no detector-accuracy/completeness claim is made**. The original runner stdout and auditor stdout are retained unchanged in `RAW-01.json` and `AUDIT-01.json`. This allocation is not rerun, tuned, or repaired post hoc.

Construction before freeze: 7/7 tests passed; auditor parsed successfully. That is harness construction evidence only.

## Provenance

- Allocation: `fd5531-delay-correlation-20261001-01`
- Frozen main: `55c467786b3b98e5f8d1746f9c2970b7ada8b47c`
- Frozen source and plan identities: `FREEZE.md`
- Formal invocation: 1, exit 0, local host CPython 3.11.9 / win32, `container:false`.
- Auditor invocation: 1, exit 1; independently recomputed 300,000 policy rows, imported no candidate module.
- Runner raw Git blob SHA-1: `fd95c5655752e2bdba90c0e67a2f5db0b292156f`; canonical JSON SHA-256 (without terminal line ending): `b8f1ef68d39a99912eca7fa87828a0972b4cac4e34ad74de66ee0bc3fc05f1f8`.
- Audit output Git blob SHA-1: `3381cc15541d927cf4dcbf7065b3f0b36a0d1732`.
- Runner invocations / auditor invocations / retries / tuning: `1 / 1 / 0 / 0`.

## Raw-only observations — not accepted findings

At primary threshold 4, the runner emitted 8,961/10,000 crashed cases as failed by tick 8, and 4 false final failures among 10,000 healthy-heavy-tail cases for the typed policy, versus 2,093 for timeout-as-failure. It also emitted 7,924 cumulative suspicion ticks in the heavy-tail class. These numbers are included only to locate the raw output; **the independent replay mismatch prevents treating them as validated results**.

The raw also shows an internal summary pattern requiring diagnosis in a new allocation: at threshold 2 it reports all 10,000 crashed cases ending `FAILED` but `crash_failed_by_8=0`, whereas threshold 4 reports 8,961 for both. No explanation is inferred here.

## Scope and resource use

This was a synthetic local CPU simulation only: no Docker/OrbStack (the active #5085 lease is assigned to another allocation), no LM Studio/model inference, no GPU computation, no network call by the experiment, no GUI, and no effectful action. LM Studio was stopped and GPU utilization returned to idle before formal execution. The outcomes, even if later explained, would remain conditional on the frozen synthetic delay and witness assumptions; they cannot establish real failure-detector behavior.

Any correction belongs in a **new successor allocation** with a diagnosis of the raw/auditor discrepancy and new frozen sources. Preserve this STOP and all source/result hashes.
