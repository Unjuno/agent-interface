# G10 comparison-contract readiness audit (R01)

## Decision

**PASS_CUSTODY_AND_EXPECTED_ADAPTER_HOLD.** The existing G10 live record remains valid as a narrow fixed-Calc positive control. It is **not admissible as a matched efficiency arm** on current main. Do not replay or retrofit it into a fictitious complete caller receipt.

The audit ran against current main `ce6449f38a56e1731f01d1024837fb34c9c759a3` and pinned the current `recorded_comparison_adapter_v1.py` SHA-256 `9680761627e72a1986304eb8985b89280fe74d74f93aef9a2375ec02065aeac1`. All 33 G10 declared source hashes matched their retained source snapshot. All 69 files in the retained run were hashed into [G10_RUN_SHA256.json](G10_RUN_SHA256.json); its manifest SHA-256 is `237b611f16f01e8ed641f4166eeb5f37470101495fc86c052dd32cf73df86527`.

The current adapter rejected the unmodified G10 `raw.json` with the expected `caller receipt does not match the reconciled recorder schema`. The normal and optimized audit outputs are byte-identical. No GUI, provider, OCR, Docker, WSLc or input action ran.

## What G10 establishes

The original scoped audit remains `PASS_SCOPED_LIVE_OCR_GRAPH`: two native guarded programs, 11 compiled graph events, three image observations, seven retained local OCR attempts and two independently scored saved effects. Its known OCR local elapsed time is 493,806,119 ns. Its primary model/provider usage is **UNKNOWN**, as recorded in the original audit. These positive facts are retained; UNKNOWN is not converted to zero.

## Admission crosswalk

| Current comparison requirement | G10 evidence | Status for a matched arm |
|---|---|---|
| Reconciled caller receipt with complete flag, ordered events, raw references, and no unresolved call IDs | `raw.json` has an empty `events` list and lacks `complete`, `raw_refs`, `unresolved_attempt_ids`, and `unresolved_tool_call_ids` | **Missing**; adapter rejection is expected |
| Every provider model attempt and usage, including failures/unknown usage | No recorder `model_attempt` events; primary usage remains UNKNOWN | **Missing**; do not infer zero |
| Matched public tool request/response events | G10 preserves graph/native records, not `tool_call` events in the current recorder contract | **Not joinable without a new evidence-bound adapter** |
| Independent task-score event joined to the caller ledger | Original AUDIT independently parses saved files and records scoped effects, but no recorder `task_score` event exists | **Effect evidence exists; caller-ledger join missing** |
| Comparison identity and environment/model/task pins | PLAN pins allocation, source revision, task outline and source hashes; it has no matched comparison block. The original scope is fixed geometry/font and narrow OCR; provider/model accounting is unavailable | **Insufficient for cross-arm equivalence** |
| Full contiguous lifecycle phases and resource accounting | Raw preserves graph, OCR, native and host timestamps/records, but not the required normalized complete arm ledger and all-attempt model usage | **Partial only** |

The appropriate next experiment is a **new prospectively frozen matched block** that reuses G10's scoped positive effect path and records every arm from the standard caller/recorder, including cold setup, warm reuse, invalidation, bounded repair, all failed attempts, usage receipts, releases and independent saved-byte scoring. G10 itself remains historical positive-control evidence and is not re-executed.

## Reproduction

From the repository root on Python 3.11.9:

- `python research/integration/g10_current_main_comparison_readiness_20261121/audit_g10_comparison_readiness.py --output research/integration/g10_current_main_comparison_readiness_20261121/RESULT.normal.json`
- `python -O research/integration/g10_current_main_comparison_readiness_20261121/audit_g10_comparison_readiness.py --output research/integration/g10_current_main_comparison_readiness_20261121/RESULT.optimized.json`

Both exited 0 and produced byte-identical JSON (2,376 bytes). Conditions and predeclared decision rules are in [CONDITIONS.md](CONDITIONS.md). Raw G10 files were read only; their individual hashes are retained in [G10_RUN_SHA256.json](G10_RUN_SHA256.json).

The first audit-harness invocation exited 1 because the harness incorrectly expected the `events` key to be absent rather than present and empty. The frozen condition itself stated an empty event list. The implementation was corrected without changing any G10 artifact, adapter, or acceptance criterion; the superseded traceback and diagnosis are preserved in [raw-audit-harness-initial-failure.txt](raw-audit-harness-initial-failure.txt).

## Limits

This is an offline custody/schema audit only. It does not independently rerun G10's original auditor, establish provider-side completeness, measure comparative efficiency, establish general Calc reliability, or close Issue #57 / #58.
