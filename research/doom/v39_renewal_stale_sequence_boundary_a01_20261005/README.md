# V39 renewal stale-sequence boundary A01

**H — Hypothesis.** In current main `6a2826d391b77496b69752609a6f07b6971b4b6f`, a newer observation delivered while a cover renewal is being admitted makes its captured `expected_sequence` stale. The admission wait may consume that observation, then return a rejected receipt. Determine the exact exception and the owned failure-cleanup planner/input-release outcome.

**T — Test.** Freeze and hash the production V39 controller plus its cleanup helper. AST-extract the real nested `wait()`, `submit_cover()`, and planner/renewal `ThreadPoolExecutor` block. Inject: previously accepted `cover-0`; its expired terminal with verified empty release; observation sequence 8; then a rejection for renewal `cover-0-renew-1` because the controller submitted sequence 7. Run the real `ControllerFailureCleanup.__exit__` with a fake already-exited child and retained event list. Repeat under normal and optimized Python; no game, model, GUI, OS input, container, or native allocation.

**D — Decision.** Reproduction is confirmed only if the exact current-main path raises the rejected-row `RuntimeError`, no renewal ID is added and no cancel is sent, planner await returns before failure cleanup closes the planner (without an explicit interrupt), the previous accepted cover's release is reconciled verified-empty, and cleanup remains incomplete because scorer/score/owner-close evidence is absent.

**C — Counterevidence.** A future completion just before the stale rejection could bypass the renewal boundary. The FIFO makes the pending planner await remain live until the rejection is consumed, so this test targets the specified overlap. It does not estimate event frequency.

**U — Limits.** This is frozen-source controller construction evidence. It shows failure cleanup closes the planner and verifies the prior accepted cover's retained empty release; it does not prove a pending or rejected renewal released input, score completion, event frequency, GUI/game behavior, live recovery, useful feedback, task effect, MAP01 progress, or a repair. The open PR #7930 review is separate and was not used as evidence. Native live-game authority remains unavailable/unassigned.

`test_current_main_boundary.py` runs only the frozen source composition. `PROCESS_RESULTS.json`, `observed_*.json`, and their test logs retain the observed behavior. `audit.py` verifies source provenance, test outcomes, observed cleanup fields, and checksums.
