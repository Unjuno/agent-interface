# V39 soft-event routing A01/A02 — scoped current-main result

## Finding

Against frozen main `f60752d0fb71595363a80977636ca74c1fd10b21`, the production V39 paired monitor receives a synthetic advancing typed observation with health unchanged at 100 and ammo decreasing from 46 to 37. The real `ObservableSignalGuard` class marks that ammo change `SOFT_CHANGED` (`hard_minimum=1`, `keep_existing_policy=true`) and `DoomCoverSignalPairMonitor.observe()` returns `None`. The planner stub had already received its single prompt before the observation and received no in-flight update. The independent source/raw reconciliation confirms that V39 captures `prior_soft_event_summary` before `begin_model_turn`, polls the monitor while the planner future is pending, then stores the current decision's soft event only after `future.result()`. The summary is consequently available to a later planner turn, not the already-running one.

Scoped disposition: `PASS_SOURCE_RAW_RECONSTRUCTION; FAIL_NO_INDEPENDENT_IN_FLIGHT_FEEDBACK` for this one synthetic ammo change. In this path, that soft event alone does not invalidate the current policy or prompt a cover switch while inference is pending. This is a feedback-routing boundary result, not a live efficacy result.

## Audit history

The A01 candidate ran once and produced `RESULT.json`. Its first auditor exited 1 because it expected `planner.await_turn(...)` to appear as a call; current source passes `planner.await_turn` as a method reference to `ThreadPoolExecutor.submit`. The candidate raw and auditor failure remain in A01 unchanged. A02 is a separately frozen auditor repair that reads the exact A01 result SHA and independently parses the frozen source; it did not rerun the candidate and passed five raw/source checks.

## Scope and remaining gates

No model, game, GUI, OS input, container, or live allocation ran. This does not test real image/OCR timing, whether a particular ammo drop is useful, active model uptake on a later turn, per-key release, bounded recovery, progress, or task outcome. It does not change the unassigned private live-game lane or close Issue #59's current-main live threat-exposure gate. Pair this boundary with a later matched exposure measuring current visible evidence, stop/switch, verified release, useful feedback, bounded recovery, ammo/progress, and outcome once an authorized lane exists.

Reproduction commands and first-failure history are colocated in the A01 and A02 directories. Each freeze records the exact base, source hashes, invocation limit, and scope.

## Subsequent current-main identity check

After execution, `origin/main` advanced to `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5` and still reports r138. The controller Git blob is still `cdf61eec2c030d7456b34a58907e9c43d5d72084` and the production guard blob is still `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`, identical to the frozen f60752d inputs. This leaves the source-composition finding applicable to the latest main source bytes without relabeling or rerunning the f60752d candidate.

## A03 — next-turn delivery follow-up

A03 then fed the unchanged A01 event through the actual V39 `latest_soft_event_summary` and `begin_model_turn` functions with a stub planner. The summary retained ammo source 46/current 37, hard floor 1, sequence 2, and `prior_cover_preserved`; the following prompt contained that exact serialized summary and current ammo 37. The A03 raw/source auditor passed five checks. Disposition: `PASS_NEXT_TURN_DELIVERY`; the A01/A02 finding that the event does not reach the in-flight planner remains unchanged. This confirms delayed availability, not that the model uses the signal well or that a next-turn change succeeds.

The main branch advanced again after A03 to `23174f45a8b802d94fbcdeda6e1ebbca28acc801`. The controller Git blob remains `cdf61eec2c030d7456b34a58907e9c43d5d72084`, the production guard remains `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`, and the current-goal document still states r138. The frozen A01/A02/A03 source identities therefore remain present; none of the candidate runs was relabeled or repeated.
