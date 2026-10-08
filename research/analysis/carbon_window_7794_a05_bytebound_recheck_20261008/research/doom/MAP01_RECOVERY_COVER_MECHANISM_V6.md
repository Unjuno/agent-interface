# MAP01 bounded-recovery mechanism v6

Status: **CONSTRUCTION FROZEN AFTER V5 PLANNER-WINDOW INVALIDATION.**

V5 completed six arms and its frozen audit returned `PASS_MECHANISM_ONLY`, but post-run boundary inspection invalidated that result: all three coast windows were about 3.605 s while recovery windows were about 0.601–0.615 s. The nominal/frozen planner delay is 600 ms. The runner sampled `planner_end_ns` only after fallback cancellation and an optional `input_released` wait of up to 3 s; coast supplied no such release event, so cleanup latency contaminated only that arm.

V5 is retained and is not reclassified as mechanism PASS. It will not be rerun.

V6 preserves the V4/V5 fixture, action, guard, authority, measurement algorithm, scorer contract and decision thresholds. It retains V5's non-destructive event waiting and changes only the planner-end boundary: immediately after the fixed-delay event fires, request the session runtime clock and freeze that receipt as planner end **before** any fallback cancellation/release cleanup. Each arm summary records `end_boundary_phase=immediately_after_delay_before_fallback_cleanup`; the V6 audit hard-fails if any arm lacks that marker.

H/T/D/C/U remain the V4 mechanism hypothesis and thresholds. Even a V6 `PASS_MECHANISM_ONLY` establishes only continuity under this zero-model fixed MAP01 block; it does not establish useful gameplay benefit or frontier-model efficacy.
