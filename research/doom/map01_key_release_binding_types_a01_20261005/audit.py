"""Independent strict oracle for the scalar/context construction comparison."""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def cases_from_fixture(fixture):
    result = [("baseline", copy.deepcopy(fixture))]
    for mutation in fixture["mutations"]:
        case = copy.deepcopy(fixture)
        name = mutation["name"]
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
        result.append((name, case))
    return result


def oracle(case):
    execution = case.get("execution", {})
    execution_id, execution_step = execution.get("id"), execution.get("step")
    if type(execution_id) is not str or not execution_id or type(execution_step) is not int or execution_step < 0:
        return "FAIL", "invalid_execution_context_type"
    releases = case.get("releases", [])
    if len(releases) != 1:
        return "FAIL", "release_not_empty_or_out_of_order"
    release = releases[0]
    if type(release.get("seq")) is not int or release["seq"] < 0:
        return "FAIL", "invalid_sequence_type"
    admissions = case.get("admissions", [])
    ids = [a.get("admission_id") for a in admissions]
    if any(type(value) is not str or not value for value in ids) or len(ids) != len(set(ids)):
        return "FAIL", "duplicate_or_invalid_admission_id"
    admitted = {}
    for row in admissions:
        if (type(row.get("execution_id")) is not str or not row.get("execution_id")
                or type(row.get("step")) is not int or row["step"] < 0
                or type(row.get("key")) is not str or not row.get("key")):
            return "FAIL", "invalid_admission_context_type"
        if row["execution_id"] != execution_id or row["step"] != execution_step:
            return "FAIL", "unbound_or_cross_execution_admission"
        if type(row.get("seq")) is not int or row["seq"] < 0:
            return "FAIL", "invalid_sequence_type"
        if row.get("outcome") == "admitted":
            admitted[row["admission_id"]] = row
    seen, up_sequences = set(), []
    for row in case.get("key_ups", []):
        if type(row.get("step")) is not int or row["step"] < 0:
            return "FAIL", "invalid_up_context_type"
        if type(row.get("seq")) is not int or row["seq"] < 0:
            return "FAIL", "invalid_sequence_type"
        admission = admitted.get(row.get("admission_id"))
        if admission is None or any(row.get(k) != admission.get(k) for k in ("execution_id", "step", "key")):
            return "FAIL", "unbound_or_cross_execution_up"
        if row.get("outcome") != "up_confirmed" or row["seq"] <= admission["seq"]:
            return "FAIL", "up_before_admission_or_unconfirmed"
        if row["admission_id"] in seen:
            return "FAIL", "duplicate_up"
        seen.add(row["admission_id"])
        up_sequences.append(row["seq"])
    if seen != set(admitted):
        return "FAIL", "missing_per_key_up"
    if (release.get("execution_id") != execution_id or release.get("outcome") != "empty_verified"
            or release["seq"] <= max(up_sequences, default=-1)):
        return "FAIL", "release_not_empty_or_out_of_order"
    return "PASS", "complete"


def main():
    fixture_bytes = (HERE / "fixture.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    candidate = json.loads((Path(sys.argv[1]) / "candidate-output.json").read_text(encoding="utf-8"))
    wanted = [(name, case, "PASS", "complete") if index == 0 else
              (name, case, fixture["mutations"][index - 1]["expected_status"],
               fixture["mutations"][index - 1]["expected_reason"])
              for index, (name, case) in enumerate(cases_from_fixture(fixture))]
    rows = candidate.get("cases", [])
    checks = []
    for actual, (name, case, declared_status, declared_reason) in zip(rows, wanted):
        status, reason = oracle(case)
        checks.append({"name_matches": actual.get("name") == name,
                       "v1_exposes_accepted_fault": name == "baseline" or actual.get("v1_status") == "PASS",
                       "strict_candidate_matches_oracle": actual.get("status") == status and actual.get("reason") == reason,
                       "frozen_disposition_matches_oracle": declared_status == status and declared_reason == reason})
    valid = len(rows) == len(wanted) and len(checks) == len(wanted) and all(all(c.values()) for c in checks)
    report = {"status": "PASS" if valid else "FAIL_AUDIT", "case_count": len(checks), "checks": checks,
              "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
              "candidate_sha256": hashlib.sha256((Path(sys.argv[1]) / "candidate-output.json").read_bytes()).hexdigest(),
              "independence": "separate strict decision oracle; does not import candidate"}
    out = Path(sys.argv[1])
    (out / "audit-output.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
