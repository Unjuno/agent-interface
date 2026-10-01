# First allocation STOP — Issue #3850 model diagnostic repair

Formal model calls: **0**. No Docker formal row started. The first allocation is unconsumed and must remain unchanged; this record documents why no model result is assigned.

Pre-allocation readiness findings:

1. The frozen prompt template has `Task: {task}`, while the frozen case task string already says `Take one read-only observation...`; substituting literally would not match the plan's declared single-`Task:` prompt. No prompt reached a model.
2. The resource gate container `mitra-rung0-853-formal-01` became terminal with exit 137. Subsequent read-only snapshots showed newly appearing/disappearing external Docker containers, one from the same image family and one near one CPU. Their ownership could not be established from snapshots. None was inspected internally, stopped, or modified. Docker concurrency was not stable enough to proceed.
3. Local Docker-only construction/syntax checks passed. Empty-allocation audit negative control correctly produced STOP/HOLD. Two early audit-fixture layout errors are retained as setup failures, not model outcomes.

A successor allocation needs a corrected single-`Task:` prompt, an independent runner/auditor, updated source hashes and GitHub read-back, plus a resource gate based on stable ownership/quiet interval. No retry or substitution is authorized under this allocation. No GitHub Actions/workflow ran the experiment. See Issue #3850 comment 5852704126.
