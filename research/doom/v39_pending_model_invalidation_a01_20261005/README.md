# V39 pending-model invalidation A01

## H / T / D / C / U

**H.** On current main `e724d6d795da2852c043cb53cfd92d5a9222a091`, a fresh paired-health/ammo observation that invalidates an admitted fire cover while `planner.await_turn` is pending is consumed before the matching model result. The controller interrupts the planner, cancels the active cover, waits for a verified-empty release, and rejects the returned answer at final admission—even if the model result races back marked answer-eligible.

**T.** Freeze `research/doom/map01_overlap_controller_v39.py` and execute its actual nested `wait()` and pending-planner `while` block by AST extraction. Use the production `DoomCoverSignalPairMonitor`, `cancel_invalidated_cover`, and `final_admission_from_planner_result`; inject one fresh paired frame crossing the authored health floor while a planner future waits. The fake planner returns an answer-eligible result only after the production interruption call. The fake session then returns a matching cancelled terminal with verified empty keys and buttons. Run once under normal Python and once under `-O`.

**D.** PASS only if the extracted current-main loop returns from wait on the paired invalidation before the model future completes; sends cancellation for the active cover; observes the matching cancelled terminal with verified-empty release; interrupts the planner; the future's answer is marked eligible to exercise the race; and final admission is `REJECTED_POLICY_INVALIDATED`. Otherwise retain FAIL/STOP with the raw trace.

**C.** This is local controller-construction evidence. A model that cooperates with the interrupt stub cannot reproduce provider cancellation races, and a synthetic observation is not a real visible threat. A06 already covers monitor/helper behavior separately; this test composes those production helpers with the actual pending-model loop to cover the missing ordering boundary.

**U.** No Doom process, model provider, GUI, OS input, physical release, game progress, independently useful feedback, recovery efficacy, terminal task effect, or MAP01 outcome was measured. The passing fake release receipt validates only the controller's acceptance gate, not a physical key release. The live threat-exposure lane remains unassigned.

## Observed outcome

Both frozen-source runs passed (1/1 normal and 1/1 optimized). The test waited until the fake planner had entered its pending await, then supplied sequence 11 with health 80 against the admitted floor 88 while ammo remained 4. The actual nested wait returned the hard health invalidation before observing a planner terminal. Cancellation interrupted the planner and targeted `cover-0`; its matching terminal reported verified empty keys/buttons. The planner stub deliberately returned an answer-eligible completed answer after that interrupt to exercise the race; final admission returned `REJECTED_POLICY_INVALIDATED`, with no executor admission or input authority. The independent raw/source audit passed 22/22 checks and confirmed the frozen production import closure is unchanged on latest `origin/main` `d3a51bc4c962b223d05280225042b96a033df8bf`.

The initial construction pass and first audit failure are retained as `raw-*-initial-fixture.json`, `AUDIT_INITIAL_FAIL.json`, and `RESULT_INITIAL_AUDIT_FAIL.json`. The first fixture did not prove the planner thread had entered its pending await, and audit v1 read the invalidation from the wrong JSON nesting. The refined run added a planner-started barrier; audit v2 corrected the raw path. No production source changed and the refined test was not retried after its passing outcome.

## Reproduction

From the repository root, run `python -m unittest research.doom.v39_pending_model_invalidation_a01_20261005.test_pending_invalidation -v` and then `python -O -m unittest research.doom.v39_pending_model_invalidation_a01_20261005.test_pending_invalidation -v`. `audit.py` independently checks source identity, both retained raw records, ordering, release fields, and the final gate. `FREEZE.json` names the exact source commit and hashes the imported repository source closure plus candidate test before the refined runs. `SHA256SUMS` covers the retained package files.
