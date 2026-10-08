import json
from collections import defaultdict
from pathlib import Path

from coder_a import annotate as code_a
from coder_b import annotate as code_b

ROOT = Path(__file__).parent
traces = json.loads((ROOT / "traces.json").read_text())
arm_key = json.loads((ROOT / "key.json").read_text())
result = {"schema": "issue6243-t0-successor02-result-v1", "scenarios": []}

for scenario in traces["scenarios"]:
    annotations = []
    pairs = []
    stats = defaultdict(lambda: {"n": 0, "elapsed_ms": 0, "penalty_ms": 0, "errors": 0, "switches": 0, "correct": 0, "failed": 0, "unfinished": 0})
    method_stats = defaultdict(lambda: {"segments": 0, "elapsed_ms": 0, "errors": 0, "switches": 0})
    for row in scenario["rows"]:
        a = code_a(row, traces["unfinished_penalty_ms"])
        b = code_b(row, traces["unfinished_penalty_ms"])
        pairs.append({"row_id": row["row_id"], "a": a, "b": b})
        arm = arm_key[scenario["id"]][row["blind_code"]]
        annotations.append({**a, "arm": arm})
        bucket = stats[arm]
        bucket["n"] += 1
        bucket["elapsed_ms"] += a["elapsed_ms"]
        bucket["penalty_ms"] += a["penalty_ms"]
        bucket["errors"] += a["errors"]
        bucket["switches"] += a["switches"]
        bucket["correct"] += int(a["final_outcome"] == "correct")
        bucket["failed"] += int(a["final_outcome"] == "failed")
        bucket["unfinished"] += int(a["final_outcome"] == "unfinished")
        for segment in a["segments"]:
            mb = method_stats[(arm, segment["method"])]
            mb["segments"] += 1
            mb["elapsed_ms"] += segment["duration_ms"]
            mb["errors"] += segment["errors"]
            mb["switches"] += segment["switches"]
    arms = {}
    for arm, values in sorted(stats.items()):
        arms[arm] = {**values, "scored_ms": values["elapsed_ms"] + values["penalty_ms"], "acquisition_ms": scenario["acquisition_ms"][arm]}
    by_method = []
    for (arm, method), values in sorted(method_stats.items()):
        by_method.append({
            "arm": arm, "method": method, **values,
            "mean_elapsed_ms": values["elapsed_ms"] / values["segments"],
        })
    result["scenarios"].append({
        "id": scenario["id"],
        "attempt_count": len(annotations),
        "attempt_ids": sorted(item["row_id"] for item in annotations),
        "annotation_pairs": pairs,
        "coder_agreement": sum(pair["a"] == pair["b"] for pair in pairs) / len(pairs),
        "all_attempts_preserved": len(annotations) == len(scenario["rows"]),
        "arms": arms,
        "method_summary": by_method,
    })

mix = next(item for item in result["scenarios"] if item["id"] == "shortcut_mixture")
per_repeat = {arm: mix["arms"][arm]["scored_ms"] for arm in ("H", "A")}
mix["horizon_sensitivity"] = {
    str(repeats): {
        arm: mix["arms"][arm]["acquisition_ms"] + repeats * per_repeat[arm]
        for arm in ("H", "A")
    }
    for repeats in traces["horizon_repeats"]
}
(ROOT / "candidate_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
