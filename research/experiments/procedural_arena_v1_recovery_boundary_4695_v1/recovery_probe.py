import json
from engine import BenchmarkSession, EpisodeSpec, generate_episode, solve_with_oracle_for_test

SEEDS = (4695001, 4695002, 4695003, 4695004, 4695005)
rows = []
for seed in SEEDS:
    generated = generate_episode(seed, 0.35, suite="full")
    recovery = next(s for s in generated.stages if s.kind == "recovery")
    spec = EpisodeSpec(generated.schema, generated.seed, "full", generated.difficulty, (recovery,))
    p = recovery.payload
    target = next(o for o in p["objects"] if o["object_id"] == p["target_id"])
    before = (target["x"], target["y"])
    after = (p["recovery_x"], p["recovery_y"])
    movement = ((before[0]-after[0])**2 + (before[1]-after[1])**2)**0.5
    stale = BenchmarkSession(spec)
    stale.click(*before)
    stale.click(*before)
    fresh = BenchmarkSession(spec)
    first = fresh._object_by_id(p["target_id"])
    fresh.click(first.x, first.y)
    moved = fresh._object_by_id(p["target_id"])
    moved_xy = (moved.x, moved.y)
    fresh.click(*moved_xy)
    oracle = BenchmarkSession(spec)
    solve_with_oracle_for_test(oracle)
    rows.append({
      "seed": seed, "movement_px": round(movement, 6),
      "stale": {"success": stale.success, "recovery_events": stale.metrics.recovery_events, "recovery_successes": stale.metrics.recovery_successes},
      "reacquire": {"success": fresh.success, "recovery_events": fresh.metrics.recovery_events, "recovery_successes": fresh.metrics.recovery_successes, "state_matches": all(abs(a-b)<1e-9 for a,b in zip(moved_xy, after))},
      "oracle": {"success": oracle.success, "recovery_events": oracle.metrics.recovery_events, "recovery_successes": oracle.metrics.recovery_successes},
    })
print(json.dumps({"schema":"arena-recovery-boundary-v1","rows":rows}, sort_keys=True, separators=(",",":")))
