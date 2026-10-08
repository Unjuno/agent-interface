"""Strict construction reducer for the v1 per-admission receipt contract."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1_PATH = HERE.parent / "map01_key_release_binding_a01_20261005" / "candidate.py"
V1_SPEC = importlib.util.spec_from_file_location("binding_candidate_v1", V1_PATH)
V1 = importlib.util.module_from_spec(V1_SPEC)
V1_SPEC.loader.exec_module(V1)


def reduce(case):
    execution = case.get("execution", {})
    execution_id = execution.get("id")
    execution_step = execution.get("step")
    if (type(execution_id) is not str or not execution_id
            or type(execution_step) is not int or execution_step < 0):
        return "FAIL", "invalid_execution_context_type"

    admissions = case.get("admissions", [])
    ups = case.get("key_ups", [])
    releases = case.get("releases", [])
    if len(releases) != 1:
        return "FAIL", "release_not_empty_or_out_of_order"
    if type(releases[0].get("seq")) is not int or releases[0]["seq"] < 0:
        return "FAIL", "invalid_sequence_type"

    ids = [row.get("admission_id") for row in admissions]
    if any(type(value) is not str or not value for value in ids) or len(ids) != len(set(ids)):
        return "FAIL", "duplicate_or_invalid_admission_id"

    for row in admissions:
        if (type(row.get("execution_id")) is not str or not row.get("execution_id")
                or type(row.get("step")) is not int or row.get("step") < 0
                or type(row.get("key")) is not str or not row.get("key")):
            return "FAIL", "invalid_admission_context_type"
        if row["execution_id"] != execution_id or row["step"] != execution_step:
            return "FAIL", "unbound_or_cross_execution_admission"
        if type(row.get("seq")) is not int or row["seq"] < 0:
            return "FAIL", "invalid_sequence_type"

    expected = {(row["admission_id"], row["execution_id"], row["step"], row["key"]): row["seq"]
                for row in admissions if row.get("outcome") == "admitted"}
    observed = {}
    for row in ups:
        if type(row.get("step")) is not int or row["step"] < 0:
            return "FAIL", "invalid_up_context_type"
        if type(row.get("seq")) is not int or row["seq"] < 0:
            return "FAIL", "invalid_sequence_type"
        key = (row.get("admission_id"), row.get("execution_id"), row.get("step"), row.get("key"))
        if key not in expected:
            return "FAIL", "unbound_or_cross_execution_up"
        if row.get("outcome") != "up_confirmed" or row["seq"] <= expected[key]:
            return "FAIL", "up_before_admission_or_unconfirmed"
        if key in observed:
            return "FAIL", "duplicate_up"
        observed[key] = row["seq"]
    if set(observed) != set(expected):
        return "FAIL", "missing_per_key_up"

    release = releases[0]
    if (release.get("execution_id") != execution_id
            or release.get("outcome") != "empty_verified"
            or release["seq"] <= max(observed.values(), default=-1)):
        return "FAIL", "release_not_empty_or_out_of_order"
    return "PASS", "complete"


def mutate(fixture, name):
    case = copy.deepcopy(fixture)
    if name == "boolean_up_step":
        case["execution"]["step"] = case["admissions"][0]["step"] = 1
        case["key_ups"][0]["step"] = True
    elif name == "boolean_up_sequence":
        case["admissions"][0]["seq"] = 0
        case["key_ups"][0]["seq"] = True
        case["releases"][0]["seq"] = 2
    elif name == "boolean_admission_sequence":
        case["admissions"][0]["seq"] = True
    elif name == "float_release_sequence":
        case["releases"][0]["seq"] = 3.0
    elif name == "admission_step_outside_execution":
        case["execution"]["step"] = 3
    else:
        raise ValueError(name)
    return case


def main():
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    cases = [("baseline", fixture, "PASS", "complete")]
    cases.extend((m["name"], mutate(fixture, m["name"]), m["expected_status"], m["expected_reason"])
                 for m in fixture["mutations"])
    rows = []
    for name, case, expected_status, expected_reason in cases:
        v1_status, v1_reason = V1.reduce(case)
        status, reason = reduce(case)
        rows.append({"name": name, "v1_status": v1_status, "v1_reason": v1_reason,
                     "status": status, "reason": reason,
                     "expected_status": expected_status, "expected_reason": expected_reason})
    report = {"schema": "map01-key-release-binding-types-a01-v1", "cases": rows}
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "candidate-output.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    ok = (rows[0]["status"] == "PASS" and rows[0]["reason"] == "complete"
          and all(r["status"] == r["expected_status"] and r["reason"] == r["expected_reason"]
                  and r["v1_status"] == "PASS" for r in rows[1:]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
