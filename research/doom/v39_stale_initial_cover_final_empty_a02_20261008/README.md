# Stale initial-cover final-empty race A02

## H / T / D / C / U

**H.** On current main, an observation can arrive immediately after the final empty check, leaving an older `latest` and a queued newer row. If the initial V39 cover submit is rejected for that stale sequence, the latest PR #8643 implementation should consume and evaluate the late health crossing, discard the stale cover, and proceed from fresh evidence to a new planner decision.

**T.** Freeze current main `1f81daa690b567a9a049cc75fae8619b2660c343` and latest candidate `a9089f0721d40c53ce982bc751d7a9ed02f9dd73`. Use a deterministic queue that inserts sequence 12 just after the exact baseline drain's final empty result. Invoke the candidate's exact `recover_stale_cover_submission` helper with the resulting queue and a monitor that recognizes the frozen hard-crossing marker. Verify source wiring, returned full observation, invalidation, discarded-cover policy and queue consumption.

**D.** PASS only if baseline returns sequence 11 with no pending events while sequence 12 remains queued, and candidate consumes/evaluates sequence 12, records the hard crossing, discards the stale cover, and does not resubmit it. Otherwise FAIL or HOLD on source mismatch.

**C.** This is a valid deterministic interleaving but not a scheduler-frequency estimate. The monitor is a narrow test double; exact helper logic and source-level main wiring are exercised.

**U.** No full controller process, real monitor implementation, App Server, model, game, GUI, OS input, physical release measurement, or task effect is run. It establishes only the initial-cover recovery helper/wiring under this schedule. Issue #59's live threat exposure and integrated recovery gates remain open.

## Result

Current-main drain missed the late sequence 12 as expected. Latest PR #8643's initial-cover recovery helper consumed sequence 12, evaluated the hard-health crossing, returned sequence 12, and marked the old cover `discarded_until_fresh_plan`; the cover was not resubmitted. The source-wiring audit confirms `main` routes a stale initial-cover ACK through this helper.

Frozen source identities are in `FREEZE.json`; raw output, result and independent checks are retained as `RUN.stdout.txt`, `RESULT.json` and `AUDIT.stdout.txt`. `SHA256SUMS.txt` covers the retained package files.

## Reproduction

From the repository root:

```powershell
py -3.13 -B research/doom/v39_stale_initial_cover_final_empty_a02_20261008/run_experiment.py
py -3.13 -B research/doom/v39_stale_initial_cover_final_empty_a02_20261008/audit.py
py -3.13 -B -m unittest discover -s research/doom/v39_stale_initial_cover_final_empty_a02_20261008 -p test_cover_recovery.py -v
```

This is a source-bound construction, not a live threat exposure or integrated product result.
