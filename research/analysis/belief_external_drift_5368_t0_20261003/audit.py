"""Independent raw-only audit; does not import candidate.py or runner.py."""
from __future__ import annotations

import json
from pathlib import Path


def reconstruct(case: dict, contracts: dict) -> tuple[list[str], str, str]:
    item = case["input"]
    if item.get("transition_complete") is not True:
        return [], "UNKNOWN_MODEL", "transition_coverage_unverified"
    relation = item["transition_relation"]
    belief = set(item["initial_belief"])
    if not belief or not belief.issubset(relation):
        return [], "UNKNOWN_MODEL", "initial_belief_outside_model"
    for _step in range(item["elapsed_steps"]):
        expanded: set[str] = set()
        for state in belief:
            if state not in relation or not relation[state]:
                return [], "UNKNOWN_MODEL", "transition_successor_missing"
            expanded.update(relation[state])
        if not expanded or not expanded.issubset(relation):
            return [], "UNKNOWN_MODEL", "reachable_state_outside_model"
        belief = expanded
    observation = item.get("observation")
    if (
        observation is not None
        and observation.get("source_bound") is True
        and observation.get("generation") == item["current_generation"]
    ):
        narrowed = belief.intersection(observation.get("states", []))
        if not narrowed:
            return [], "UNKNOWN_MODEL", "fresh_observation_contradicts_model"
        belief = narrowed
    safe_states = set(contracts[item["action"]]["safe_states"])
    if belief.issubset(safe_states):
        return sorted(belief), "ADMIT", "all_reachable_states_safe"
    return sorted(belief), "YIELD_UNSAFE_OR_AMBIGUOUS", "unsafe_state_remains_possible"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def candidate_row_errors(case: dict, row: dict | None, expected: tuple[list[str], str, str], contracts: dict) -> list[str]:
    case_id = case["id"]
    if row is None:
        return [f"candidate_missing:{case_id}"]
    reachable, expected_decision, expected_reason = expected
    errors = []
    if set(row) != {"id", "reachable", "decision", "reason"}:
        errors.append(f"candidate_unexpected_fields:{case_id}")
    if row.get("id") != case_id:
        errors.append(f"candidate_id_mismatch:{case_id}")
    if row.get("reachable") != reachable:
        errors.append(f"reachable_mismatch:{case_id}")
    if row.get("decision") != expected_decision:
        errors.append(f"decision_mismatch:{case_id}")
    if row.get("reason") != expected_reason:
        errors.append(f"reason_mismatch:{case_id}")
    actual = case["truth"]["actual_state"]
    safe_states = set(contracts[case["input"]["action"]]["safe_states"])
    if row.get("decision") == "ADMIT" and actual not in safe_states:
        errors.append(f"unsafe_admission:{case_id}:{actual}")
    return errors


def mutation_controls(
    rows_by_id: dict[str, dict],
    cases_by_id: dict[str, dict],
    expected_by_id: dict[str, tuple[list[str], str, str]],
    contracts: dict,
) -> list[dict]:
    controls = [
        ("omit_hidden_redirect", "hidden_redirect_without_observation", {"decision": "ADMIT", "reachable": ["A"]}),
        ("trust_stale_observation", "stale_generation_observation_ignored", {"decision": "ADMIT", "reachable": ["A"]}),
        ("admit_unknown_transition_model", "unknown_transition_alphabet", {"decision": "ADMIT", "reachable": ["A"]}),
        ("accept_observation_outside_complete_model", "fresh_observation_contradicts_complete_model", {"decision": "ADMIT", "reachable": ["B"]}),
    ]
    results = []
    for name, case_id, mutated in controls:
        row = dict(rows_by_id[case_id])
        row.update(mutated)
        detected = bool(candidate_row_errors(cases_by_id[case_id], row, expected_by_id[case_id], contracts))
        results.append({"name": name, "detected": detected})
    return results


