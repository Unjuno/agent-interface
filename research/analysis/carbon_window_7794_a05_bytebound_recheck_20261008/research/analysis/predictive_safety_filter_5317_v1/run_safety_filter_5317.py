"""Run one deterministic host-only matrix and retain raw JSON."""

import json
import sys
from test_safety_filter_5317 import CASES
from safety_filter_5317 import POLICIES, run_case


def serializable_case(case):
    def graph_rows(graph):
        return [{"state": s, "action": a, "successors": list(nexts)}
                for (s, a), nexts in sorted(graph.items())]
    return {"initial": case["initial"], "plan": case["plan"],
            "model": graph_rows(case["model"]), "truth": graph_rows(case["truth"]),
            "forbidden": case["forbidden"], "goals": case["goals"],
            "recoveries": case["recoveries"], "model_quality": case["model_quality"]}


def main(path):
    raw = {
        "metadata": {"issue": 5317, "source_main": "70b69b47845b35afde59c2a5f0b56c6f906c6904",
                     "mode": "host-only-construction", "horizon": 2,
                     "container_invocations": 0},
        "cases": {},
    }
    for name, case in CASES.items():
        raw["cases"][name] = {
            "input": serializable_case(case),
            "policies": {policy: run_case(case, policy) for policy in POLICIES},
        }
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(raw, f, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps({"raw_path": path, "scenarios": len(raw["cases"]),
                      "policy_cells": sum(len(v["policies"]) for v in raw["cases"].values()),
                      "container_invocations": 0}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "safety_filter_5317_raw.json")
