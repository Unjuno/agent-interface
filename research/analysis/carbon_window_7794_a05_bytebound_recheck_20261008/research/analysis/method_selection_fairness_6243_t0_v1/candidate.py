import json
from collections import defaultdict
from pathlib import Path

from annotator_a import annotate as code_a
from annotator_b import annotate as code_b

ROOT = Path(__file__).parent
cases = json.loads((ROOT / "cases.json").read_text())
key = json.loads((ROOT / "key.json").read_text())

output = {"schema": "issue6243-t0-candidate-v1", "scenario_results": []}
for scenario in cases["scenarios"]:
    by_id = {}
    comparisons = []
    annotation_pairs = []
    for row in scenario["rows"]:
        a = code_a(row)
        b = code_b(row)
        comparisons.append(a == b)
        annotation_pairs.append({"row_id": row["row_id"], "a": a, "b": b})
        arm = key[scenario["id"]][row["blind_code"]]
        by_id[row["row_id"]] = {**a, "arm": arm}

    by_method = defaultdict(list)
    for item in by_id.values():
        by_method[(item["arm"], item["method"])].append(item)

    method_summary = []
    for (arm, method), items in sorted(by_method.items()):
        method_summary.append({
            "arm": arm, "method": method, "n": len(items),
            "elapsed_ms": sum(x["duration_ms"] for x in items),
            "correct": sum(x["terminal"] == "correct" for x in items),
            "failed": sum(x["terminal"] != "correct" for x in items),
            "switches": sum(x["switches"] for x in items),
            "errors": sum(x["errors"] for x in items),
        })

    natural = scenario["natural_method"]
    natural_elapsed = {}
    for arm in ("H", "A"):
        selected = [x for x in by_id.values() if x["arm"] == arm and
                    (natural[arm] == "mixed" or x["method"] == natural[arm])]
        natural_elapsed[arm] = sum(x["duration_ms"] for x in selected)
    horizon = scenario["horizon"]
    acquisition = scenario["acquisition_ms"]
    horizon_cost = {arm: acquisition[arm] + horizon * natural_elapsed[arm] for arm in ("H", "A")}

    output["scenario_results"].append({
        "scenario": scenario["id"],
        "coder_rows": len(comparisons),
        "coder_agreement": sum(comparisons) / len(comparisons),
        "annotation_pairs": annotation_pairs,
        "all_rows_preserved": len(by_id) == len(scenario["rows"]),
        "method_summary": method_summary,
        "natural_method_elapsed_ms": natural_elapsed,
        "acquisition_inclusive_horizon_ms": horizon_cost,
        "horizon": horizon,
        "row_ids": sorted(by_id),
    })

output["horizon_sensitivity"] = {
    str(n): {"H": 35000 + n * 4000, "A": n * 10000}
    for n in (1, 4, 10)
}

(ROOT / "candidate.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
print(json.dumps(output, indent=2, sort_keys=True))
