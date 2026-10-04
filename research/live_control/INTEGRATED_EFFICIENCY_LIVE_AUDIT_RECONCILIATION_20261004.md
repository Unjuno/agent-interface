# #57 live result reconciliation — 2026-10-04

This is an additive, read-only post-run reconciliation of `integrated-efficiency-live-01`. It does not modify the preregistration, raw results, earlier audits, or the historical finite-allocation disposition. No model, GUI, or formal allocation was rerun.

## Reconciled usage

`audit_integrated_efficiency_summary_reconciliation_v1.py` joins all 14 retained model `result.json` records to their `events.jsonl` `thread.started` IDs and `turn.completed` usage, then joins the three schema-preflight gate reports and model event streams. All 14/14 model event/result/trace joins and 3/3 preflight gate/event/trace joins agree, with no duplicate or mismatched call IDs. The 17 total attempts are unique. Recomputed totals match the retained `audit.json`:

| Provider-reported usage field | Total |
|---|---:|
| Input tokens | 153,470 |
| Cached input tokens (subset of input) | 4,864 |
| Cache-write input tokens | 0 |
| Output tokens | 2,435 |
| Reasoning output tokens (subset of output) | 837 |

The detailed report and audit give final cumulative input tokens of 63,128 plain, 63,779 ephemeral, and 26,563 persistent. Those values include each arm's preflight. The task-level `report.json` retains each attempted stage's input/output and usage fields. The reconciliation identifies the checked repository tip as `3f7d3d4967ccac2559e473c982ad733a7d501a41`.

The separate `integrated-efficiency-live-01-summary.json` has the same study name, seed, and source-main label, but reports 131,517 / 136,473 / 56,403 input tokens. These exceed the detailed report by 68,389 / 72,694 / 29,840 respectively. The differences do not reconcile to the 4,864 cached-input subset total. The summary file is preserved unchanged and should not be used as an input-token result unless its provenance and arithmetic are resolved. The more detailed trace/report/audit agree with one another on the totals above; this reconciliation does not infer why the standalone summary differs.

## Frozen-source replay boundary

Running the checked-in `audit_integrated_efficiency_live_v1.py` on current main stops at its first source hash assertion for `run_integrated_efficiency_live_v1.py`. The frozen preregistration expects SHA-256 `630972a0402d2c6a1cd6a57237165d5b402cf8fc364ceddb36ac998c143a7410`; current main and both retained comparison-source snapshots have `cadb3e068dbe1474541371cb70d87a4681eed9d2d8639ce159962e179f648e83`. The reconciliation also identifies five other preregistered source files for which the exact frozen bytes are unavailable among those current-main/source snapshots: `integrated_efficiency_protocol_v1.py`, `integrated_efficiency_client_v1.py`, `integrated_efficiency_model_v1.py`, `schema_preflight_v1.py`, and `coordinate_frame_transform_v1.py`.

Thus the stored post-run author audit still records the frozen allocation as RETAIN, and the retained result records still support the displayed usage arithmetic. A fresh full audit against the exact frozen executable/source closure is **HOLD** because required frozen bytes are not available. Do not rewrite the historical RETAIN or rerun the consumed allocation to repair provenance. This finite result does not establish a population success rate, general GUI speedup, human-tempo gain, or second-domain transfer.

## Reproduction

From the repository root, run:

```text
python research/live_control/audit_integrated_efficiency_summary_reconciliation_v1.py --write
```

The command writes only the additive `results/integrated-efficiency-live-01-summary-reconciliation-v1.json`. Exit code 2 is the expected recorded HOLD while the standalone summary and frozen source closure remain unresolved; exit 2 does not mean the historical GUI tasks failed. The original result and summary remain untouched.
