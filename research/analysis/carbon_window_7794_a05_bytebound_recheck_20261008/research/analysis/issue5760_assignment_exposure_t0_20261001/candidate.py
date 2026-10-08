"""Candidate T0 calculator for the frozen assignment/exposure fixtures."""
import json
import sys
from fractions import Fraction
from pathlib import Path

TASKS = ("E1", "E2", "H1", "H2")


def validate(case):
    rows = case["rows"]
    if [r["task"] for r in rows] != list(TASKS):
        raise ValueError("assignment_denominator_or_order_mismatch")
    for r in rows:
        if r["difficulty"] != ("easy" if r["task"].startswith("E") else "hard"):
            raise ValueError("difficulty_stratum_mismatch")
        if r["A_path"] not in ("local", "fallback") or r["B_path"] != "plain":
            raise ValueError("unknown_exposure_path")
        for key in ("A_success", "B_success"):
            if type(r[key]) is not int or r[key] not in (0, 1):
                raise ValueError("invalid_binary_outcome")
        for key in ("A_total_time", "B_total_time"):
            if type(r[key]) not in (int, float) or r[key] < 0:
                raise ValueError("invalid_total_time")
    return rows


def mean(rows, field):
    return str(sum((Fraction(str(row[field])) for row in rows), Fraction()) / len(rows))


def summarize(case):
    rows = validate(case)
    local = [r for r in rows if r["A_path"] == "local"]
    if not local:
        raise ValueError("no_local_exposure_rows")
    return {
        "case_id": case["case_id"],
        "assigned_n": len(rows),
        "A_assigned_success": mean(rows, "A_success"),
        "B_assigned_success": mean(rows, "B_success"),
        "A_assigned_mean_total_time": mean(rows, "A_total_time"),
        "B_assigned_mean_total_time": mean(rows, "B_total_time"),
        "A_exposure_flow": {
            "local": sum(r["A_path"] == "local" for r in rows),
            "fallback": sum(r["A_path"] == "fallback" for r in rows),
        },
        "A_local_subset_n": len(local),
        "A_local_subset_success": mean(local, "A_success"),
        "A_local_subset_mean_total_time": mean(local, "A_total_time"),
        "local_subset_is_descriptive_only": True,
    }


def main():
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if data["schema"] != "route_assignment_exposure_fixture_v1":
        raise SystemExit("unexpected fixture schema")
    result = {"schema": "route_assignment_exposure_candidate_v1",
              "cases": [summarize(c) for c in data["cases"]]}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