def main() -> None:
    root = Path(__file__).resolve().parent
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    raw = read_jsonl(root / "formal_raw.jsonl")
    sticky = read_jsonl(root / "sticky_baseline.jsonl")
    age = read_jsonl(root / "age_baseline.jsonl")
    errors: list[str] = []
    expected_by_id: dict[str, tuple[list[str], str, str]] = {}
    for case in fixture["cases"]:
        expected_by_id[case["id"]] = reconstruct(case, fixture["action_contracts"])
    for path_name, rows in (("candidate", raw), ("sticky", sticky), ("age", age)):
        if len(rows) != len(fixture["cases"]):
            errors.append(f"{path_name}_row_count:{len(rows)}!={len(fixture['cases'])}")
        ids = [row.get("id") for row in rows]
        if len(ids) != len(set(ids)):
            errors.append(f"{path_name}_duplicate_id")
    candidate_by_id = {row.get("id"): row for row in raw}
    sticky_by_id = {row.get("id"): row for row in sticky}
    age_by_id = {row.get("id"): row for row in age}
    details = []
    for case in fixture["cases"]:
        case_id = case["id"]
        reachable, expected_decision, expected_reason = expected_by_id[case_id]
        declared = case["expected"]
        if declared != {"reachable": reachable, "decision": expected_decision}:
            errors.append(f"fixture_expected_label_mismatch:{case_id}")
        row = candidate_by_id.get(case_id)
        errors.extend(candidate_row_errors(case, row, expected_by_id[case_id], fixture["action_contracts"]))
        sticky_row = sticky_by_id.get(case_id)
        if sticky_row is None:
            errors.append(f"sticky_missing:{case_id}")
        else:
            expected_sticky = "ADMIT" if set(case["input"]["initial_belief"]).issubset(set(fixture["action_contracts"][case["input"]["action"]]["safe_states"])) else "YIELD"
            if sticky_row != {"id": case_id, "decision": expected_sticky}:
                errors.append(f"sticky_mismatch:{case_id}")
        age_row = age_by_id.get(case_id)
        if age_row is None:
            errors.append(f"age_missing:{case_id}")
        else:
            expected_age = "YIELD" if case["input"]["elapsed_steps"] > 0 else "ADMIT"
            if age_row != {"id": case_id, "decision": expected_age}:
                errors.append(f"age_mismatch:{case_id}")
        details.append({"id": case_id, "reachable": reachable, "expected": expected_decision, "actual": (row or {}).get("decision")})

    candidate_admissions = sum(row.get("decision") == "ADMIT" for row in raw)
    unsafe_admissions = sum(
        row.get("decision") == "ADMIT"
        and case["truth"]["actual_state"] not in set(fixture["action_contracts"][case["input"]["action"]]["safe_states"])
        for case in fixture["cases"]
        for row in [candidate_by_id.get(case["id"], {})]
    )
    sticky_false_admissions = sum(
        row.get("decision") == "ADMIT" and expected_by_id[row.get("id")][1] != "ADMIT"
        for row in sticky
    )
    age_safe_control_refusals = sum(
        age_by_id.get(case["id"], {}).get("decision") == "YIELD" and expected_by_id[case["id"]][1] == "ADMIT"
        for case in fixture["cases"]
    )
    cases_by_id = {case["id"]: case for case in fixture["cases"]}
    mutations = mutation_controls(candidate_by_id, cases_by_id, expected_by_id, fixture["action_contracts"])
    if sum(not item["detected"] for item in mutations):
        errors.append("mutation_control_escaped")
    admitted_safe_controls = sum(
        candidate_by_id.get(case["id"], {}).get("decision") == "ADMIT" and expected_by_id[case["id"]][1] == "ADMIT"
        for case in fixture["cases"]
    )
    if unsafe_admissions != 0:
        errors.append("unsafe_admissions_nonzero")
    if sticky_false_admissions == 0:
        errors.append("sticky_baseline_no_counterexample")
    if age_safe_control_refusals == 0:
        errors.append("age_baseline_no_safe_control_refusal")
    if admitted_safe_controls < 2:
        errors.append("candidate_safe_controls_not_retained")
    result = {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "rows_expected": len(fixture["cases"]),
        "rows_received": len(raw),
        "candidate_admissions": candidate_admissions,
        "unsafe_admissions": unsafe_admissions,
        "sticky_false_admissions": sticky_false_admissions,
        "age_safe_control_refusals": age_safe_control_refusals,
        "admitted_safe_controls": admitted_safe_controls,
        "mutation_controls": mutations,
        "details": details,
        "errors": errors,
        "authority_or_effect_emitted": False,
    }
    with (root / "audit.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
