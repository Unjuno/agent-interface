# Issue #6590 successor result — block-overlap mutation challenge

**Decision: `MUTATION_PASS` in isolated OrbStack containers.** The clean 12,800-row raw table passed the frozen auditor as `METHOD_PASS`. The frozen mutation changed only `block_id` for row `uniform_positive_control/x00-y00/negative/r00`, from `b00` to `b01`, leaving its coordinate `(0,0)` unchanged.

The pre-reconstruction split summary reported `position_overlap_count=1` in both affected folds (`b00` and `b01`). The raw-only top-level auditor then returned `HOLD_AUDIT_INTEGRITY` with exactly one `row_reconstruction` error. All three commands exited 0, were run once without retries, on pinned `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, in separate `--network=none`, read-only-root containers. The unrelated active OrbStack container was untouched.

This directly challenges the predecessor's weak overlap assertion: a single actual block reassignment became visible to the split aggregate and was rejected by the frozen row oracle. It does not prove a dedicated semantic leakage error code; the top-level rejection is specifically due to row reconstruction mismatch. Full raw, both audits, container event IDs/timestamps, stdout/stderr and hashes are in [`results/`](results/).

Scope is synthetic method/corruption validation only. No model was fit and no issue-level T1 visual-position hypothesis, real-data leakage, GUI behavior, calibration, safety, or authority claim is supported. The predecessor allocation and its `METHOD_PASS` record remain unchanged.
