"""Independent direct-table oracle; intentionally does not import candidate."""
import json
import sys
from fractions import Fraction
from pathlib import Path

EXPECTED_TASKS = {"E1", "E2", "H1", "H2"}


def avg(values):
    return str(sum((Fraction(str(v)) for v in values), Fraction(0, 1)) / len(values))


def oracle_case(case):
    by_id = {row["task"]: row for row in case["rows"]}
    if set(by_id) != EXPECTED_TASKS or len(by_id) != len(case["rows"]):
        raise ValueError("oracle_assignment_set_mismatch")
    order = [by_id[k] for k in ("E1", "E2", "H1", "H2")]
    local = [row for row in order if row["A_path"] == "local"]
    fallback = [row for row in order if row["A_path"] == "fallback"]
    if len(local) + len(fallback) != 4 or not local:
        raise ValueError("oracle_exposure_partition_mismatch")
    return {
        "case_id": case["case_id"],
        "assigned_n": 4,
        "A_assigned_success": avg([r["A_success"] for r in order]),
        "B_assigned_success": avg([r["B_success"] for r in order]),
        "A_assigned_mean_total_time": avg([r["A_total_time"] for r in order]),
        "B_assigned_mean_total_time": avg([r["B_total_time"] for r in order]),
        "A_exposure_flow": {"local": len(local), "fallback": len(fallback)},
        "A_local_subset_n": len(local),
        "A_local_subset_success": avg([r["A_success"] for r in local]),
        "A_local_subset_mean_total_time": avg([r["A_total_time"] for r in local]),
        "local_subset_is_descriptive_only": True,
    }


def main():
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps({"schema": "route_assignment_exposure_oracle_v1",
                      "cases": [oracle_case(c) for c in data["cases"]]},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
