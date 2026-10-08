"""Independent raw-output auditor; intentionally does not import candidate.py."""
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).parent


def reconstruct(inp, block):
    scenario = next(x for x in inp["scenarios"] if x["id"] == block["scenario"])
    policy, onset = block["policy"], block["onset"]
    n, slots = inp["horizon"], set(block["b_slots"])
    failed_run, switched, last_b, queue = 0, False, None, 0
    expected = []
    for idx in range(n):
        active = onset != 0 and idx + 1 >= onset
        if policy == "bounded_mixture":
            intent = "B" if idx in slots and scenario["b_eligible"] else "A"
        elif policy == "context_gated" and scenario["kind"] == "observable" and active and scenario["b_eligible"]:
            intent = "B"
        elif policy == "oracle" and active and scenario["b_eligible"] and not scenario["shared_failure"]:
            intent = "B"
        else:
            intent = "A"
        actual = "B" if switched and scenario["b_eligible"] else intent
        ready = True
        outcome, effect = "SUCCESS", "EXACT"
        elapsed = inp["direct_cost"][actual]
        if scenario["kind"] == "queue":
            elapsed += queue
            queue = max(0, queue - 1) + (2 if actual == "B" else 0)
        if actual == "B" and scenario["kind"] == "idle_decay":
            idle = idx if last_b is None else idx - last_b
            ready = idle < 4
            if ready:
                last_b = idx
            else:
                outcome, effect = "YIELD_UNREADY", "NO_EFFECT"
        elif actual == "B":
            last_b = idx
        if active and (actual == "A" or scenario["shared_failure"]):
            outcome, effect = "UNRESOLVED", "NO_EFFECT"
        failed_run = failed_run + 1 if outcome != "SUCCESS" else 0
        if policy in {"best_reactive", "context_gated", "bounded_mixture"} and failed_run >= inp["switch_detection_consecutive_unresolved"]:
            switched = True
        expected.append({
            "task": idx + 1, "planned_route": intent, "route": actual,
            "regime_active_truth": active, "result": outcome, "effect": effect,
            "direct_cost": inp["direct_cost"][actual], "latency": elapsed,
            "b_ready_before": ready, "queue_after": queue,
            "switched_after": switched
        })
    misses = sum(r["result"] != "SUCCESS" for r in expected)
    return {
        "scenario": scenario["id"], "onset": onset, "b_slots": block["b_slots"],
        "policy": policy, "rows": expected, "offered": n,
        "verified": n - misses, "unresolved": misses,
        "tail_failure": misses >= inp["tail_unresolved_threshold"],
        "forbidden_effects": 0,
        "direct_cost_total": sum(r["direct_cost"] for r in expected),
        "latency_total": sum(r["latency"] for r in expected)
    }


def aggregate(blocks, scenario, policy, field):
    selected = [b for b in blocks if b["scenario"] == scenario and b["policy"] == policy]
    return sum(b[field] for b in selected) / len(selected) if selected else None


