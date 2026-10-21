# V39 stale rejection → source refresh → planner input A01

Date: 2026-10-09 (Asia/Tokyo)
Hypothesis: Issue #59, fresh-source recovery after stale Executor rejection.

## H/T/D/C/U

- **H:** After the current V39 controller discards an action rejected by the Executor sequence fence, a queued full observation with unavailable ammo can be passed through the production bounded `refresh_source` path. Only a newer observation with a verified, lease-matched empty release and paired health/ammo should reach the next planner turn.
- **T:** Run the exact `test_stale_executor_rejection_replans_from_new_image_and_hud` against current-main controller/admission/guard/source-refresh functions. Include a negative control whose release token mismatches. Run the full V39 controller and pending-observation-drain suites normally and under `python -O`.
- **D:** PASS if sequence 5 stale-rejection recovery leaves the V3 guard closed without authority; source refresh submits observe with expected sequence 5, accepts sequence 6 only with a verified empty release and the same intent token, and `begin_model_turn` receives the new image, health 60 and ammo 8. The mismatched-token case must refuse. No input action may be admitted by this experiment.
- **C:** This deterministic fake transport validates composition of production functions; it does not exercise the live session writer, App Server, game, or scheduler timing.
- **U:** No model, live game, GUI, OS input, physical release, threat response, task progress, or MAP01 completion is tested. A positive construction result is not a live-control efficacy claim.

## Reproduction

From `research/doom`, set `PYTHONPATH` to include `research/live_control`, then run:

```powershell
python -m unittest -v test_map01_overlap_controller_v39.Map01V39CoastTests.test_stale_executor_rejection_replans_from_new_image_and_hud
python -O -m unittest -v test_map01_overlap_controller_v39.Map01V39CoastTests.test_stale_executor_rejection_replans_from_new_image_and_hud
python -m unittest -v test_map01_overlap_controller_v39
python -O -m unittest -v test_map01_overlap_controller_v39
python -m unittest -v test_map01_v39_pending_observation_drain
python -O -m unittest -v test_map01_v39_pending_observation_drain
```

Exact stdout, stderr, and exit codes are retained in `results/`. `FREEZE.json` records the source commit, source hashes, Git blobs, and Python environment. `audit.py` independently verifies source identity, all six test outcomes, and the positive/negative case assertions.
