"""Frozen finite policy simulator; no agent, model, or interface calls."""
import itertools
import json
from pathlib import Path


def masks(horizon, count):
    return [list(xs) for xs in itertools.combinations(range(horizon), count)]


def simulate(inp, scenario, onset, b_slots, policy):
    n = inp["horizon"]
    b_ok = scenario["b_eligible"]
    failures_shared = scenario["shared_failure"]
    reactive = policy in {"best_reactive", "context_gated", "bounded_mixture"}
    unresolved_run = 0
    switched = False
    last_b = None
    queue = 0
    rows = []
    for t in range(n):
        active = onset > 0 and t + 1 >= onset
        planned = "A"
        if policy == "bounded_mixture" and b_ok and t in b_slots:
            planned = "B"
        elif policy == "context_gated" and scenario["kind"] == "observable" and active and b_ok:
            planned = "B"
        elif policy == "oracle" and active and b_ok and not failures_shared:
            planned = "B"
        elif policy == "conservative_default":
            planned = "A"
        if not b_ok:
            planned = "A"
        route = "B" if switched and b_ok else planned
        if route == "B" and not b_ok:
            route = "A"

        result = "SUCCESS"
        effect = "EXACT"
        latency = inp["direct_cost"][route]
        b_ready_before = True
        if scenario["kind"] == "queue":
            latency += queue
            queue = max(0, queue - 1) + (2 if route == "B" else 0)
        if route == "B" and scenario["kind"] == "idle_decay":
            age = t if last_b is None else t - last_b
            b_ready_before = age < 4
            if not b_ready_before:
                result, effect = "YIELD_UNREADY", "NO_EFFECT"
            else:
                last_b = t
        elif route == "B":
            last_b = t
        if active and (route == "A" or failures_shared):
            result, effect = "UNRESOLVED", "NO_EFFECT"
        if result in {"UNRESOLVED", "YIELD_UNREADY"}:
            unresolved_run += 1
        else:
            unresolved_run = 0
        if reactive and unresolved_run >= inp["switch_detection_consecutive_unresolved"]:
            switched = True
        rows.append({
            "task": t + 1, "planned_route": planned, "route": route,
            "regime_active_truth": active, "result": result, "effect": effect,
            "direct_cost": inp["direct_cost"][route], "latency": latency,
            "b_ready_before": b_ready_before, "queue_after": queue,
            "switched_after": switched
        })
    unresolved = sum(r["result"] != "SUCCESS" for r in rows)
    return {
        "scenario": scenario["id"], "onset": onset, "b_slots": b_slots,
        "policy": policy, "rows": rows, "offered": n,
        "verified": n - unresolved, "unresolved": unresolved,
        "tail_failure": unresolved >= inp["tail_unresolved_threshold"],
        "forbidden_effects": sum(r["effect"] == "FORBIDDEN" for r in rows),
        "direct_cost_total": sum(r["direct_cost"] for r in rows),
        "latency_total": sum(r["latency"] for r in rows)
    }


def run(inp):
    all_masks = masks(inp["horizon"], inp["mixture_b_slots_per_session"])
    blocks = []
    for s in inp["scenarios"]:
        schedules = all_masks if s["b_eligible"] else [[]]
        for onset in s["onsets"]:
            for slots in schedules:
                for policy in inp["policies"]:
                    blocks.append(simulate(inp, s, onset, slots, policy))
    return {"allocation_id": inp["allocation_id"], "blocks": blocks}


if __name__ == "__main__":
    p = Path(__file__).with_name("input.json")
    result = run(json.loads(p.read_text(encoding="utf-8")))
    target = p.with_name("candidate.json")
    target.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"WROTE {target.name}: {len(result['blocks'])} complete session-policy records")
