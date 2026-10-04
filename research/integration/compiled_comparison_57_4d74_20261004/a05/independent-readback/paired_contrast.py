"""Read-only paired task-level description of the merged A05 raw records."""
import collections
import json
import subprocess
from pathlib import Path

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
REF = "58bcbb4c45501880db8782158ddd3add3b765984"
BASE = "research/integration/compiled_comparison_57_4d74_20261004/a05/formal-output"


def task(block, arm, number):
    raw = subprocess.check_output([
        "git", "-C", REPO, "show",
        f"{REF}:{BASE}/block-{block}/{arm}/task-{number}.json",
    ])
    row = json.loads(raw)
    calls = row["caller"].get("model_call_ledger", [])
    usage = sum((call.get("usage") or {}).get("input_tokens", 0) +
                (call.get("usage") or {}).get("output_tokens", 0) for call in calls)
    return {
        "task_id": row["task"]["task_id"],
        "token": row["task"]["token"],
        "layout": row["task"]["layout"],
        "phase": row["task"]["phase"],
        "success": row["caller"]["outcome"] == "TASK_SUCCEEDED",
        "tokens": usage,
        "elapsed_ms": row["elapsed_ns"] / 1_000_000,
    }


totals = {arm: collections.Counter() for arm in "ABCD"}
phases = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
comparisons = {}
pair_rows = []
for block in (1, 2):
    for number in range(1, 7):
        rows = {arm: task(block, arm, number) for arm in "ABCD"}
        assert len({(r["token"], r["layout"], r["phase"]) for r in rows.values()}) == 1
        for arm, row in rows.items():
            totals[arm]["tokens"] += row["tokens"]
            totals[arm]["elapsed_ms"] += row["elapsed_ms"]
            totals[arm]["successes"] += int(row["success"])
            phase = phases[row["phase"]][arm]
            phase["tokens"] += row["tokens"]
            phase["elapsed_ms"] += row["elapsed_ms"]
            phase["successes"] += int(row["success"])
        item = {"block": block, "task": number, "phase": rows["A"]["phase"]}
        for left, right in (("A", "B"), ("B", "C"), ("B", "D")):
            item[f"{left}_minus_{right}_tokens"] = rows[left]["tokens"] - rows[right]["tokens"]
            item[f"{left}_minus_{right}_elapsed_ms"] = round(
                rows[left]["elapsed_ms"] - rows[right]["elapsed_ms"], 3)
            item[f"{left}_{right}_both_succeeded"] = rows[left]["success"] and rows[right]["success"]
        pair_rows.append(item)

for left, right in (("A", "B"), ("B", "C"), ("B", "D")):
    comparisons[f"{left}_minus_{right}"] = {
        "pairs": 12,
        "both_succeeded_pairs": sum(item[f"{left}_{right}_both_succeeded"] for item in pair_rows),
        "left_used_fewer_tokens": sum(item[f"{left}_minus_{right}_tokens"] < 0 for item in pair_rows),
        "equal_tokens": sum(item[f"{left}_minus_{right}_tokens"] == 0 for item in pair_rows),
        "left_faster": sum(item[f"{left}_minus_{right}_elapsed_ms"] < 0 for item in pair_rows),
        "equal_elapsed": sum(item[f"{left}_minus_{right}_elapsed_ms"] == 0 for item in pair_rows),
        "left_slower": sum(item[f"{left}_minus_{right}_elapsed_ms"] > 0 for item in pair_rows),
    }

assert [totals[arm]["successes"] for arm in "ABCD"] == [12, 12, 9, 12]
assert comparisons["A_minus_B"]["both_succeeded_pairs"] == 12
assert comparisons["B_minus_C"]["both_succeeded_pairs"] == 9
assert comparisons["B_minus_D"]["left_slower"] == 12

output = {
    "ref": REF,
    "matching_key": "block + task_id, cross-checked token/layout/phase identical in all four arms",
    "arm_totals": {arm: {key: round(value, 3) if key == "elapsed_ms" else value
                         for key, value in totals[arm].items()} for arm in "ABCD"},
    "paired_contrasts": comparisons,
    "phase_totals": {
        phase: {arm: {key: round(value, 3) if key == "elapsed_ms" else value
                      for key, value in values.items()} for arm, values in arms.items()}
        for phase, arms in phases.items()
    },
    "pairs": pair_rows,
    "limits": [
        "Descriptive two-block archive analysis; not a population estimate.",
        "Task elapsed excludes separately measured schema-preflight waits.",
        "Human setup cost is unavailable; D is a known-form deterministic route.",
        "No historical arms were pooled and no producer was replayed.",
    ],
}
print(json.dumps(output, indent=2, sort_keys=True))
