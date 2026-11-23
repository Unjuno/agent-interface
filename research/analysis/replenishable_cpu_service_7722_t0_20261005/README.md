# Issue #7722 T0 — replenishable CPU service

This package records the first frozen, CPU-only scheduler simulation for [Issue #7722](https://github.com/Unjuno/agent-interface/issues/7722). Its original auditor recorded `METHOD_PASS_SCOPED` and the scientific gate recorded `FAIL_HYPOTHESIS`. Subsequent review found defects in the original mutation-result handling, policy-dispatch reconstruction, backpressure admission audit, and optimized-mode retained verifier. Treat the original method PASS as superseded; the candidate, raw trace, original audit output, and frozen source remain unchanged.

`review_audit.py` is a separately versioned, read-only reconstruction of all 18 retained runs. It checks control-priority/FIFO dispatch and the queue-capacity condition for every best-effort rejection. Its supplemental audit rejected the six original mutation classes plus dispatch-order and premature-backpressure mutations, while accepting the unchanged trace. This supplemental check did not invoke the candidate or original frozen auditor and does not upgrade the consumed formal allocation or establish a computer-control/runtime result.

The result is useful negative evidence about this Qc/Pc allocation: p99 improved by 71–77%, but a 5-tick rolling control budget did not cover every fixed-seed adjacent-arrival pattern. It does not establish that reservations are unnecessary or that real CPU contention delays release. No tuning or rerun followed the retained first result.

## Contents

- `PROTOCOL.md`: H/T/D/C/U, units, thresholds, model and scope.
- `cases.json`: exact fixed-seed schedulable, negative, overload and replenishment-boundary traces.
- `freeze.json`: main base, image, requested resources, invocation count and frozen source hashes.
- `candidate.py`, `auditor.py`: frozen deterministic scheduler and original raw-event verifier, preserved byte-for-byte.
- `review_audit.py`, `output/review/review_audit.json`: supplemental read-only reconstruction and its hash-bound result.
- `test_review_regressions.py`: regressions for the identified review defects.
- `output/candidate/`: untouched candidate raw JSON, stderr, WSLc logs, CID and elapsed-time metadata.
- `output/auditor/`: untouched independent audit result, stderr, WSLc logs, CID and elapsed-time metadata.
- `REPORT.md`, `RUN.md`, `RESULT.json`: interpretation, reproduction and compact outcome.
- `SHA256SUMS`: checksums for every retained file except the checksum list itself.

## Verification

Run `python verify_retained.py` to check the exact checksum manifest, frozen inputs, retained raw/audit bytes, supplemental reconstruction and recorded run metadata. It uses explicit failures rather than Python `assert`, including under `python -O`; it never launches the candidate or original auditor. The one candidate and one frozen-auditor invocations are not repeated.
