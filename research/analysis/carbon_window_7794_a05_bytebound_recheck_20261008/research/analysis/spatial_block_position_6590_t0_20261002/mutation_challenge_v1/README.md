# #6590 successor: split-overlap auditor mutation challenge

This independent one-shot container challenge addresses the review finding on the predecessor T0's `intentional_position_overlap_is_rejected` gate. That gate evaluated a set predicate directly rather than injecting a malformed row into split aggregation.

H: if one row is reassigned to a different spatial block while retaining its original coordinate, that coordinate appears in both the held-out block and its training complement; split summarization must report the overlap and the top-level raw-only auditor must fail closed on the mutated row.

T: generate the frozen 12,800-row synthetic raw once, run the frozen auditor once on clean raw, then once on a single-block-label mutation. Inspect the resulting split-overlap count and fail-closed decision. A separately frozen test suite exercises both clean and mutated paths.

D: PASS only if the clean raw returns `METHOD_PASS`, the single mutation yields a positive position-overlap count in the affected fold, and the top-level auditor returns `HOLD_AUDIT_INTEGRITY` with a row-reconstruction error. Otherwise `FAIL_METHOD`; command/runtime/provenance failure is `STOP`.

C: the top-level auditor may reject only because the mutated row no longer matches the frozen row oracle, not because it has a dedicated leakage error. We therefore require both the lower-level split summary's explicit overlap count and the full audit's fail-closed result; neither alone is sufficient.

U: this is a synthetic corruption-control experiment, not T1 model evidence, not a real-data leakage estimate, and not proof of GUI robustness. It does not amend the predecessor T0 result. Docker validates this exact finite method on Python 3.12; WSLc is not involved.

See `FREEZE.json` and `RUN_PROTOCOL.md` for immutable source/image/gate identity. Outputs are retained in `results/`.
