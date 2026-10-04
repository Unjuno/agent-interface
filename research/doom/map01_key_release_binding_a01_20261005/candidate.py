"""Candidate reducer for a synthetic per-admission key-up receipt contract."""
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def reduce(case):
    admissions = case["admissions"]
    ups = case["key_ups"]
    releases = case["releases"]
    ids = [row.get("admission_id") for row in admissions]
    if any(type(value) is not str or not value for value in ids) or len(ids) != len(set(ids)):
        return "FAIL", "duplicate_or_invalid_admission_id"
    expected = {(row["admission_id"], row["execution_id"], row["step"], row["key"]): row["seq"]
                for row in admissions if row.get("outcome") == "admitted"}
    observed = {}
    for row in ups:
        key = (row.get("admission_id"), row.get("execution_id"), row.get("step"), row.get("key"))
        if key not in expected:
            return "FAIL", "unbound_or_cross_execution_up"
        if row.get("outcome") != "up_confirmed" or row.get("seq", -1) <= expected[key]:
            return "FAIL", "up_before_admission_or_unconfirmed"
        if key in observed:
            return "FAIL", "duplicate_up"
        observed[key] = row.get("seq")
    if set(observed) != set(expected):
        return "FAIL", "missing_per_key_up"
    if (len(releases) != 1 or releases[0].get("execution_id") != case["execution"].get("id")
            or releases[0].get("outcome") != "empty_verified"
            or releases[0].get("seq", -1) <= max(observed.values(), default=-1)):
        return "FAIL", "release_not_empty_or_out_of_order"
    return "PASS", "complete"


def mutate(case, fault):
    case = copy.deepcopy(case)
    if fault == "duplicate_admission_id":
        case["admissions"].append(dict(case["admissions"][0], key="Up", seq=2))
    elif fault == "cross_execution_up":
        case["key_ups"][0]["execution_id"] = "exec-other"
    elif fault == "up_before_admission":
        case["key_ups"][0]["seq"] = 0
    elif fault == "missing_per_key_up":
        case["key_ups"] = []
    elif fault == "duplicate_up":
        case["key_ups"].append(dict(case["key_ups"][0], seq=3))
        case["releases"][0]["seq"] = 4
    elif fault == "release_not_empty_verified":
        case["releases"][0]["outcome"] = "release_requested"
    else:
        raise ValueError(fault)
    return case


def main():
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    cases = [("baseline", fixture, fixture["expected"])]
    for mutation in fixture["mutations"]:
        cases.append((mutation["name"], mutate(fixture, mutation["fault"]),
                      {"status": "FAIL", "class": mutation["fault"]}))
    rows = []
    for name, case, expected in cases:
        status, reason = reduce(case)
        rows.append({"name": name, "status": status, "reason": reason,
                     "expected_status": expected["status"],
                     "expected_class": expected["class"]})
    report = {"schema": "map01-key-release-binding-candidate-v1", "cases": rows}
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "candidate-output.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(r["status"] == r["expected_status"] and r["reason"] == r["expected_class"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
