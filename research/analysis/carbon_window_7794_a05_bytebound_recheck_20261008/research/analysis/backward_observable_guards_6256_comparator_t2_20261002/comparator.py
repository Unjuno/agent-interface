"""Finite comparator analysis for #6256; no runtime or external effects."""
from __future__ import annotations

import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT.parent / "backward_observable_guards_6256_stale_generation_t1_20261002" / "inputs"
MODEL_PATH = INPUT / "MODEL.json"
CANDIDATE_PATH = INPUT / "results" / "t0-01" / "candidate_raw.json"
CUES = ["pixels", "generation_fresh", "already_committed_fresh", "release_available", "termination_bounded", "effect_contract_reliable", "certificate_status"]


def total_correct(outcome: dict, horizon: int) -> bool:
    return (outcome["effect"] == "exact_target_saved" and not outcome["forbidden_prefix"]
            and outcome["release"] == "empty_verified" and outcome["terminated"]
            and outcome["steps"] <= horizon)


def preimage(model: dict) -> set[str]:
    return {s["id"] for s in model["states"] if s["outcomes"] and
            all(total_correct(o, model["horizon_steps"]) for o in s["outcomes"])}


def projection(state: dict, cues: tuple[str, ...]) -> tuple:
    return tuple(state["cues"][c] for c in cues)


