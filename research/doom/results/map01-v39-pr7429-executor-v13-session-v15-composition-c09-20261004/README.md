# C09: latest ExecutorV13 overlaid onto the #7449 MAP01 owner/backend candidate

**Question.** Does the session-v15 candidate compose with the current #7429 executor implementation without breaking release-before-terminal ordering, at-most-once publication, downstream receipt validation, or executor selection?

**Hypothesis.** The #7429 ExecutorV12/V13 publication barrier and error handling can replace the older executor modules in the #7449 candidate overlay; the cancellation-order integration, executor regressions, client guard, and session-selection checks will all pass.

**Test.** Pin PR #7429 head `0f50064a7ea7a69c51cb6751ac313b0c8b5ec9e2`, PR #7449 base `915c46d7f448003d82dd002d6e9fb34141e2712a`, and candidate commit `3e498aebd77e500d5a7b1ac9d434d37350a9f597`. Copy #7449's top-level `research/live_control/*.py` and `research/doom/*.py` modules into a disposable overlay, replace the executor and publication-test files with exact files archived from #7429, then run the five recorded Python tests from that overlay.

**Decision.** PASS for this source-level composition check if all 16 tests pass (1 order barrier, 4 ExecutorV13, 6 cancellation/publication, 4 running-action guard, 1 session-v15 selector). The recorded run passes 16/16. If any test fails, treat composition as unresolved.

**Competing explanation.** These tests may miss interactions in the actual MAP01 session because the selector test uses a stub base module and the event tests use fake backends/Xlib. Passing means source API compatibility and the tested event invariants only.

**Uncertainty and limits.** No full MAP01 session, Doom process, X server, physical input, model, useful task feedback, recovery timing, matched trial, or live allocation was exercised. This does not establish the r134 research gate or supersede review of PR #7429. The #7429 base is `0178fd24e9c317fff40e0fa1952fbe7e8ae01078`; main has advanced since that base. The candidate remains stacked on #7449 pending a reconciled current-main integration.

## Results

All five raw test outputs and zero exit receipts are in `raw/`. `audit_c09.py` verifies source/raw hashes, expected test counts and names, source refs, and scope labels. The exploratory overlay setup initially had path/checkout mistakes; those attempts are explicitly excluded from C09. Only the run from a temp overlay constructed with exact #7429 commit `0f50064...` is considered the C09 result.

No container or live allocation was started.
