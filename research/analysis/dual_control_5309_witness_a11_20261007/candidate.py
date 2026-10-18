"""A11 advisory chooser; candidate-input only by protocol, not OS isolation."""
import json
import sys
from pathlib import Path


def choose(case, witness_aware):
    actions = case["admissible_actions"]
    if not witness_aware or case["preexisting_witness"]:
        return min(actions)
    eligible = [a for a in actions if case["predicted_witness_survival"][a]
                and case["preservation_cost"][a] <= case["cost_budget"]]
    return min(eligible, key=lambda a: (case["preservation_cost"][a], a)) if eligible else min(actions)


def main():
    workload = json.loads(Path(sys.argv[1]).read_text())
    rows = [{"case_id": c["case_id"], "generic_action": choose(c, False),
             "witness_action": choose(c, True)} for c in workload["cases"]]
    Path(sys.argv[2]).write_text(json.dumps({"allocation": workload["allocation"], "rows": rows},
                                            sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
