import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parent
OUT = Path("/out/formal01")


def summarize(rows):
    if not rows:
        return {"n": 0, "successes": 0, "success_rate": None, "mean_time": None}
    return {"n": len(rows), "successes": sum(r["success"] for r in rows),
            "success_rate": sum(r["success"] for r in rows) / len(rows),
            "mean_time": sum(r["total_time"] for r in rows) / len(rows)}


def build_raw():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    rows = []
    summaries = {}
    for scenario, tasks in fixture["scenarios"].items():
        scenario_rows = []
        for task in tasks:
            for arm in ("A", "B"):
                if arm == "A":
                    path = task["A_path"]
                    admitted = path == "local"
                    success = task["A_success"]
                    total_time = task["A_time"]
                else:
                    path = "plain"
                    admitted = True
                    success = task["B_success"]
                    total_time = task["B_time"]
                row = {"scenario": scenario, "task": task["task"], "difficulty": task["difficulty"],
                       "assigned_arm": arm, "actual_path": path,
                       "admission": admitted, "admission_timing": "POST_ASSIGNMENT",
                       "success": success, "total_time": total_time,
                       "fallback_time": total_time if arm == "A" and path == "fallback" else 0}
                rows.append(row)
                scenario_rows.append(row)
        assigned = {arm: summarize([r for r in scenario_rows if r["assigned_arm"] == arm]) for arm in ("A", "B")}
        selected = summarize([r for r in scenario_rows if r["assigned_arm"] == "A" and r["actual_path"] == "local"])
        summaries[scenario] = {"assigned_policy": assigned,
                               "A_executed_local_only_descriptive": selected,
                               "A_minus_B_success_rate": assigned["A"]["success_rate"] - assigned["B"]["success_rate"],
                               "A_minus_B_mean_time": assigned["A"]["mean_time"] - assigned["B"]["mean_time"],
                               "local_only_minus_B_success_rate_descriptive": selected["success_rate"] - assigned["B"]["success_rate"],
                               "local_only_minus_B_mean_time_descriptive": selected["mean_time"] - assigned["B"]["mean_time"]}
    return {"schema": "issue5760-assignment-exposure-raw-v1",
            "allocation": fixture["allocation"],
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "fixture_sha256": hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest(),
            "estimand_label": "SYNTHETIC_AS_ASSIGNED_DESCRIPTIVE_NOT_CAUSAL",
            "exposure_label": "POST_ASSIGNMENT_SELECTED_SUBSET_DESCRIPTIVE_ONLY",
            "rows": rows, "summaries": summaries}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    encoded = json.dumps(build_raw(), sort_keys=True, separators=(",", ":")) + "\n"
    (OUT / "raw.json").write_text(encoded, encoding="utf-8")
    print(json.dumps({"allocation": "5760-route-assignment-t0-20261001-01", "rows": len(json.loads(encoded)["rows"]),
                      "raw_sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
