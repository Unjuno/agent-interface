# V39 current-main final-empty observation race A01

## H / T / D / C / U

**H.** The current V39 drain's final `Queue.empty()` check is not atomic with producer enqueue. An observation arriving just after that check can be left queued while the drain reports no pending events. Executor freshness should still prevent the controller from acting on the stale sequence, but the current controller may abort without a fresh replan.

**T.** Execute the exact pinned current-main `drain_pending_observation_events`, `Executor.submit`, and nested `execute_segment` ASTs. A deterministic queue fixture inserts sequence 12 immediately after the final empty result while sequence 11 is the latest drained observation. Require the executor to reject sequence 11 against backend sequence 12 before admission/input; then require the controller rejection path to make one submit and no retry.

**D.** PASS for the identified boundary if the drain returns `latest=11`, `pending_events=false` while sequence 12 is queued, Executor rejects before input, and the controller aborts after one attempt. Any stale input acceptance is FAIL.

**C.** This is a synthetic schedule at a valid concurrent queue interleaving. The `Queue.empty()` result is a point-in-time observation; another producer may enqueue after its lock is released. It does not establish how often the schedule occurs in a live session.

**U.** This does not run the full backend/session or show a live HUD change, model wait, fresh replan, useful feedback, recovery, task progress, physical release, or game outcome. The fail-closed boundary is a safety result; no session continuity or recovery benefit is claimed.

## Result

On base main `99f2521811df790db3c96cdfa9313a6296f247f7`, the exact drain returns sequence 11 with `pending_events=false`, while sequence 12 is already queued after the final empty check. The exact Executor rejects expected sequence 11 against backend sequence 12 with `latest observation sequence required before input`; no admission or input event is emitted. The exact controller `execute_segment` propagates the rejection after one submit and does not retry. This confirms fail-closed behavior and isolates a liveness gap in that schedule.

The earlier late-observation A01 package is frozen to an older controller blob and its runner requires the retired `qsize()` drain. This A01 re-executes the final-empty interleaving against the updated current-main bounded drain. The four source blob IDs and SHA-256 values are in `FREEZE.json`.

## Reproduction

From the repository root:

```powershell
python -B research/doom/v39_final_empty_check_race_a01_20261008/run_experiment.py
python -B research/doom/v39_final_empty_check_race_a01_20261008/audit.py
python -B -m unittest discover -s research/doom/v39_final_empty_check_race_a01_20261008 -p test_race.py -v
```

This is a source-bound construction experiment. It is not an integrated live threat exposure and does not close Issue #59.
