# Issue #3311 A02 current-main revalidation

## H — Hypothesis

The saved A02 paired synthetic trace is useful as a narrow accounting-composition result: the acquisition caller should preserve an adapter's incomplete/safe-yield state and must not promote a wrong-value submission to verified task success.

## T — Revalidation on current main

- Current-main base: `1eac6ea9f5b91cc10a8c3dc20374b9d79ffcf179`.
- All six A02 source/test blobs listed in `PLAN.md` were compared with this main tip and match exactly: caller v3, adapters v1/v2, caller/adapter-v2 tests, and compiled GUI core.
- Current-main-matched caller and adapter-v2 suites: 19/19 passed locally on Python 3.12.
- `audit_raw.py` over the retained A02 raw returned `PASS_COMPOSED_RECEIPT_RECONSTRUCTION`.
- A02 SHA-256 manifest entries were checked against the preserved package; no frozen bytes were edited.
- The initial A01 output-path failure remains a STOP record. It was not relabeled or replayed.

## D — Data and scope

The paired A02 record uses three synthetic observation rows, the warm-reuse caller route, zero model callbacks, and a deterministic effect stub. V1 reports inner `TASK_SUCCEEDED` on pixel change but the outer caller returns `TASK_NOT_VERIFIED` after the synthetic effect check fails. V2 safe-yields after one simulated action; the caller returns `EXECUTION_INCOMPLETE/effect_failed`, `confirmed_partial`, with no effect-scorer call. The source snapshot bytes are identical to the six current-main files checked above.

No real GUI/application, OCR, model, OS input, effect, recovery, latency/cost, efficiency, population claim, or one-shot #3489 allocation was used. This is synthetic construction/accounting evidence only.

## C — Conclusion

PASS for the retained, finite A02 accounting contrast and its current-main source/test continuity. No application-effect or product-safety conclusion follows. Keep draft pending independent review.

## U — Uncertainty / preservation

The original A01 runner and failed output-path attempt are preserved separately; the A02 rerun uses a unique run directory and source/runtime provenance. Do not rerun into either frozen evidence path. The three-arm desktop comparison and live task-effect evidence remain outstanding.
