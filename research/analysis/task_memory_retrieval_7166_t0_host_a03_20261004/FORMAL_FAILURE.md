# A03 formal failure — FAIL_METHOD

Candidate ran once and produced 72 rows; independent auditor base reconstruction
passed, but only five of six corruption controls were rejected. The frozen
wrong-label mutator rewrote a current-only `NONE` label to `NONE`, so it was a
no-op and escaped. Candidate/auditor exits 0/1, retries 0. Full raw and report:
[`results/REPORT.md`](results/REPORT.md). This is authored finite fixture
evidence only, not retrieval/model/cost/task-effect evidence. Preserve unchanged.
