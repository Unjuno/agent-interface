"""Raw-only independent class gate and schedule reconstruction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


VALID_CLASSES = ("control", "best_effort")
REQUIRED = ("id", "class", "release", "execution", "deadline", "preemptible")


def _status(case: dict) -> str:
    work = case.get("jobs") if isinstance(case, dict) else None
    if not isinstance(work, list) or not work:
        return "HOLD_NO_SCHEDULABILITY_INPUTS"
    for item in work:
        if not isinstance(item, dict):
            return "HOLD_NO_SCHEDULABILITY_INPUTS"
        label = item.get("class", object())
        if type(label) is not str or label not in VALID_CLASSES:
            return "HOLD_UNKNOWN_JOB_CLASS"
    for item in work:
        if any(name not in item for name in REQUIRED):
            return "HOLD_NO_SCHEDULABILITY_INPUTS"
        if item["preemptible"] is not True:
            return "UNKNOWN_MODEL_MISMATCH"
        if (
            type(item["release"]) is not int
            or type(item["execution"]) is not int
            or type(item["deadline"]) is not int
            or type(item["id"]) is not str
            or not item["id"]
            or item["release"] < 0
            or item["execution"] < 1
            or item["deadline"] <= item["release"]
        ):
            return "HOLD_NO_SCHEDULABILITY_INPUTS"
    identifiers = [item["id"] for item in work]
    if len(identifiers) != len(set(identifiers)):
        return "HOLD_DUPLICATE_JOB_ID"
    return "ELIGIBLE"


def _demand_feasible(work: list[dict]) -> bool:
    points = sorted({job["release"] for job in work} | {job["deadline"] for job in work})
    for start in points:
        for stop in points:
            if stop <= start:
                continue
            demand = sum(
                job["execution"] for job in work
                if start <= job["release"] and job["deadline"] <= stop
            )
            if demand > stop - start:
                return False
    return True


def _exhaustive_feasible(work: list[dict]) -> bool:
    if not work:
        return True
    first = min(job["release"] for job in work)
    last = max(job["deadline"] for job in work)
    initial = tuple(job["execution"] for job in work)
    states = {initial}
    for tick in range(first, last):
        next_states = set()
        for remaining in states:
            if any(remaining[i] and work[i]["deadline"] <= tick for i in range(len(work))):
                continue
            ready = [
                i for i, job in enumerate(work)
                if remaining[i] and job["release"] <= tick
            ]
            for selected in [None, *ready]:
                updated = list(remaining)
                if selected is not None:
                    updated[selected] -= 1
                next_states.add(tuple(updated))
        states = next_states
    return any(not any(remaining) for remaining in states)


def _expected(case: dict) -> dict:
    status = _status(case)
    if status != "ELIGIBLE":
        return {"status": status}
    work = case["jobs"]
    controls = [item for item in work if item["class"] == "control"]
    control_demand = _demand_feasible(controls)
    control_exhaustive = _exhaustive_feasible(controls)
    all_demand = _demand_feasible(work)
    all_exhaustive = _exhaustive_feasible(work)
    if control_demand != control_exhaustive or all_demand != all_exhaustive:
        return {"status": "FAIL_ORACLE_DISAGREEMENT"}
    return {
        "status": "ELIGIBLE",
        "control_feasible": control_demand,
        "all_feasible": all_demand,
    }


def audit(raw: dict, frozen_cases: list[dict]) -> dict:
    errors = []
    if not isinstance(raw, dict) or raw.get("schema") != "7748-duplicate-id-a01-raw-v1":
        errors.append("schema")
    rows = raw.get("rows", []) if isinstance(raw, dict) else []
    if not isinstance(rows, list) or len(rows) != len(frozen_cases):
        errors.append("case_count")
        rows = rows if isinstance(rows, list) else []
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("input"), dict):
            errors.append("row_shape")
            continue
        case_id = row["input"].get("id")
        if case_id in by_id:
            errors.append("duplicate_id:" + str(case_id))
        by_id[case_id] = row
    for case in frozen_cases:
        key = case.get("id")
        row = by_id.get(key)
        if row is None:
            errors.append("missing:" + str(key))
            continue
        if row.get("input") != case:
            errors.append("input:" + str(key))
        expected = _expected(case)
        if expected.get("status") == "FAIL_ORACLE_DISAGREEMENT":
            errors.append("oracle:" + str(key))
        if row.get("result") != expected:
            errors.append("result:" + str(key))
    return {
        "status": "PASS_DUPLICATE_ID_BOUNDARY_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "case_count": len(frozen_cases),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    package = Path(__file__).parent
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    cases = json.loads((package / "cases.json").read_text(encoding="utf-8"))["cases"]
    result = audit(raw, cases)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_CLASS_BOUNDARY_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
