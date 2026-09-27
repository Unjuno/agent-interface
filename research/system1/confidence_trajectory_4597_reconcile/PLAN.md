# Confidence-trajectory rule reconciliation — successor analysis

Issue: [#4597](https://github.com/Unjuno/agent-interface/issues/4597)
Predecessor: #4588 / PR #4596, merged as `9d069e55f432abc559db56544e7659bbcf550246`.
Allocation: `confidence-trajectory-4597-rule-reconciliation-20260927-01`.

## H — hypothesis

The predecessor `LEVEL_PLUS_VELOCITY` arm applies an undeclared nonnegative-velocity requirement to its current-only positive rule. Correctly replaying the frozen PLAN.md rule will change the six `high_confidence_falling_yield` rows and reduce or eliminate the reported velocity advantage.

## T — frozen reanalysis

This is a deterministic, one-invocation reanalysis of the immutable predecessor `results/formal-01/raw.jsonl`, not a new observation or replacement of the predecessor experiment. Read the predecessor rows as inputs and recorded predictions; recompute the velocity arm from the frozen predecessor PLAN.md specification:

`ACTION iff (p2 >= 0.75) OR (p2 >= 0.55 AND v2 >= 0.20)` for `ACTION_REQUIRED` with valid history; preserve `SELF_CORRECTING -> NO_OP`, `UNCERTAIN -> YIELD`, and invalid-history current-only fallback.

Also independently recompute CURRENT_ONLY for comparison. Report every changed case ID, predecessor vs corrected decisions, and metrics. Preserve predecessor files byte-for-byte. No retuning, row changes, or runtime integration.

Container: reuse exact immutable predecessor image `sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0`, `--pull=never --network none --read-only`, read-only source mount, separate writable output. Python stdlib only.

## D — gates

- Input is exactly 84 predecessor raw rows; source raw SHA-256 matches the predecessor report.
- Independently reconstructed current-only and velocity outputs reconcile for every row; no malformed or missing rows.
- Changed rows are enumerated, not silently pooled into predecessor metrics.
- A separate auditor checks the reanalysis output and expected changed-row set; local container unittest passes.
- Report is explicitly a correction/reanalysis; predecessor outcome remains retained as originally reported.

## C — competing explanations

This exposes an implementation/specification mismatch, not necessarily a defect in the conceptual temporal method. The frozen corpus is authored and finite; its metrics are not event-rate estimates. The discrepancy does not validate any live model.

## U — scope

Synthetic and authority-neutral only. No live/shadow collection or runtime promotion is performed by this allocation.
