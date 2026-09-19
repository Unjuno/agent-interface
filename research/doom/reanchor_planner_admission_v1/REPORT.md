# Reanchor planner admission — deterministic formal result

Task `MAP01-REANCHOR-PLANNER-ADMISSION-20260917-001`, Issue #629.

## Decision

**`PASS_REANCHOR_PLANNER_ADMISSION_SCOPED`**.

One source-first frozen six-case deterministic matrix ran once after freeze, with no retry, tuning, GUI/game/model/provider call, or authority-bearing reanchor path.

The exact upstream `semantic_grounding_admission_v1.py` source is retained at SHA-256 `337eed1ef5fc248ba121ad7c9769fda7e2f685bade1c82482542eab2b0674dcc`. The canonical no-authority reanchor receipt binds sequence, RGB hash and pointer binding; its canonical digest is `6afe34e25fde1996812e2b5d1a3c26320f51496a7a265dc8ea86b0dd53e52f68`.

## Formal matrix

| Case | Result | Fresh planner decision eligible |
|---|---|---|
| `matching_completed` | `FRESH_PLANNER_DECISION_ELIGIBLE` / `matching_reanchor_receipt_completed` | `true` |
| `capacity_deferred` | `TASK_DEFERRED` / `deferred_upstream` | `false` |
| `completed_stale_receipt` | `TASK_BLOCKED` / `stale_reanchor_receipt` | `false` |
| `receipt_grants_input_authority` | `TASK_BLOCKED` / `reanchor_receipt_authority_violation` | `false` |
| `deferred_with_output_usage` | `TASK_BLOCKED` / `invalid_typed_outcome` | `false` |
| `changed_receipt_old_digest` | `TASK_BLOCKED` / `reanchor_receipt_content_mismatch` | `false` |

Only the matching validated `COMPLETED` outcome becomes `FRESH_PLANNER_DECISION_ELIGIBLE`. It still grants neither semantic nor input authority, preserves `ordinary_executor_admission_required=true`, and records `old_action_authority_reused=false`.

Exact capacity deferral remains `TASK_DEFERRED` with no grounding/action authority. A completed outcome bound to a stale receipt digest, a receipt mutated to grant input authority, malformed deferred output carrying result/usage, and changed receipt content presented with the old digest all fail closed before fresh-decision eligibility.

## Integrity

Frozen audit passes with zero errors. Postformal source hashes are unchanged. The 16 frozen unit/mutation tests re-pass after formal execution. Nine direct mutations of the actual formal result are rejected by the unchanged audit, including authority escalation, removal of ordinary executor admission, stale-receipt promotion, receipt-digest lies, blocked-output leakage, source dependency mutation, and case deletion.

## Interpretation

This closes only a provenance/authority composition gap between the no-authority post-recovery reanchor receipt from #615 and the existing typed semantic-grounding admission boundary. It shows how a completed planner outcome can be *eligible as a fresh decision* only when it names the exact current reanchor context. It does not execute the resulting action and does not establish provider availability, model correctness, latency, gameplay value, or MAP01 clear.

The next rung should be a separately frozen supported-host service-admission/model call that binds the real request to this receipt digest and still requires ordinary executor admission. Do not reuse the discarded pre-recovery action.
