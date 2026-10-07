"""A11 deterministic transition: receipt survives only on arrival at witness state."""
import json
import sys
from pathlib import Path


def main():
    workload, choices, oracle = [json.loads(Path(p).read_text()) for p in sys.argv[1:4]]
    cases = {c["case_id"]: c for c in workload["cases"]}
    truth = oracle["truth_by_case_id"]
    rows = []
    for selected in choices["rows"]:
        c, t = cases[selected["case_id"]], truth[selected["case_id"]]
        for arm, key in (("GENERIC", "generic_action"), ("WITNESS", "witness_action")):
            action = selected[key]
            next_state = t["next_state_by_action"][action]
            survives = next_state == t["witness_state"] or c["preexisting_witness"]
            rows.append({"case_id": c["case_id"], "topology": c["topology"], "arm": arm,
                         "action": action, "next_state": next_state,
                         "witness_observed": survives,
                         "decision": "COMPLETE" if survives else "UNKNOWN_WITNESS_LOST",
                         "commit": t["correct_commit_by_next_state"][next_state] if survives else None,
                         "authority_grants": 0})
    Path(sys.argv[4]).write_text(json.dumps({"allocation": workload["allocation"], "rows": rows},
                                            sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
