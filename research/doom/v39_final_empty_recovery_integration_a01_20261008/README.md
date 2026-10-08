# Final-empty race × stale-rejection recovery A01

## H / T / D / C / U

**H.** The exact current-main drain can report no pending event while sequence 12 is already queued after its final empty check. The stale Executor submit is rejected. The candidate stale-rejection recovery in PR #8643 should then consume sequence 12, preserve the no-authority decision, and return fresh evidence for a new planner decision without retrying the stale action.

**T.** Freeze current main `1f81daa690b567a9a049cc75fae8619b2660c343` and PR #8643 head `71344443fbb72a5f055cca4417e26207aaabbdf3`. Reproduce the late arrival with the exact baseline drain; pass the resulting queue and stale rejection to the candidate's exact recovery helper. Check the recovered sequence, consumed queue row, and authority/retry fields.

**D.** PASS only if the baseline drain returns 11 with `pending_events=false` while 12 is queued, the candidate recovers 12, consumes the row, creates no action authority, requires a new decision, and emits no retry/input. Otherwise FAIL or HOLD if frozen sources cannot be read.

**C.** The deterministic queue reproduces a valid interleaving, but production scheduler timing and the live observation producer may differ. Existing helper-level recovery tests cover an already-queued fresh row; this test specifically joins that helper to the final-empty schedule.

**U.** The production `wait`, running-action guard, and admission receipt functions are not run as integrated implementations here; narrow side-effect doubles stand in for those API calls. Executor fail-closed behavior is supported by the earlier retained source-bound experiment. No full controller process, App Server, game, GUI, model, OS input, physical release measurement, task effect, or live recovery result is established.

## Result

The baseline exact drain returned sequence 11 and `pending_events=false` while sequence 12 remained queued. The candidate exact `recover_stale_executor_rejection` consumed sequence 12 in one recovery batch, retained stale rejection/no-authority state, required a new decision, and did not retry or emit input. A static AST check also verified that the candidate `execute_segment` calls this recovery helper and routes the stale candidate to discard/next-decision handling. This supports that PR #8643 closes this particular late-event liveness gap in the recovery helper and its source wiring; integrated runtime/live behavior remains unproven.

Source blobs and SHA-256 values are frozen in `FREEZE.json`; raw output is `RUN.stdout.txt`; result and independent audit are retained in `RESULT.json` and `AUDIT.stdout.txt`.

## Reproduction

From the repository root:

```powershell
py -3.13 -B research/doom/v39_final_empty_recovery_integration_a01_20261008/run_experiment.py
py -3.13 -B research/doom/v39_final_empty_recovery_integration_a01_20261008/audit.py
py -3.13 -B -m unittest discover -s research/doom/v39_final_empty_recovery_integration_a01_20261008 -p test_recovery.py -v
```

This is a source-bound integration construction, not an Issue #59 live threat exposure and not product/task completion.
