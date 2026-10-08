#!/usr/bin/env python3
"""Independent exact replay of authored Markov worlds and scheduler outcomes."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
import sys
from pathlib import Path

H = 4
CAP = 3
SENTINEL = "mandatory-focus-lease-cancel-v1"
FALSE_CAP = Fraction(3, 2)
SETUPS = {
    "independent_train": ([Fraction(9, 10), Fraction(1, 20), Fraction(3, 10)], [Fraction(2, 5), Fraction(1, 20), Fraction(3, 10)], [0, 1, 0], [3, 2, 1], True, True, True),
    "independent_heldout": ([Fraction(9, 10), Fraction(1, 10), Fraction(1, 5)], [Fraction(2, 5), Fraction(1, 10), Fraction(1, 4)], [0, 1, 1], [3, 2, 1], True, True, True),
    "coupled_common_cause": ([Fraction(1, 3)] * 3, [Fraction(1, 3)] * 3, [0, 0, 0], [3, 2, 1], False, True, True),
    "mode_switch": ([Fraction(1, 4)] * 3, [Fraction(1, 4)] * 3, [0, 1, 0], [3, 2, 1], True, False, True),
    "unknown_transition": ([Fraction(1, 3)] * 3, [Fraction(1, 3)] * 3, [0, 1, 0], [3, 2, 1], True, True, False),
}


def textfrac(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def step_belief(p, up, down):
    return p * (1 - down) + (1 - p) * up


def world_iterator(case, up, down, start):
    if case == "coupled_common_cause":
        for trajectory in itertools.product((0, 1), repeat=H):
            prior = start[0]
            weight = Fraction(1)
            for bit in trajectory:
                p1 = up[0] if prior == 0 else 1 - down[0]
                weight *= p1 if bit else 1 - p1
                prior = bit
            if weight:
                yield tuple(trajectory for _ in start), weight
        return
    per_stream = []
    for j, first in enumerate(start):
        stream_rows = []
        for trajectory in itertools.product((0, 1), repeat=H):
            prior, weight = first, Fraction(1)
            for tick, bit in enumerate(trajectory):
                u, d = (Fraction(3, 4), Fraction(1, 4)) if case == "mode_switch" and tick >= 2 else (up[j], down[j])
                p1 = u if prior == 0 else 1 - d
                weight *= p1 if bit else 1 - p1
                prior = bit
            if weight:
                stream_rows.append((trajectory, weight))
        per_stream.append(stream_rows)
    for combination in itertools.product(*per_stream):
        yield tuple(z[0] for z in combination), _product([z[1] for z in combination])


def _product(values):
    result = Fraction(1)
    for value in values:
        result *= value
    return result


def action_for(kind, belief, age, tick, weights):
    n = len(age)
    if kind == "cyclic":
        return tick % n
    if kind == "aoi":
        best = 0
        for i in range(1, n):
            if age[i] > age[best]:
                best = i
        return best
    if kind == "entropy":
        best = 0
        for i in range(1, n):
            if belief[i] * (1 - belief[i]) > belief[best] * (1 - belief[best]):
                best = i
        return best
    overdue = [i for i in range(n) if age[i] >= CAP - 1]
    if overdue:
        best = overdue[0]
        for i in overdue[1:]:
            if age[i] > age[best]:
                best = i
        return best
    best = 0
    for i in range(1, n):
        if weights[i] * belief[i] > weights[best] * belief[best]:
            best = i
    return best


def replay(case, kind, up, down, start, weights, flags):
    independent, stationary, known = flags
    okay = independent and stationary and known
    effective = "cyclic" if kind == "belief_value" and not okay else kind
    initial_belief = [step_belief(Fraction(x), u, d) for x, u, d in zip(start, up, down)]
    misses = false_count = Fraction(0)
    action_weight = [Fraction(0)] * len(start)
    max_age = worlds = Fraction(0)
    digest = hashlib.sha256()
    for truth, world_prob in world_iterator(case, up, down, start):
        worlds += 1
        belief = initial_belief.copy()
        age = [0] * len(start)
        per_world_miss = per_world_false = Fraction(0)
        per_world_age = 0
        actions = []
        for tick in range(H):
            chosen = action_for(effective, belief, age, tick, weights)
            actions.append(chosen)
            for source, value in enumerate(truth):
                bit = value[tick]
                if source != chosen:
                    if bit:
                        per_world_miss += weights[source]
                    if (belief[source] >= Fraction(9, 10) and bit == 0) or (belief[source] <= Fraction(1, 10) and bit == 1):
                        per_world_false += 1
            age = [0 if i == chosen else a + 1 for i, a in enumerate(age)]
            per_world_age = max(per_world_age, *age)
            belief = [step_belief(Fraction(truth[i][tick]) if i == chosen else belief[i], *( (Fraction(3, 4), Fraction(1, 4)) if case == "mode_switch" and tick >= 2 else (up[i], down[i]) )) for i in range(len(start))]
            action_weight[chosen] += world_prob
        misses += world_prob * per_world_miss
        false_count += world_prob * per_world_false
        max_age = max(max_age, per_world_age)
        row = {"states": truth, "probability": textfrac(world_prob), "actions": actions, "weighted_miss": textfrac(per_world_miss), "false_confidence": textfrac(per_world_false), "max_starvation": per_world_age}
        digest.update(json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    return {
        "declared_policy": kind,
        "effective_policy": effective,
        "index_claim": False,
        "expected_weighted_misses": textfrac(misses),
        "expected_false_confidence": textfrac(false_count) if okay else None,
        "max_starvation": int(max_age),
        "captures": H,
        "action_mass": [textfrac(x) for x in action_weight],
        "enumerated_worlds": int(worlds),
        "probability_mass": "1",
        "world_result_sha256": digest.hexdigest(),
        "mandatory_sentinel": SENTINEL,
    }


def result(rows):
    errors = []
    if len(rows) != len(SETUPS):
        errors.append("case_count")
    seen = set()
    for row in rows:
        name = row.get("case_id")
        if name not in SETUPS or name in seen:
            errors.append(f"case_identity:{name}")
            continue
        seen.add(name)
        up, down, start, weights, independent, stationary, known = SETUPS[name]
        flags = (independent, stationary, known)
        supported = independent and stationary and known
        wanted_policies = {"cyclic", "aoi", "entropy", "belief_value"} if supported else {"cyclic", "belief_value"}
        policy_rows = {p.get("declared_policy"): p for p in row.get("policies", [])}
        if set(policy_rows) != wanted_policies:
            errors.append(f"policy_set:{name}")
        if row.get("stream_count") != 3 or row.get("horizon") != H or row.get("weights") != weights:
            errors.append(f"design:{name}")
        if row.get("support_flags") != {"independent": independent, "stationary_mode": stationary, "known_transition": known}:
            errors.append(f"support_flags:{name}")
        if row.get("fallback_required") is not (not supported):
            errors.append(f"fallback_required:{name}")
        if row.get("opportunity_definition") != "synthetic_evaluator_truth_state_equals_one" or row.get("observation_boundary") != "policy_receives_selected_stream_state_only" or row.get("oracle_truth_scope") != "auditor_only":
            errors.append(f"truth_boundary:{name}")
        analytic_p = Fraction(0)
        beliefs = []
        ranks = []
        for _ in range(3):
            analytic_p = step_belief(analytic_p, Fraction(9, 10), Fraction(2, 5))
            beliefs.append(textfrac(analytic_p))
            ranks.append(textfrac(analytic_p * (1 - analytic_p)))
        expected_analytic = {"beliefs": beliefs, "entropy_rank_exact": ranks, "age2_gt_age3": Fraction(ranks[1]) > Fraction(ranks[2])}
        if row.get("analytic_entropy_control") != expected_analytic:
            errors.append(f"analytic_entropy:{name}")
        for policy in wanted_policies:
            expected = replay(name, policy, up, down, start, weights, flags)
            if policy_rows.get(policy) != expected:
                errors.append(f"replay_mismatch:{name}:{policy}")
    if seen != set(SETUPS):
        errors.append("missing_case")
    held = next((r for r in rows if r.get("case_id") == "independent_heldout"), None)
    if held:
        p = {x.get("declared_policy"): x for x in held.get("policies", [])}
        belief = p.get("belief_value", {})
        selected_misses = Fraction(belief.get("expected_weighted_misses", "999"))
        if selected_misses >= Fraction(p["entropy"]["expected_weighted_misses"]) or any(
            selected_misses > Fraction(p[x]["expected_weighted_misses"]) for x in ("cyclic", "aoi")
        ):
            errors.append("heldout_miss_improvement")
        if belief.get("max_starvation", 999) > CAP:
            errors.append("heldout_starvation_cap")
        if Fraction(belief.get("expected_false_confidence", "999")) > FALSE_CAP:
            errors.append("heldout_false_confidence_cap")
    for case in ("coupled_common_cause", "mode_switch", "unknown_transition"):
        if case in seen:
            p = {x.get("declared_policy"): x for x in next(r for r in rows if r.get("case_id") == case).get("policies", [])}
            belief_policy, cyclic_policy = p.get("belief_value", {}), p.get("cyclic", {})
            same_outcome = {k: v for k, v in belief_policy.items() if k != "declared_policy"} == {
                k: v for k, v in cyclic_policy.items() if k != "declared_policy"
            }
            if belief_policy.get("effective_policy") != "cyclic" or belief_policy.get("index_claim") is not False or not same_outcome:
                errors.append(f"fallback:{case}")
    return {"disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "cases": len(rows), "errors": errors}


def main(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    outcome = result(rows)
    print(json.dumps(outcome, sort_keys=True, indent=2))
    return 1 if outcome["errors"] else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python audit.py RAW.jsonl")
    raise SystemExit(main(sys.argv[1]))
