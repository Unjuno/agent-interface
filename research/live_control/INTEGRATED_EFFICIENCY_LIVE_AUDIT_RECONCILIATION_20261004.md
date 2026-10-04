# #57 live result reconciliation — 2026-10-04

This is an additive, read-only post-run reconciliation of `integrated-efficiency-live-01`. It does not modify the preregistration, raw results, earlier audits, or the historical finite-allocation disposition. No model, GUI, or formal allocation was rerun.

## Reconciled usage

`audit_integrated_efficiency_summary_reconciliation_v1.py` joins all 14 retained model `result.json` records to their `events.jsonl` `thread.started` IDs and `turn.completed` usage, then joins the three schema-preflight gate reports and model event streams. All 14/14 model event/result/trace joins and 3/3 preflight gate/event/trace joins agree, with no duplicate or mismatched call IDs. The 17 total attempts are unique. A follow-up run found and fixed an indentation defect that had omitted per-arm attempts from the accumulator; the regenerated trace totals now include every task call and preflight exactly once and match the independently recomputed raw totals and retained `audit.json`:

| Provider-reported usage field | Total |
|---|---:|
| Input tokens | 153,470 |
| Cached input tokens (subset of input) | 4,864 |
| Cache-write input tokens | 0 |
| Output tokens | 2,435 |
| Reasoning output tokens (subset of output) | 837 |

The detailed report, trace reconciliation, and audit agree on final cumulative input tokens of 63,128 plain, 63,779 ephemeral, and 26,563 persistent. Those values include each arm's preflight. The task-level `report.json` retains each attempted stage's input/output and usage fields. The reconciliation identifies the checked repository tip as `3f7d3d4967ccac2559e473c982ad733a7d501a41`.

The separate `integrated-efficiency-live-01-summary.json` has the same study name, seed, and source-main label, but reports 131,517 / 136,473 / 56,403 input tokens. These exceed the detailed report by 68,389 / 72,694 / 29,840 respectively. The differences do not reconcile to the 4,864 cached-input subset total. The summary file is preserved unchanged and should not be used as an input-token result unless its provenance and arithmetic are resolved. The more detailed trace/report/audit agree with one another on the totals above; this reconciliation does not infer why the standalone summary differs.

## Frozen-source replay boundary

The first reconciliation checked current main and the two retained comparison-source snapshots. That bounded search found six unavailable source copies and stopped the fresh source audit at `run_integrated_efficiency_live_v1.py`. A broader history search recovered the complete preregistered closure from commit `54910c6f9f0594c609f1f3c6895a918caa64130f` (`Freeze integrated live runner`). All 29 files match the SHA-256 values in the retained preregistration. Their byte-for-byte copies and paths are preserved in `results/integrated-efficiency-live-01-frozen-source-v1/`; the manifest records the commit and hashes. This establishes source-byte availability. It does not independently prove which checkout the original execution used.

`replay_integrated_efficiency_frozen_sources_v1.py --write` reconstructs a temporary tree from those archived bytes, copies the retained study records, runs `audit_integrated_efficiency_live_v1.py`, and compares the generated audit with the preserved `audit.json`. It exited 0: all 29 source hashes matched, the auditor returned 0 with RETAIN, and the fresh audit JSON equals the preserved audit byte-semantically. The temporary replay does not contact a model or GUI and does not modify the retained study directory. Its result is preserved in `results/integrated-efficiency-live-01-frozen-source-audit-v1.json`.

The separate `integrated-efficiency-live-01-summary.json` still disagrees with the detailed report, reconciled trace, and audit on input-token totals; its provenance remains unresolved. The historical allocation RETAIN remains unchanged. The replay closes the missing-source-bytes gap but does not establish the original runtime checkout identity, a population success rate, general GUI speedup, human-tempo gain, or second-domain transfer.

## Reproduction

From the repository root, run:

```text
python research/live_control/audit_integrated_efficiency_summary_reconciliation_v1.py --write
```

The reconciliation command writes only the additive `results/integrated-efficiency-live-01-summary-reconciliation-v1.json`. It reports all pinned source bytes available through the frozen-source archive, while exit code 2 remains expected because the standalone summary does not reconcile. Exit 2 does not mean the historical GUI tasks failed. The original result and summary remain untouched.
