"""Independent audit of candidate receipt decisions; does not import candidate."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def expected_for(case, is_baseline):
    admissions = case.get("admissions", [])
    ups = case.get("key_ups", [])
    release_rows = case.get("releases", [])
    ids = [a.get("admission_id") for a in admissions]
    if len(ids) != len(set(ids)) or any(not isinstance(x, str) or not x for x in ids):
        return "FAIL", "duplicate_or_invalid_admission_id"
    by_id = {a["admission_id"]: a for a in admissions if a.get("outcome") == "admitted"}
    seen = set()
    for up in ups:
        admission = by_id.get(up.get("admission_id"))
        if admission is None or any(up.get(k) != admission.get(k) for k in ("execution_id", "step", "key")):
            return "FAIL", "unbound_or_cross_execution_up"
        if up.get("outcome") != "up_confirmed" or not isinstance(up.get("seq"), int) or up["seq"] <= admission.get("seq", -1):
            return "FAIL", "up_before_admission_or_unconfirmed"
        if up["admission_id"] in seen:
            return "FAIL", "duplicate_up"
        seen.add(up["admission_id"])
    if len(seen) != len(by_id):
        return "FAIL", "missing_per_key_up"
    if (len(release_rows) != 1 or release_rows[0].get("execution_id") != case.get("execution", {}).get("id")
            or release_rows[0].get("outcome") != "empty_verified"
            or release_rows[0].get("seq", -1) <= max((up.get("seq", -1) for up in ups), default=-1)):
        return "FAIL", "release_not_empty_or_out_of_order"
    return ("PASS", "complete") if is_baseline else ("FAIL", "mutation_unexpectedly_valid")


def main():
    fixture_bytes = (HERE / "fixture.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    candidate = json.loads((output_dir / "candidate-output.json").read_text(encoding="utf-8"))
    expected_cases = [("baseline", fixture, fixture["expected"]["status"], fixture["expected"]["class"], True)]
    expected_cases += [(m["name"], _mutated(fixture, m["name"]), "FAIL", m["expected_reason"], False)
                       for m in fixture["mutations"]]
    checks = []
    for row, (name, case, declared_status, declared_reason, baseline) in zip(candidate.get("cases", []), expected_cases):
        expected_status, expected_reason = expected_for(case, baseline)
        checks.append({"name_matches": row.get("name") == name,
                       "status_matches_independent_oracle": row.get("status") == expected_status,
                       "reason_matches_independent_oracle": row.get("reason") == expected_reason,
                       "declared_status_matches_oracle": declared_status == expected_status,
                       "declared_reason_matches_oracle": declared_reason == expected_reason,
                       "candidate_expectation_matches_frozen_declaration":
                           row.get("expected_status") == declared_status and row.get("expected_reason") == declared_reason})
    valid = (len(candidate.get("cases", [])) == len(expected_cases) and len(checks) == len(expected_cases)
             and all(all(c.values()) for c in checks))
    report = {"status": "PASS" if valid else "FAIL_AUDIT", "case_count": len(checks),
              "checks": checks, "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
              "candidate_sha256": hashlib.sha256((output_dir / "candidate-output.json").read_bytes()).hexdigest(),
              "independence": "standalone decision oracle; does not import candidate"}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "audit-output.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if valid else 1


def _mutated(fixture, name):
    import copy
    case = copy.deepcopy(fixture)
    mutation = next(m for m in fixture["mutations"] if m["name"] == name)
    fault = mutation["fault"]
    if fault == "duplicate_admission_id": case["admissions"].append(dict(case["admissions"][0], key="Up", seq=2))
    elif fault == "cross_execution_up": case["key_ups"][0]["execution_id"] = "exec-other"
    elif fault == "up_before_admission": case["key_ups"][0]["seq"] = 0
    elif fault == "missing_per_key_up": case["key_ups"] = []
    elif fault == "duplicate_up":
        case["key_ups"].append(dict(case["key_ups"][0], seq=3)); case["releases"][0]["seq"] = 4
    elif fault == "release_not_empty_verified": case["releases"][0]["outcome"] = "release_requested"
    return case


if __name__ == "__main__":
    raise SystemExit(main())
