# Issue #6505 — A02 report

## Disposition

**PASS_INDEPENDENT_AUDIT_SCOPED** (one OrbStack invocation; exit 0, no OOM). The independent reconstruction verified all 10 frozen Git blobs, the 104,640-byte archive and 3,241,590-byte/11,111-row raw input; all rows and summary matched, with 0 row mismatches. It independently enumerated 2,025 reachable states and 87,551 legal linearizations across 11,111 event words, and confirmed 10,828 words with strict constraint reduction and 39,122 removed ordering constraints. Eight effective corruption mutations were rejected (`PASS_CONTROLS`). The predecessor's original 7/8 no-op control remains preserved exactly; this successor demonstrates that the `linearizations` corruption changes the target field and is rejected. No predecessor candidate/auditor was run and no retry occurred.

After latest main `6cec6079acfbf0e7ee94154784dddc4916ce7b12` was integrated (unrelated archived evidence only), local Analysis Index CI passed 18 test commands / 109 tests, A02 construction passed 7/7, and the index covers 551 retained result/failure directories. Frozen auditor/test/workflow hashes remained unchanged.

## H / T / D / C / U

See `PREREGISTRATION.md`. A01's `STOP_OUTPUT_NOT_EMPTY_OR_MISSING` remains preserved in its own package and is not a result of A02.

## Execution

Raw receipts, stdout, exit code, runtime record, and `RUN_RECORD.json` are retained under `results/audit_01/`; container state/configuration and mount evidence are under `execution/`. The host run used OrbStack context `orbstack`, linux/arm64, with the pinned cached image. Cgroup values were recorded, but resource enforcement is not claimed.

## Limits

Even a scoped PASS would corroborate only the retained finite table, not real traces, GUI/runtime replay safety, latency, storage savings, or product behavior.
