# A02 — independent reconciliation after frozen A01 auditor-shape STOP

## H / T / D / C / U (frozen before A02 audit)

**H:** A01’s audit stopped because it modeled the planner submission incorrectly: current V39 passes `planner.await_turn` as a method reference to `ThreadPoolExecutor.submit`, not as an `await_turn(...)` call. An auditor that recognizes the actual AST shape should independently reconcile the unchanged A01 candidate raw and establish whether in-envelope ammo feedback reaches the pending planner turn.

**T:** Read only the A01 raw result at the exact SHA-256 in this freeze and parse the same pinned current-main controller and guard-copy identities. Recognize the `pool.submit(planner.await_turn, ...)` method reference, locate the monitored wait nested under `while not future.done()`, and check the captured soft-summary/prompt and post-`future.result()` decision-record order. Do not run the candidate, controller, planner, game, or image reader again.

**D:** PASS_A02_RAW_AND_SOURCE_RECONSTRUCTION iff the unchanged candidate raw confirms one paired ammo 46→37 `SOFT_CHANGED` with no invalidation and one already-built planner prompt, and AST independently confirms summary capture / `begin_model_turn` precede pending wait, monitor observation occurs in that wait, soft changes return no invalidation, and the event is recorded only after the current future result. Otherwise preserve STOP/FAIL.

**C/U:** This is an auditor repair/reconciliation for an offline synthetic construction result only. It adds no new candidate execution, no production change, no real OCR/model/game/input, and no new allocation. It does not establish useful strategy, timing under a live workload, key release, bounded recovery, task success, survival, or MAP01 exit.

A01 remains immutable, including its candidate raw and `FAIL_AUDIT_TIMELINE_ANCHORS_MISSING`-equivalent audit process failure. A02 is a distinct audit attempt, not a retry or upgrade of any live allocation. No live-game lane is granted or implied.
