# Independent audit attempt 01 — STOP

- **Allocation:** `cache-epoch-monitor-execution-2928-v1-20260928`
- **Command:** `python research/analysis/cache_epoch_monitor_execution_2928_v1/independent_audit.py`
- **Outcome:** auditor exited nonzero before writing `AUDIT.json`.
- **Failure:** `FileNotFoundError` while opening `research/measurement/decision_policy_cache_rung0_v1/cache.py`; inspection showed the auditor used the directory's `parents[3]` rather than `parents[2]` as repository root.
- **Impact:** no candidate code, raw rows, or result values were changed. This was an auditor-path construction failure, not a candidate outcome and not a scientific retry.
- **Correction:** changed only the independent auditor's root calculation to `HERE.parents[2]`, then ran the audit-only command once more. The corrected invocation wrote `AUDIT.json` with all 9 checks passing. The first traceback is preserved in the PR/Issue provenance and summarized here; the runner/result were not rerun or rewritten.