def audit(inp, result):
    expected = [reconstruct(inp, b) for b in result["blocks"]]
    exact = expected == result["blocks"]
    blocks = result["blocks"]
    keys = [(b["scenario"], b["onset"], tuple(b["b_slots"]), b["policy"]) for b in blocks]
    all_rows = all(len(b["rows"]) == inp["horizon"] and b["offered"] == inp["horizon"] for b in blocks)
    no_forbidden = all(b["forbidden_effects"] == 0 and all(r["effect"] != "FORBIDDEN" for r in b["rows"]) for b in blocks)
    hidden_base_tail = aggregate(blocks, "hidden_exogenous", "best_reactive", "tail_failure")
    hidden_mix_tail = aggregate(blocks, "hidden_exogenous", "bounded_mixture", "tail_failure")
    hidden_mix_cost = aggregate(blocks, "hidden_exogenous", "bounded_mixture", "direct_cost_total") / inp["horizon"]
    observable_context = aggregate(blocks, "observable_exogenous", "context_gated", "tail_failure")
    observable_mix = aggregate(blocks, "observable_exogenous", "bounded_mixture", "tail_failure")
    shared_base = aggregate(blocks, "shared_failure", "best_reactive", "unresolved")
    shared_mix = aggregate(blocks, "shared_failure", "bounded_mixture", "unresolved")
    stable_a = aggregate(blocks, "stable_a_dominant", "best_reactive", "unresolved")
    stable_mix = aggregate(blocks, "stable_a_dominant", "bounded_mixture", "unresolved")
    idle_safe = all(
        row["b_ready_before"] is False and row["result"] == "YIELD_UNREADY" and row["effect"] == "NO_EFFECT"
        for b in blocks if b["scenario"] == "b_idle_decay"
        for row in b["rows"] if row["route"] == "B" and not row["b_ready_before"]
    )
    no_b = all(row["route"] != "B" for b in blocks if b["scenario"] == "no_eligible_b" for row in b["rows"])
    conservative_no_b = all(row["route"] != "B" for b in blocks if b["policy"] == "conservative_default" for row in b["rows"])
    conservative_justified = inp["route_completion_lower_bound"]["B"] < inp["conservative_completion_floor"]
    queue_seen = any(row["queue_after"] > 0 for b in blocks if b["scenario"] == "route_carryover" for row in b["rows"])
    denominators = len(keys) == len(set(keys)) and all(b["offered"] == inp["horizon"] for b in blocks)

    # Negative mutation controls: regime truth leak, a missing assigned task,
    # false readiness for a decayed route, and silent obligation reset.
    leak = next(b for b in blocks if b["scenario"] == "hidden_exogenous" and b["onset"] == 1 and b["policy"] == "context_gated")
    leak_mutant = json.loads(json.dumps(leak))
    leak_mutant["rows"][0]["planned_route"] = "B"
    missing_mutant = json.loads(json.dumps(next(b for b in blocks if b["scenario"] == "hidden_exogenous")))
    missing_mutant["rows"].pop()
    stale = next((b, r) for b in blocks if b["scenario"] == "b_idle_decay" for r in b["rows"] if r["route"] == "B" and not r["b_ready_before"])
    stale_mutant = json.loads(json.dumps(stale[0]))
    stale_mutant["rows"][stale[1]["task"] - 1]["b_ready_before"] = True
    reset_mutant = json.loads(json.dumps(next(b for b in blocks if b["scenario"] == "hidden_exogenous" and b["policy"] == "bounded_mixture")))
    reset_mutant["unresolved"] = 0

    gates = {
        "candidate_raw_exactly_reconstructed": exact,
        "all_offered_tasks_retained": all_rows and denominators,
        "hidden_shock_tail_reduced": hidden_mix_tail < hidden_base_tail,
        "hidden_mixture_within_mean_cost_budget": hidden_mix_cost <= inp["mean_cost_budget_per_task"],
        "observable_regime_context_policy_not_worse_than_mixture": observable_context <= observable_mix,
        "shared_failure_control_no_mixture_gain": shared_mix == shared_base,
        "stable_a_dominant_control_no_completion_gain": stable_mix == stable_a == 0,
        "idle_decay_never_claims_stale_b_ready": idle_safe,
        "no_eligible_b_never_called": no_b,
        "conservative_default_respects_completion_floor": conservative_no_b and conservative_justified,
        "route_induced_queue_carryover_retained": queue_seen,
        "hard_safety_gate_never_bypassed": no_forbidden,
        "mutation_regime_leak_rejected": reconstruct(inp, leak_mutant) != leak_mutant,
        "mutation_missing_assigned_task_rejected": reconstruct(inp, missing_mutant) != missing_mutant,
        "mutation_stale_ready_rejected": reconstruct(inp, stale_mutant) != stale_mutant,
        "mutation_silent_obligation_reset_rejected": reconstruct(inp, reset_mutant) != reset_mutant
    }
    return {
        "disposition": "METHOD_PASS_SCOPED" if all(gates.values()) else "METHOD_FAIL",
        "block_count": len(blocks), "unique_sessions": len(keys), "gates": gates,
        "metrics": {
            "hidden_best_reactive_tail_fraction": hidden_base_tail,
            "hidden_mixture_tail_fraction": hidden_mix_tail,
            "hidden_mixture_mean_direct_cost_per_task": hidden_mix_cost,
            "hidden_best_reactive_mean_unresolved": aggregate(blocks, "hidden_exogenous", "best_reactive", "unresolved"),
            "hidden_mixture_mean_unresolved": aggregate(blocks, "hidden_exogenous", "bounded_mixture", "unresolved"),
            "observable_context_tail_fraction": observable_context,
            "observable_mixture_tail_fraction": observable_mix,
            "shared_failure_best_reactive_mean_unresolved": shared_base,
            "shared_failure_mixture_mean_unresolved": shared_mix,
            "stable_best_reactive_mean_unresolved": stable_a,
            "stable_mixture_mean_unresolved": stable_mix,
            "conservative_route_b_lower_bound": inp["route_completion_lower_bound"]["B"],
            "declared_completion_floor": inp["conservative_completion_floor"]
        },
        "mutations_tested": ["regime_truth_leak", "omit_offered_task", "claim_stale_b_ready", "silently_reset_unresolved_obligation"]
    }


if __name__ == "__main__":
    inp = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "candidate.json").read_text(encoding="utf-8"))
    report = audit(inp, raw)
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["disposition"])
