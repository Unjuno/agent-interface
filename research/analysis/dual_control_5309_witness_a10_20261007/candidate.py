"""Advisory chooser. Reads candidate input only; this is not OS-isolated."""
import json
import sys
from pathlib import Path


def choose(case, witness_aware):
    actions = case["admissible_actions"]
    if not witness_aware or case["preexisting_witness"]:
        return min(actions)
    candidates = [a for a in actions if case["predicted_witness_survival"][a]
                  and case["preservation_cost"][a] <= case["cost_budget"]]
    return min(candidates, key=lambda a: (case["preservation_cost"][a], a)) if candidates else min(actions)


def main():
    source = Path(sys.argv[1]).read_bytes()
    workload = json.loads(source)
    rows = []
    for case in workload["cases"]:
        rows.append({"case_id": case["case_id"], "generic_action": choose(case, False),
                     "witness_action": choose(case, True)})
    Path(sys.argv[2]).write_text(json.dumps({"allocation": workload["allocation"], "rows": rows},
                                            sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
