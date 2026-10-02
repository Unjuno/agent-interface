"""Independent raw-only checker for the frozen Issue #6256 finite model."""
from __future__ import annotations

import itertools
import json
from pathlib import Path


def oracle_accepts(row: dict, horizon: int, required_effect: str, forbidden: set[str], release: str) -> bool:
    return bool(
        row.get("terminated") is True
        and isinstance(row.get("steps"), int)
        and row["steps"] <= horizon
        and row.get("effect") == required_effect
        and isinstance(row.get("forbidden_prefix"), list)
        and not any(tag in forbidden for tag in row["forbidden_prefix"])
        and row.get("release") == release
    )


def audit(model: dict, candidate: dict) -> dict:
    errors: list[str] = []
    states = model.get("states", [])
    cue_names = model.get("permitted_cues", [])
    preimage = set()
    accepted_rows = []
    for state in states:
        outcomes = state.get("outcomes", [])
        flags = [oracle_accepts(o, model["horizon_steps"], model["required_effect"], set(model["forbidden_prefix_tags"]), model["required_release"]) for o in outcomes]
        if outcomes and all(flags):
            preimage.add(state["id"])
        for outcome, flag in zip(outcomes, flags):
            accepted_rows.append((state["id"], outcome["id"], flag))
    expected_rows = [
        {"state_id": sid, "outcome_id": oid, "passes_total_correctness": ok}
        for sid, oid, ok in accepted_rows
    ]
    reported_rows = [
        {"state_id": row.get("state_id"), "outcome_id": row.get("outcome", {}).get("id"), "passes_total_correctness": row.get("passes_total_correctness")}
        for row in candidate.get("outcome_rows", [])
    ]
    if expected_rows != reported_rows:
        errors.append("OUTCOME_ORACLE_DISAGREEMENT")
    if sorted(preimage) != candidate.get("preimage_state_ids"):
        errors.append("PREIMAGE_DISAGREEMENT")

    groups: dict[tuple, list[dict]] = {}
    for state in states:
        if set(state.get("cues", {})) != set(cue_names):
            errors.append(f"CUE_SCHEMA:{state.get('id')}")
            continue
        sig = tuple(state["cues"][name] for name in cue_names)
        groups.setdefault(sig, []).append(state)
    decisions = []
    for sig, group in sorted(groups.items(), key=lambda item: repr(item[0])):
        membership = {s["id"] in preimage for s in group}
        expected = "ADMIT" if membership == {True} else "REFUSE" if membership == {False} else "UNKNOWN_NOT_OBSERVABLE"
        decisions.append({"signature": list(sig), "state_ids": [s["id"] for s in group], "decision": expected})
    if decisions != candidate.get("full_cue_decisions"):
        errors.append("OBSERVATION_PARTITION_DISAGREEMENT")

    verified = [s for s in states if s["cues"]["certificate_status"] == "verified"]
    sufficient = []
    for width in range(len(cue_names) + 1):
        for subset in itertools.combinations(cue_names, width):
            cells: dict[tuple, list[dict]] = {}
            for state in verified:
                cells.setdefault(tuple(state["cues"][cue] for cue in subset), []).append(state)
            if all(len({s["id"] in preimage for s in cell}) == 1 for cell in cells.values()):
                sufficient.append(list(subset))
        if sufficient:
            break
    if sufficient != candidate.get("verified_stratum_minimum_sufficient_cue_sets"):
        errors.append("MINIMUM_CUE_SET_DISAGREEMENT")
    global_uniform = all(len({s["id"] in preimage for s in cell}) == 1 for cell in groups.values())
    if global_uniform != candidate.get("full_model_global_sufficient_cue_set_exists"):
        errors.append("GLOBAL_IDENTIFIABILITY_DISAGREEMENT")

    mutations = {
        "existential_success_accepts_unreliable_state": any(
            oracle_accepts(o, model["horizon_steps"], model["required_effect"], set(model["forbidden_prefix_tags"]), model["required_release"])
            for o in next(s for s in states if s["id"] == "unreliable_effect_contract")["outcomes"]
        ),
        "drop_release_gate_accepts_release_blocked": all(
            o["terminated"] and o["steps"] <= model["horizon_steps"] and o["effect"] == model["required_effect"] and not set(o["forbidden_prefix"]).intersection(model["forbidden_prefix_tags"])
            for o in next(s for s in states if s["id"] == "release_blocked")["outcomes"]
        ),
        "drop_termination_gate_accepts_late_completion": all(
            o["effect"] == model["required_effect"] and o["release"] == model["required_release"] and not set(o["forbidden_prefix"]).intersection(model["forbidden_prefix_tags"])
            for o in next(s for s in states if s["id"] == "late_completion")["outcomes"]
        ),
        "pixels_only_merges_ready_and_duplicate": len({s["id"] in preimage for s in states if s["cues"]["pixels"] == "save_visible"}) > 1,
        "drop_forbidden_prefix_accepts_duplicate": all(o["effect"] == model["required_effect"] and o["release"] == model["required_release"] and o["terminated"] and o["steps"] <= model["horizon_steps"] for o in next(s for s in states if s["id"] == "already_committed")["outcomes"]),
    }
    if not all(mutations.values()):
        errors.append("MUTATION_CONTROL_NOT_SENSITIVE")
    if "ready_complex" not in preimage or "ready_complex" in candidate.get("overstrong_guard_state_ids", []):
        errors.append("OVERSTRONG_GUARD_CONTROL_NOT_SENSITIVE")
    hidden_pair = [s for s in states if s["id"] in {"unobservable_safe_alias", "unobservable_silent_alias"}]
    if len({tuple(s["cues"][cue] for cue in cue_names) for s in hidden_pair}) != 1 or {s["id"] in preimage for s in hidden_pair} != {False, True}:
        errors.append("UNOBSERVABLE_ALIAS_FIXTURE_INVALID")

    return {
        "decision": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "independent_preimage_state_ids": sorted(preimage),
        "state_count": len(states),
        "outcome_count": len(accepted_rows),
        "verified_stratum_minimum_sufficient_cue_sets": sufficient,
        "full_model_global_sufficient_cue_set_exists": global_uniform,
        "mutation_controls": mutations,
        "unobservable_alias_decision": "UNKNOWN_NOT_OBSERVABLE",
        "scope": "finite declared simulator only; no real GUI, authority, or product claim"
    }


def main() -> None:
    directory = Path(__file__).resolve().parent
    model = json.loads((directory / "MODEL.json").read_text(encoding="utf-8"))
    candidate = json.loads((directory / "results" / "t0-01" / "candidate_raw.json").read_text(encoding="utf-8"))
    result = audit(model, candidate)
    out = directory / "results" / "t0-01" / "audit_raw.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "error_count": len(result["errors"]), "preimage": result["independent_preimage_state_ids"]}, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
