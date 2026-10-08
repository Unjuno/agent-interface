# Issue #59 — retained V39 visible-threat invalidation timing (post hoc)

## H / T / D / C / U

**H.** A retained V39 live trace may show a visible hostile during a long pending planner turn, a health decrease crossing its authored floor, and whether that invalidation cancels cover before the planner reaches terminal state.

**T.** Reconstruct decision 5 from exact pinned report/event Git blobs; bind full observation PNGs for sequences 166, 200, 217, and 218; compare their in-memory typed signals, model-wait timing, health guard outcome, cover terminal, and planner terminal. Independently recompute the timing and event ordering from the same pinned raw sources.

**D.** Count one positive mechanism observation only if the retained frame sequence shows the threat in view during the pending wait, the health guard reports `HARD_INVALIDATED`, the result precedes planner terminal, the cover is cancelled with verified empty release, and the planner answer is ineligible. Treat the measured margin as descriptive, not a reliability threshold.

**C.** This is a post hoc reconstruction of one older V39 live run. Damage source, repeatability, causal benefit, and survival effect are not identified. The visual review is a single analyst’s reading; the audit verifies source identity and frame/event binding, not enemy classification.

**U.** This run predates the current-main paired health/ammo cover monitor and current per-key input-owner changes. Its runtime monitor mode was `authored_policy_guard`, and its final empty-release receipt is not per-key release evidence. It does not establish bounded recovery, independently useful task feedback, causal combat effectiveness, or MAP01 exit. A fresh current-main exposure remains required.

## Result

In decision 5, the model wait lasted 8.916 s. Sequence 166 began from a source observation with health 61 and ammo 40; no hostile is visible in that frame. A hostile is visible by sequence 200 while the model is still pending. At sequences 200 and 217 health reads 51, equal to the admitted hard floor; sequence 218 reads health 48 and ammo 37 with the hostile still visible.

The last at-floor frame (sequence 217) and first below-floor frame (218) are 339.601 ms apart. Sequence 218 was captured 8.723 s into the wait. The monitor received it 133.690 ms after capture and evaluated `HARD_INVALIDATED/below_hard_minimum` 22.335 ms after monitor receipt. The outcome evaluation preceded planner terminal by 37.051 ms. The matched cover was cancelled; terminal release verified empty keys and buttons; the planner ended interrupted, its answer was ineligible, and the plan was not admitted. The trace’s independent episode score is one kill, no death, no MAP01 exit.

This is a positive historical mechanism observation: a visible on-screen hostile and worsening HUD state coincided with a health guard that cancelled cover before the pending planner terminal. It does not prove the hostile caused the health loss. The 37 ms margin is narrow and comes from one post hoc sample, so it cannot establish robust timing.

## Current-main boundary

The run’s frozen source commit is `b67fc4f33a28f9cea1c4c6cb2d95a470f6be53f3`, an ancestor of the main head rechecked for this analysis, `ff13baf57d5f1c12819151e668b92cb6db4a7c1c`. The frozen `session_map01_v15.py` matches that main head, but the controller, typed-observation producer, and input owner have different blob identities. In particular, this run records `authored_policy_guard`; current main pairs health and ammo for fire cover. The trace therefore informs the current-main experiment but does not replace it.

The private game lane remains unassigned in current-goal R139. No live allocation was added, no runtime code was changed, and no new game/model/GUI/input execution occurred.

## Provenance and reproduction

`FREEZE.json` pins the report, 634-row event log, fixture, four full observation PNGs, and runtime-source comparisons. The candidate and independent auditor read Git blobs directly and verify blob IDs and SHA-256 values. `VISUAL_REVIEW.md` records the frame reading. Reproduce from the repository root with:

```sh
python3 -B research/doom/v39_invalidation_latency_59_p02_20261005/analyze.py --output /tmp/v39-invalidation-59-p02-replay-result-20261005.json
python3 -B research/doom/v39_invalidation_latency_59_p02_20261005/audit.py --result /tmp/v39-invalidation-59-p02-replay-result-20261005.json --output /tmp/v39-invalidation-59-p02-replay-audit-20261005.json
```

The source traces remain unchanged. This standard-library reanalysis did not launch a container or rerun the live allocation.