def decisions_for_cues(model: dict, safe: set[str], cues: tuple[str, ...]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for state in model["states"]:
        groups.setdefault(projection(state, cues), []).append(state)
    rows = []
    for signature, states in sorted(groups.items(), key=lambda item: repr(item[0])):
        labels = {s["id"] in safe for s in states}
        decision = "ADMIT" if labels == {True} else "REFUSE" if labels == {False} else "UNKNOWN_NOT_OBSERVABLE"
        rows.append({"signature": list(signature), "state_ids": sorted(s["id"] for s in states), "decision": decision})
    return rows


def proposal_local(candidate: dict) -> set[str]:
    """Model a checker that only validates states named in candidate output."""
    rows = candidate.get("outcome_rows", [])
    seen: dict[str, list[bool]] = {}
    for row in rows:
        seen.setdefault(row["state_id"], []).append(bool(row["passes_total_correctness"]))
    return {state_id for state_id, outcomes in seen.items() if outcomes and all(outcomes)}


def dominates(a: dict, b: dict, keys: tuple[str, ...]) -> bool:
    av, bv = [a[k] for k in keys], [b[k] for k in keys]
    return all(x <= y for x, y in zip(av, bv)) and any(x < y for x, y in zip(av, bv))


def cost_frontier(model: dict, safe: set[str]) -> dict:
    verified = [s for s in model["states"] if s["cues"]["certificate_status"] == "verified"]
    # Explicitly illustrative ordinal coordinates; not empirically measured.
    costs = {
        "pixels": {"latency": 1, "tokens": 4, "staleness_risk": 3},
        "generation_fresh": {"latency": 3, "tokens": 1, "staleness_risk": 1},
        "already_committed_fresh": {"latency": 2, "tokens": 2, "staleness_risk": 1},
        "release_available": {"latency": 2, "tokens": 1, "staleness_risk": 2},
        "termination_bounded": {"latency": 1, "tokens": 1, "staleness_risk": 3},
        "effect_contract_reliable": {"latency": 4, "tokens": 2, "staleness_risk": 1},
    }
    rows = []
    eligible = []
    for n in range(len(costs) + 1):
        for subset in itertools.combinations(costs, n):
            ds = decisions_for_cues({"states": verified}, safe.intersection(s["id"] for s in verified), subset)
            if not any(row["decision"] == "UNKNOWN_NOT_OBSERVABLE" for row in ds):
                eligible.append(subset)
                rows.append({"cues": list(subset), "cost": {k: sum(costs[c][k] for c in subset) for k in ("latency", "tokens", "staleness_risk")}})
    frontier = [r for r in rows if not any(dominates(other["cost"], r["cost"], ("latency", "tokens", "staleness_risk")) for other in rows if other is not r)]
    # Weighted sums are a sensitivity demonstration only, never the selection rule.
    weighted = {}
    for label, weights in {"latency_heavy": (5, 1, 1), "token_heavy": (1, 5, 1)}.items():
        ranked = sorted(rows, key=lambda r: sum(w * r["cost"][k] for w, k in zip(weights, ("latency", "tokens", "staleness_risk"))))
        weighted[label] = {"selected_cues": ranked[0]["cues"], "score": sum(w * ranked[0]["cost"][k] for w, k in zip(weights, ("latency", "tokens", "staleness_risk")))}
    return {"coordinate_meaning": "authored ordinal toy costs; lower is preferred; no measured units", "cost_rows": rows, "pareto_frontier": frontier, "weight_sensitivity": weighted}


def run(model: dict, candidate: dict) -> dict:
    exact = preimage(model)
    declared = set(candidate["preimage_state_ids"])
    local = proposal_local(candidate)
    all_state_coverage = {s["id"] for s in model["states"]}
    exhaustive_forward = {s["id"] for s in model["states"] if s["outcomes"] and all(total_correct(o, model["horizon_steps"]) for o in s["outcomes"])}
    verified_ids = {s["id"] for s in model["states"] if s["cues"]["certificate_status"] == "verified"}
    verified_safe = exact & verified_ids
    verified_decisions = decisions_for_cues(model, verified_safe, tuple(CUES))
    pixel_only = decisions_for_cues(model, exact, ("pixels",))
    errors = []
    if declared != exact: errors.append("candidate_preimage_mismatch")
    if exhaustive_forward != exact: errors.append("exhaustive_forward_mismatch")
    if not local.issubset(exact): errors.append("proposal_local_unsafe_admission")
    if local == exact: errors.append("proposal_local_failed_to_illustrate_incompleteness")
    if all_state_coverage != set(model_state_ids := [s["id"] for s in model["states"]]): errors.append("all_state_coverage_incomplete")
    alias = next((r for r in pixel_only if set(r["state_ids"]) == {"ready_simple", "already_committed"}), None)
    if alias is None or alias["decision"] != "UNKNOWN_NOT_OBSERVABLE": errors.append("pixel_alias_not_unknown")
    if not any(set(r["state_ids"]) == {"unobservable_safe_alias", "unobservable_silent_alias"} and r["decision"] == "UNKNOWN_NOT_OBSERVABLE" for r in verified_decisions):
        # Missing-certificate states are outside the verified stratum; check them separately.
        full = decisions_for_cues(model, exact, tuple(CUES))
        if not any("unobservable_safe_alias" in r["state_ids"] and "unobservable_silent_alias" in r["state_ids"] and r["decision"] == "UNKNOWN_NOT_OBSERVABLE" for r in full): errors.append("silent_alias_not_unknown")
    return {
        "decision": "PASS_COMPARATOR_AND_COST_METHOD_SCOPED" if not errors else "FAIL_OR_HOLD",
        "errors": errors,
        "state_count": len(model["states"]),
        "outcome_count": sum(len(s["outcomes"]) for s in model["states"]),
        "exact_universal_preimage": sorted(exact),
        "candidate_preimage_matches": declared == exact,
        "proposal_local_checker": {"semantics": "validate only candidate-listed state/outcome rows", "admitted_state_ids": sorted(local), "omitted_safe_states": sorted(exact - local), "unsafe_admitted_states": sorted(local - exact)},
        "exhaustive_forward_checker": {"semantics": "enumerate every model state and every declared outcome; admit iff all pass", "coverage_state_ids": sorted(all_state_coverage), "admitted_state_ids": sorted(exhaustive_forward), "extensionally_equals_preimage": exhaustive_forward == exact},
        "observation": {"pixel_only_ready_committed": alias, "minimum_verified_stratum_cue_sets": candidate["verified_stratum_minimum_sufficient_cue_sets"], "full_cue_decisions": verified_decisions, "cost_frontier": cost_frontier(model, exact)},
        "scope": "finite authored synthetic model only; ordinal costs are illustrative and not measured"
    }


def main() -> None:
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    print(json.dumps(run(model, candidate), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
