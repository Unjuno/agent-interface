from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

from candidate import (
    EFFECT, YIELD, INACTIVE,
    run_redecide_every_cycle,
    run_cached_supervisor_only,
    run_cached_action_guard,
)
from oracle import exact_reference, guarded_cache_reference, regime_at
from scenario import ACTION_TIMES_MS, HARD, AMBIG, VALID, generate_scenarios, scenario_to_dict

FORMAL_SEED = 2026091801
FORMAL_SCENARIOS = 250_000


def _new_metrics():
    return Counter({
        "effects": 0,
        "valid_effects": 0,
        "hard_invalid_effects": 0,
        "ambiguous_effects": 0,
        "yields": 0,
        "inactive": 0,
        "semantic_decisions": 0,
    })


def _score(metrics: Counter, s, result: dict):
    metrics["semantic_decisions"] += result["semantic_decisions"]
    for t, d in zip(ACTION_TIMES_MS, result["decisions"]):
        r = regime_at(s, t)
        if d.disposition == EFFECT:
            metrics["effects"] += 1
            if r == VALID:
                metrics["valid_effects"] += 1
            elif r == HARD:
                metrics["hard_invalid_effects"] += 1
            elif r == AMBIG:
                metrics["ambiguous_effects"] += 1
        elif d.disposition == YIELD:
            metrics["yields"] += 1
        elif d.disposition == INACTIVE:
            metrics["inactive"] += 1


def run_experiment(count: int, seed: int) -> dict:
    metrics = {
        "redecide_every_cycle": _new_metrics(),
        "cached_supervisor_only": _new_metrics(),
        "cached_action_guard": _new_metrics(),
    }
    mismatch = Counter()
    representatives = []
    pre_hard_guard_valid_mismatch = 0

    for s in generate_scenarios(count, seed):
        ref = run_redecide_every_cycle(s)
        sup = run_cached_supervisor_only(s)
        guard = run_cached_action_guard(s)
        ref_oracle = exact_reference(s)
        guard_oracle = guarded_cache_reference(s)

        ref_disp = [x.disposition for x in ref["decisions"]]
        sup_disp = [x.disposition for x in sup["decisions"]]
        guard_disp = [x.disposition for x in guard["decisions"]]

        mismatch["redecide_vs_oracle"] += sum(a != b for a, b in zip(ref_disp, ref_oracle))
        mismatch["guard_vs_oracle"] += sum(a != b for a, b in zip(guard_disp, guard_oracle))

        first_hard_action = next(t for t in ACTION_TIMES_MS if regime_at(s, t) == HARD)
        for t, rd, gd in zip(ACTION_TIMES_MS, ref_disp, guard_disp):
            if t < first_hard_action and regime_at(s, t) == VALID and rd != gd:
                pre_hard_guard_valid_mismatch += 1

        _score(metrics["redecide_every_cycle"], s, ref)
        _score(metrics["cached_supervisor_only"], s, sup)
        _score(metrics["cached_action_guard"], s, guard)

        if len(representatives) < 12:
            stale_slots = [
                t for t, d in zip(ACTION_TIMES_MS, sup_disp)
                if d == EFFECT and regime_at(s, t) == HARD
            ]
            ambiguous_slots = [
                t for t, d in zip(ACTION_TIMES_MS, sup_disp)
                if d == EFFECT and regime_at(s, t) == AMBIG
            ]
            if stale_slots or ambiguous_slots:
                representatives.append({
                    "scenario": scenario_to_dict(s),
                    "supervisor_stale_hard_effect_slots_ms": stale_slots,
                    "supervisor_ambiguous_effect_slots_ms": ambiguous_slots,
                    "guard": guard_disp,
                    "supervisor": sup_disp,
                })

    serial_metrics = {k: dict(v) for k, v in metrics.items()}
    decision = "FAIL_ACTION_GUARD"
    g = serial_metrics["cached_action_guard"]
    s = serial_metrics["cached_supervisor_only"]
    r = serial_metrics["redecide_every_cycle"]
    if mismatch["redecide_vs_oracle"] or mismatch["guard_vs_oracle"]:
        decision = "FAIL_ACTION_GUARD"
    elif g["hard_invalid_effects"] or g["ambiguous_effects"]:
        decision = "FAIL_ACTION_GUARD"
    elif s["hard_invalid_effects"] <= 0:
        decision = "HOLD_NO_DISCRIMINATOR"
    elif pre_hard_guard_valid_mismatch != 0:
        decision = "FAIL_ACTION_GUARD"
    elif g["semantic_decisions"] != count or r["semantic_decisions"] != count * len(ACTION_TIMES_MS):
        decision = "FAIL_ACTION_GUARD"
    else:
        decision = "PASS_DECISION_POLICY_ACTION_GUARD_SCOPED"

    return {
        "task": "DECISION-POLICY-CACHE-ACTION-GUARD-R0-20260918-001",
        "formal_seed": seed,
        "scenario_count": count,
        "action_slots_per_scenario": len(ACTION_TIMES_MS),
        "candidate_oracle_mismatch": dict(mismatch),
        "pre_hard_valid_guard_reference_mismatch": pre_hard_guard_valid_mismatch,
        "metrics": serial_metrics,
        "representative_supervisor_failures": representatives,
        "authority_grants": 0,
        "formal_invocations": 1,
        "reruns": 0,
        "decision": decision,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--formal", action="store_true")
    p.add_argument("--count", type=int, default=10_000)
    p.add_argument("--seed", type=int, default=99117)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.formal:
        count, seed = FORMAL_SCENARIOS, FORMAL_SEED
    else:
        count, seed = args.count, args.seed
    t0 = time.perf_counter_ns()
    result = run_experiment(count, seed)
    result["wall_ns"] = time.perf_counter_ns() - t0
    payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
    args.out.write_text(payload, encoding="utf-8")
    print(json.dumps({
        "decision": result["decision"],
        "count": count,
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "wall_ns": result["wall_ns"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
