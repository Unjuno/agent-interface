"""Finite deterministic environment step; truth input is not mounted/isolation-protected."""
import json
import sys
from pathlib import Path


def main():
    workload = json.loads(Path(sys.argv[1]).read_text())
    choices = json.loads(Path(sys.argv[2]).read_text())
    oracle = json.loads(Path(sys.argv[3]).read_text())
    cases = {row["case_id"]: row for row in workload["cases"]}
    truths = oracle["truth_by_case_id"]
    rows = []
    for choice in choices["rows"]:
        case = cases[choice["case_id"]]
        truth = truths[choice["case_id"]]
        for arm, key in (("GENERIC", "generic_action"), ("WITNESS", "witness_action")):
            action = choice[key]
            next_state = truth["next_state_by_action"][action]
            survives = truth["witness_survival_by_action"][action] or case["preexisting_witness"]
            rows.append({"case_id": case["case_id"], "topology": case["topology"],
                         "arm": arm, "action": action, "next_state": next_state,
                         "witness_observed": survives,
                         "decision": "COMPLETE" if survives else "UNKNOWN_WITNESS_LOST",
                         "commit": truth["correct_commit_by_next_state"][next_state] if survives else None,
                         "authority_grants": 0})
    Path(sys.argv[4]).write_text(json.dumps({"allocation": workload["allocation"], "rows": rows},
                                            sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
