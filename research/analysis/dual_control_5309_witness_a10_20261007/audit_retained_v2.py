"""Read-only successor audit of immutable A10 choices/raw; never runs candidate."""
import json
import sys
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text())


def main():
    workload, choices, raw, oracle = map(read, sys.argv[1:5])
    case_map = {r["case_id"]: r for r in workload["cases"]}
    truth_map = oracle["truth_by_case_id"]
    choice_map = {r["case_id"]: r for r in choices["rows"]}
    raw_map = {(r["case_id"], r["arm"]): r for r in raw["rows"]}
    errors = []
    completed = {"GENERIC": {}, "WITNESS": {}}
    expected_n = len(case_map)
    if expected_n != 132 or len(choice_map) != expected_n:
        errors.append("case_count_or_identity")
    if len(raw["rows"]) != 2 * expected_n or len(raw_map) != 2 * expected_n:
        errors.append("raw_count_or_duplicate")

    for cid, case in case_map.items():
        choice, truth = choice_map.get(cid), truth_map.get(cid)
        if choice is None or truth is None:
            errors.append("missing_identity:" + cid)
            continue
        actions = case["admissible_actions"]
        generic = min(actions)
        eligible = [a for a in actions if case["predicted_witness_survival"][a]
                    and case["preservation_cost"][a] <= case["cost_budget"]]
        witness = (min(eligible, key=lambda a: (case["preservation_cost"][a], a))
                   if eligible and not case["preexisting_witness"] else generic)
        if choice != {"case_id": cid, "generic_action": generic, "witness_action": witness}:
            errors.append("policy_reconstruction:" + cid)
        prediction_correct = all(case["predicted_witness_survival"][a] ==
                                 truth["witness_survival_by_action"][a] for a in actions)
        group = ("prior_witness" if case["preexisting_witness"] else
                 "correct_affordable" if prediction_correct and
                 case["preservation_cost"]["action-b"] <= case["cost_budget"] else
                 "correct_over_budget" if prediction_correct else "misspecified")
        for arm, selected in (("GENERIC", generic), ("WITNESS", witness)):
            if selected not in actions:
                errors.append("inadmissible:" + cid + ":" + arm)
                continue
            next_state = truth["next_state_by_action"][selected]
            has_witness = (truth["witness_survival_by_action"][selected]
                           or case["preexisting_witness"])
            complete = bool(has_witness)
            expected = {"case_id": cid, "topology": case["topology"], "arm": arm,
                        "action": selected, "next_state": next_state,
                        "witness_observed": has_witness,
                        "decision": "COMPLETE" if complete else "UNKNOWN_WITNESS_LOST",
                        "commit": truth["correct_commit_by_next_state"][next_state] if complete else None,
                        "authority_grants": 0}
            if raw_map.get((cid, arm)) != expected:
                errors.append("transition_effect_or_decision:" + cid + ":" + arm)
            completed[arm][group] = completed[arm].get(group, 0) + int(complete)

    signatures = {}
    for name, graph in oracle["topologies"].items():
        indegree = {node: 0 for node in graph["states"]}
        outdegree = []
        for edges in graph["edges"].values():
            outdegree.append(len(edges))
            for dest in edges.values():
                indegree[dest] += 1
        signatures[name] = [len(graph["states"]), sorted(outdegree), sorted(indegree.values())]
    if len({json.dumps(x, sort_keys=True) for x in signatures.values()}) != 3:
        errors.append("graph_families_not_distinct")
    authority = sum(row.get("authority_grants", -1) for row in raw["rows"])
    if authority != 0:
        errors.append("authority_nonzero")
    expected_groups = {"GENERIC": {"prior_witness": 66, "correct_affordable": 0,
                                   "correct_over_budget": 0, "misspecified": 0},
                       "WITNESS": {"prior_witness": 66, "correct_affordable": 22,
                                   "correct_over_budget": 0, "misspecified": 0}}
    if completed != expected_groups:
        errors.append("stratum_result_mismatch")
    result = {"allocation": workload["allocation"], "audit_version": "retained-v2",
              "cases": expected_n, "raw_rows": len(raw["rows"]),
              "completed_by_arm_and_stratum": completed, "topology_signatures": signatures,
              "authority_grants": authority, "errors": errors,
              "verdict": "PASS_RETAINED_RAW_RECONSTRUCTION" if not errors else "FAIL_RETAINED_AUDIT"}
    Path(sys.argv[5]).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
