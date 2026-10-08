"""Independent reconstruction from candidate input, choices, raw, and oracle."""
import json
import sys
from pathlib import Path


def main():
    workload, choices, raw, oracle = [json.loads(Path(p).read_text()) for p in sys.argv[1:5]]
    cases = {r["case_id"]: r for r in workload["cases"]}
    truth = oracle["truth_by_case_id"]
    choice_rows = {r["case_id"]: r for r in choices["rows"]}
    raw_rows = {(r["case_id"], r["arm"]): r for r in raw["rows"]}
    errors, reconstructed, observed = [], 0, {"GENERIC": [], "WITNESS": []}
    if len(cases) != 132 or len(raw["rows"]) != 264 or len(raw_rows) != 264:
        errors.append("row_count_or_duplicate")
    for case_id, case in cases.items():
        chosen = choice_rows.get(case_id)
        expected_truth = truth.get(case_id)
        if chosen is None or expected_truth is None:
            errors.append("missing_case:" + case_id)
            continue
        generic_expected = min(case["admissible_actions"])
        preferred = [a for a in case["admissible_actions"]
                     if case["predicted_witness_survival"][a]
                     and case["preservation_cost"][a] <= case["cost_budget"]]
        witness_expected = (min(preferred, key=lambda a: (case["preservation_cost"][a], a))
                            if preferred and not case["preexisting_witness"] else generic_expected)
        if chosen["generic_action"] != generic_expected:
            errors.append("generic_policy_mismatch:" + case_id)
        if chosen["witness_action"] != witness_expected:
            errors.append("witness_policy_mismatch:" + case_id)
        for arm, action_key in (("GENERIC", "generic_action"), ("WITNESS", "witness_action")):
            action = chosen[action_key]
            if action not in case["admissible_actions"]:
                errors.append("inadmissible:" + case_id)
                continue
            predicted = case["predicted_witness_survival"][action]
            action_cost = case["preservation_cost"][action]
            next_state = expected_truth["next_state_by_action"][action]
            survives = expected_truth["witness_survival_by_action"][action] or case["preexisting_witness"]
            completion = survives
            exp = {"case_id": case_id, "topology": case["topology"], "arm": arm,
                   "action": action, "next_state": next_state, "witness_observed": survives,
                   "decision": "COMPLETE" if completion else "UNKNOWN_WITNESS_LOST",
                   "commit": expected_truth["correct_commit_by_next_state"][next_state] if completion else None,
                   "authority_grants": 0}
            got = raw_rows.get((case_id, arm))
            if got != exp:
                errors.append("raw_mismatch:" + case_id + ":" + arm)
            else:
                reconstructed += 1
            if arm == "WITNESS" and not case["preexisting_witness"]:
                predicted_affordable = predicted and action_cost <= case["cost_budget"]
                if not predicted_affordable and action != min(case["admissible_actions"]):
                    errors.append("budget_or_prediction_fallback:" + case_id)
                if completion and not survives:
                    errors.append("false_completion:" + case_id)
            observed[arm].append((completion, action, case["topology"], case["preexisting_witness"],
                                  case["preservation_cost"][action], case["predicted_witness_survival"][action], survives))
    primary = {arm: sum(x[0] for x in rows if not x[3]) for arm, rows in observed.items()}
    correct_within = sum(1 for x in observed["WITNESS"]
                         if not x[3] and x[4] <= 1 and x[5] and x[6])
    topology_signatures = {}
    for name, graph in oracle["topologies"].items():
        indegree = {node: 0 for node in graph["states"]}
        outdegree = []
        for node, edges in graph["edges"].items():
            outdegree.append(len(edges))
            for target in edges.values():
                indegree[target] += 1
        topology_signatures[name] = (len(graph["states"]), tuple(sorted(outdegree)),
                                     tuple(sorted(indegree.values())))
    if len(set(topology_signatures.values())) != len(topology_signatures):
        errors.append("topology_signatures_not_distinct")
    report = {"allocation": workload["allocation"], "cases": len(cases), "rows_reconstructed": reconstructed,
              "errors": errors, "primary_completion_without_preexisting_witness": primary,
              "witness_correct_model_within_budget_completions": correct_within,
              "topology_signatures": {k: [v[0], list(v[1]), list(v[2])] for k, v in topology_signatures.items()},
              "authority_grants": sum(r["authority_grants"] for r in raw["rows"]),
              "verdict": "PASS_METHOD_SCOPED" if not errors and reconstructed == 144 else "FAIL_AUDIT"}
    Path(sys.argv[5]).write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
