"""Mutation controls for the T12 raw-only auditor."""

import copy
import json
import sys

from audit import audit_rows


def main(path):
    with open(path, encoding="utf-8") as handle:
        baseline = [json.loads(line) for line in handle if line.strip()]
    mutations = {}
    duplicate = copy.deepcopy(baseline)
    duplicate.append(copy.deepcopy(duplicate[0]))
    mutations["duplicate_case"] = duplicate
    mutations["missing_case"] = copy.deepcopy(baseline[:-1])
    flipped = copy.deepcopy(baseline)
    flipped[1]["bisimilar"] = True
    mutations["forged_bisim_summary"] = flipped
    dropped = copy.deepcopy(baseline)
    dropped[1]["left"]["delete_branch"].pop("DELETE")
    mutations["deleted_branch_edge"] = dropped
    renamed = copy.deepcopy(baseline)
    renamed[1]["right"]["combined_branch"]["DELETE"] = renamed[1]["right"]["combined_branch"].pop("COPY")
    mutations["renamed_visible_edge"] = renamed
    cyclic = copy.deepcopy(baseline)
    cyclic[1]["left"]["done"]["LOOP"] = ["done"]
    mutations["out_of_model_cycle"] = cyclic
    forged_traces = copy.deepcopy(baseline)
    forged_traces[0]["left_traces"] = [["FORGED"]]
    mutations["forged_trace_list"] = forged_traces
    results = []
    for name, rows in mutations.items():
        result = audit_rows(rows)
        results.append({"name": name, "rejected": result["audit"] == "FAIL", "errors": result["errors"]})
    return {"controls": results, "passed": sum(row["rejected"] for row in results), "total": len(results)}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), sort_keys=True, separators=(",", ":")))
