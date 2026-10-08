"""Independent A11 reconstruction from truth, input, selected actions, and raw."""
import json
import sys
from pathlib import Path


def main():
    workload, choices, raw, oracle = [json.loads(Path(p).read_text()) for p in sys.argv[1:5]]
    cases = {c["case_id"]: c for c in workload["cases"]}
    truths, selected = oracle["truth_by_case_id"], {r["case_id"]: r for r in choices["rows"]}
    raw_map = {(r["case_id"], r["arm"]): r for r in raw["rows"]}
    errors, reconstructed = [], 0
    counts = {arm: {g: 0 for g in ("prior", "correct_affordable", "correct_over_budget", "misspecified")}
              for arm in ("GENERIC", "WITNESS")}
    topology_patterns = {}
    for name, graph in oracle["topologies"].items():
        topology_patterns[name] = tuple(
            (state, tuple(sorted(action for action, dest in edges.items()
                                 if dest == graph["witness_state"])))
            for state, edges in sorted(graph["edges"].items()))
    if len(cases) != 132 or len(raw["rows"]) != 264 or len(raw_map) != 264:
        errors.append("row_count_or_duplicate")
    if len(set(topology_patterns.values())) != 3:
        errors.append("topology_witness_patterns_not_distinct")
    for cid, c in cases.items():
        choice, t = selected.get(cid), truths.get(cid)
        if choice is None or t is None:
            errors.append("missing_identity:" + cid)
            continue
        actions = c["admissible_actions"]
        actual = {a: t["next_state_by_action"][a] == t["witness_state"] for a in actions}
        predicted = c["predicted_witness_survival"]
        correct = predicted == actual
        generic = min(actions)
        eligible = [a for a in actions if predicted[a] and c["preservation_cost"][a] <= c["cost_budget"]]
        witness = (min(eligible, key=lambda a: (c["preservation_cost"][a], a))
                   if eligible and not c["preexisting_witness"] else generic)
        if choice != {"case_id": cid, "generic_action": generic, "witness_action": witness}:
            errors.append("policy_mismatch:" + cid)
        group = ("prior" if c["preexisting_witness"] else
                 "correct_affordable" if correct and c["preservation_cost"]["action-b"] <= 1 else
                 "correct_over_budget" if correct else "misspecified")
        for arm, action in (("GENERIC", generic), ("WITNESS", witness)):
            dest = t["next_state_by_action"][action]
            survives = dest == t["witness_state"] or c["preexisting_witness"]
            expected = {"case_id": cid, "topology": c["topology"], "arm": arm,
                        "action": action, "next_state": dest, "witness_observed": survives,
                        "decision": "COMPLETE" if survives else "UNKNOWN_WITNESS_LOST",
                        "commit": t["correct_commit_by_next_state"][dest] if survives else None,
                        "authority_grants": 0}
            if raw_map.get((cid, arm)) != expected:
                errors.append("raw_reconstruction:" + cid + ":" + arm)
            else:
                reconstructed += 1
            counts[arm][group] += int(survives)
            if not survives and raw_map.get((cid, arm), {}).get("decision") == "COMPLETE":
                errors.append("unsupported_completion:" + cid + ":" + arm)
    authority = sum(r.get("authority_grants", -1) for r in raw["rows"])
    if authority != 0:
        errors.append("authority_nonzero")
    if counts["WITNESS"]["correct_affordable"] <= counts["GENERIC"]["correct_affordable"]:
        errors.append("no_correct_affordable_increment")
    if counts["WITNESS"]["misspecified"] != 0:
        errors.append("misspecified_policy_false_completion")
    if counts["WITNESS"]["correct_over_budget"] != counts["GENERIC"]["correct_over_budget"]:
        errors.append("over_budget_not_generic_fallback")
    if counts["WITNESS"]["prior"] != counts["GENERIC"]["prior"]:
        errors.append("prior_witness_control_mismatch")
    report = {"allocation": workload["allocation"], "cases": len(cases),
              "rows_reconstructed": reconstructed, "errors": errors,
              "completion_by_arm_and_stratum": counts,
              "topology_witness_patterns": {k: [[s, list(a)] for s, a in v]
                                             for k, v in topology_patterns.items()},
              "authority_grants": authority,
              "verdict": "PASS_TOPOLOGY_DEPENDENT_WITNESS_SCOPED"
              if not errors and reconstructed == 264 else "FAIL_AUDIT"}
    Path(sys.argv[5]).write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
