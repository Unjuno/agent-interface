# Issue #5960 T0 — bounded pre-recovery evidence capture

Allocation: `R133-RECOVERY-PRESNAPSHOT-5960-T0-20261002-01`

## H / T / D / C / U

- **H:** In recoverable, non-immediate-hazard failures, a bounded authority-free snapshot of source-bound volatile evidence can distinguish two planted causes that ordinary recovery makes observationally identical. Safety-stop, input release, privacy, source freshness and deadline gates must dominate capture. This tests method consistency only, not real GUI diagnosis value.
- **T:** Deterministic, no-model/no-GUI finite-state simulation over fixed synthetic scenarios and seeds. Compare `IMMEDIATE_RECOVER`, `PRE_RECOVERY_MINIMAL_CAPTURE`, and `CAPTURE_EVERYTHING`; include discriminating causes A/B, a null cause, hazard/held input, zero slack, forbidden private signal, stale source, lost receipt, and observer perturbation. Candidate runs once after tests and freeze; independent auditor reconstructs trace invariants separately.
- **D:** Scoped pass only if eligible A/B evidence is retained by minimal capture and erased by immediate recovery, null evidence does not create a diagnosis, and every hazard/privacy/deadline/stale-source/lost-receipt/perturbation gate prevents unsafe or unauthorized evidence promotion. The synthetic capture budget is 2 units; minimal capture costs 1 and overcapture costs 9, so overcapture must be marked deadline-missing and identified as a negative control, not a successful policy.
- **C:** The simulator encodes the expected causal relation by construction. Equal post-recovery states and cause labels are planted, not empirical GUI observations. Policy timing and byte costs are illustrative units, not measured latency or privacy risk.
- **U:** This cannot show diagnostic yield, reproducer yield, recovery quality, real observer perturbation, runtime latency, or transfer to a live interface. T1 requires an eligible retained cohort or isolated matched fixtures with blinded independent labels and randomized/counterbalanced policies.

## Frozen gates

Immediate safety release/stop is first whenever `hazard`, `held_input`, `privacy_forbidden`, or `slack == 0`. Such runs must record `SNAPSHOT_SKIPPED_SAFETY` and no snapshot bytes. Eligible minimal capture is allowed only with fresh source ID, available receipt, no observer perturbation, and capture cost within slack; otherwise recover immediately and report the exact hold reason. Captures carry failure/source identity and confer no input authority.

`PASS_METHOD_SCOPED` is a construction result only. Any safety-order, privacy, stale-source, missing-receipt, null-cause, or overcapture invariant violation is `FAIL_METHOD`. No retry or live allocation is allowed.
