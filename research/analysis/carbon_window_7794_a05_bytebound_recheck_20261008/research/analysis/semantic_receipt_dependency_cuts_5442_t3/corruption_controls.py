"""Six raw mutations checked by the T3 independent auditor."""

import copy
import json
import sys

from audit import audit


def run(path):
    with open(path, encoding="utf-8") as handle:
        base = [json.loads(line) for line in handle if line.strip()]
    mutations = {}
    graph = copy.deepcopy(base)
    graph[0]["provenance"]["observer_c"].append("shared_cache")
    mutations["forged_shared_dependency"] = graph
    missing_failure = copy.deepcopy(base)
    missing_failure[3]["failed_dependencies"] = []
    mutations["erased_failure_record"] = missing_failure
    report = copy.deepcopy(base)
    report[1]["observer_reports"]["observer_a"] = "doc:v9"
    mutations["altered_observer_report"] = report
    truth = copy.deepcopy(base)
    truth[3]["actual"] = "doc:v9"
    mutations["forged_ground_truth"] = truth
    summary = copy.deepcopy(base)
    summary[3]["ab_agreement_commit"] = False
    mutations["flipped_baseline_summary"] = summary
    endpoint = copy.deepcopy(base)
    endpoint[3]["trusted_endpoint"] = "observer_a"
    mutations["changed_trusted_endpoint"] = endpoint

    rows = []
    for name, mutated in mutations.items():
        result = audit(mutated)
        rows.append({"name": name, "rejected": result["audit"] == "FAIL", "errors": result["errors"]})
    return {"controls": rows, "passed": sum(item["rejected"] for item in rows), "total": len(rows)}


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1]), sort_keys=True, separators=(",", ":")))
