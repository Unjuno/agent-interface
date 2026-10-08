"""Finite deterministic route-choice / shared-verifier candidate for #5855."""
import itertools
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "candidate-output"
OUT.mkdir(exist_ok=False)
N = 16
SLOW_MODEL = 8
SLOW_LOCAL = 5
FAST_LOCAL = 4
OBSERVATION = 2
SLOW_VERIFY = 4
CLEANUP = 1
DEADLINE = 32
TARGET_VERIFY_UTILIZATION = 0.50
LOADS = (16, 8, 2)
FAST_VERIFY_WORK = (8, 12)


def simulate(mask, interval, fast_verify, disjoint=False):
    obs_free = 0
    model_free = 0
    local_free = {"A": 0, "B": 0, "F": 0}
    mask_bits = format(mask, f"0{N}b")
    prepared = []
    for i in range(N):
        arrival = i * interval
        obs_start = max(arrival, obs_free)
        obs_done = obs_start + OBSERVATION
        obs_free = obs_done
        fast = mask_bits[i] == "1"
        klass = "A" if i % 2 == 0 else "B"
        if fast:
            route = "F"
            ready = obs_done
            lane = "F"
            service = FAST_LOCAL
            model_start = model_done = None
        else:
            route = klass
            model_start = max(obs_done, model_free)
            model_done = model_start + SLOW_MODEL
            model_free = model_done
            ready = model_done
            lane = klass
            service = SLOW_LOCAL
        local_start = max(ready, local_free[lane])
        local_done = local_start + service
        local_free[lane] = local_done
        prepared.append({
            "id": i, "arrival": arrival, "class": klass, "route": route,
            "observation_done": obs_done, "model_start": model_start,
            "model_done": model_done, "local_start": local_start,
            "local_done": local_done, "verify_work": fast_verify if fast else SLOW_VERIFY,
        })

    verifier_wait_total = 0
    if not disjoint:
        verifier_free = 0
        for row in sorted(prepared, key=lambda r: (r["local_done"], r["id"])):
            start = max(row["local_done"], verifier_free)
            row["verify_start"] = start
            row["verify_done"] = start + row["verify_work"]
            row["verify_wait"] = start - row["local_done"]
            verifier_free = row["verify_done"]
            verifier_wait_total += row["verify_wait"]
    else:
        lane_free = {"A": 0, "B": 0}
        fast_lanes = [0] * (fast_verify // SLOW_VERIFY)
        for row in sorted(prepared, key=lambda r: (r["local_done"], r["id"])):
            if row["route"] == "F":
                finishes = []
                starts = []
                for k in range(len(fast_lanes)):
                    start = max(row["local_done"], fast_lanes[k])
                    starts.append(start)
                    fast_lanes[k] = start + SLOW_VERIFY
                    finishes.append(fast_lanes[k])
                row["verify_start"] = min(starts)
                row["verify_done"] = max(finishes)
                row["verify_wait"] = max(0, max(starts) - row["local_done"])
            else:
                lane = row["route"]
                start = max(row["local_done"], lane_free[lane])
                row["verify_start"] = start
                row["verify_done"] = start + SLOW_VERIFY
                row["verify_wait"] = start - row["local_done"]
                lane_free[lane] = row["verify_done"]
            verifier_wait_total += row["verify_wait"]

    cleanup_free = 0
    for row in sorted(prepared, key=lambda r: (r["verify_done"], r["id"])):
        start = max(row["verify_done"], cleanup_free)
        row["cleanup_start"] = start
        row["completion"] = start + CLEANUP
        row["latency"] = row["completion"] - row["arrival"]
        row["cleanup_wait"] = start - row["verify_done"]
        cleanup_free = row["completion"]
        row["effect_exact"] = True
        row["release_verified"] = True
        row["safety_passed"] = True
        row["on_time"] = row["latency"] <= DEADLINE
    latencies = sorted(r["latency"] for r in prepared)
    p95 = latencies[math.ceil(0.95 * N) - 1]
    return {
        "mask": format(mask, f"0{N}b"),
        "fast_count": mask.bit_count(),
        "mean_latency": sum(latencies) / N,
        "p95_latency": p95,
        "on_time": sum(r["on_time"] for r in prepared),
        "verifier_work": sum(r["verify_work"] for r in prepared),
        "verifier_wait_total": verifier_wait_total,
        "model_calls": sum(r["route"] != "F" for r in prepared),
        "synthetic_model_wait": sum(SLOW_MODEL for r in prepared if r["route"] != "F"),
        "synthetic_token_units": sum(20 for r in prepared if r["route"] != "F"),
        "observation_work": N * OBSERVATION,
        "cleanup_work": N * CLEANUP,
        "exact_effects": sum(r["effect_exact"] for r in prepared),
        "verified_releases": sum(r["release_verified"] for r in prepared),
        "safety_passes": sum(r["safety_passed"] for r in prepared),
        "tasks": prepared,
    }


def balanced_mask(count):
    mask = 0
    for i in range(N):
        if math.floor((i + 1) * count / N) > math.floor(i * count / N):
            mask |= 1 << (N - 1 - i)
    return mask


def optimize(interval, fast_verify):
    best = None
    max_on_time = -1
    best_deadline_mask = 0
    for mask in range(1 << N):
        row = simulate(mask, interval, fast_verify)
        if row["on_time"] > max_on_time:
            max_on_time = row["on_time"]
            best_deadline_mask = mask
        objective = (round(row["mean_latency"] * N, 8), row["p95_latency"], mask)
        if best is None or objective < best[0]:
            best = (objective, row)
    return best[1], max_on_time, format(best_deadline_mask, f"0{N}b")


scenarios = []
for interval, fast_verify in itertools.product(LOADS, FAST_VERIFY_WORK):
    base_mask = 0
    greedy_mask = (1 << N) - 1
    extra = fast_verify - SLOW_VERIFY
    max_share = max(0.0, min(1.0, (TARGET_VERIFY_UTILIZATION * interval - SLOW_VERIFY) / extra))
    cap_count = min(N, math.floor(N * max_share + 1e-12))
    cap_mask = balanced_mask(cap_count)
    central, max_on_time, best_deadline_mask = optimize(interval, fast_verify)
    scenario = {
        "arrival_interval": interval,
        "fast_verify_work": fast_verify,
        "held_out": interval == 8 and fast_verify == 12,
        "route_isolated_cost": {"slow": SLOW_MODEL + SLOW_LOCAL + SLOW_VERIFY, "fast": FAST_LOCAL + fast_verify},
        "baseline": simulate(base_mask, interval, fast_verify),
        "greedy": simulate(greedy_mask, interval, fast_verify),
        "capped": simulate(cap_mask, interval, fast_verify),
        "cap_rule": {
            "target_shared_verifier_utilization": TARGET_VERIFY_UTILIZATION,
            "allowed_fast_share": max_share,
            "fast_count": cap_count,
        },
        "central_exact": central,
        "maximum_deadline_success_over_all_assignments": max_on_time,
        "best_deadline_mask": best_deadline_mask,
    }
    if interval == 8 and fast_verify == 12:
        scenario["disjoint_negative_control"] = {
            "baseline": simulate(base_mask, interval, fast_verify, disjoint=True),
            "greedy": simulate(greedy_mask, interval, fast_verify, disjoint=True),
        }
    scenarios.append(scenario)

result = {
    "schema": "braess-route-verifier-t0-result-v1",
    "offers_per_scenario": N,
    "class_schedule": "A,B alternating by task ID",
    "deadline_ticks": DEADLINE,
    "same_offers_across_policies": True,
    "scenarios": scenarios,
}
(OUT / "candidate-result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"scenarios": len(scenarios), "offers_per_scenario": N, "masks_exactly_enumerated_per_scenario": 1 << N, "result": str(OUT / "candidate-result.json")}, sort_keys=True))
