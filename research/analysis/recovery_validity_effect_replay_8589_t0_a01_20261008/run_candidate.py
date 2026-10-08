"""One-shot candidate runner for the frozen finite input corpus."""

import json
import sys

from candidate import plan_recovery


def _expand(payload):
    nodes = payload["base_nodes"]
    rows = []
    for scenario in payload["cases"]:
        graph = json.loads(json.dumps(nodes))
        receipts = scenario.get("receipt_overrides", {})
        for node in graph:
            if node["id"] in receipts:
                node["receipt"] = receipts[node["id"]]
        rows.append({
            "case_id": scenario["case_id"],
            "provenance_complete": scenario["provenance_complete"],
            "current_versions": scenario["current_versions"],
            "nodes": graph,
        })
    return rows


def evaluate(payload):
    results = [{"case_id": case["case_id"], "plan": plan_recovery(case)}
               for case in _expand(payload)]
    return {"results": results}


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as stream:
        payload = json.load(stream)
    rendered = json.dumps(evaluate(payload), sort_keys=True, separators=(",", ":")) + "\n"
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
