"""Independent audit of the small timestamp-order construction corpus."""
import argparse
import hashlib
import json
from pathlib import Path

FIELDS = ("admitted_ns", "input_ack_ns", "release_call_started_ns", "release_call_returned_ns")


def audit(cases_path, raw_path, source_path, phase):
    cases_path, raw_path, source_path = map(Path, (cases_path, raw_path, source_path))
    cases_doc = json.loads(cases_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "owner-keyup-timestamp-order-raw-v1":
        errors.append("raw_schema")
    if raw.get("phase") != phase:
        errors.append("phase")
    if raw.get("base_commit") != cases_doc.get("base_commit"):
        errors.append("base_commit")
    if raw.get("cases_sha256") != hashlib.sha256(cases_path.read_bytes()).hexdigest():
        errors.append("cases_hash")
    if raw.get("source_sha256") != hashlib.sha256(source_path.read_bytes()).hexdigest():
        errors.append("source_hash")
    expected_cases = cases_doc.get("cases", [])
    observed = raw.get("results", [])
    if [r.get("id") for r in observed] != [c.get("id") for c in expected_cases]:
        errors.append("case_identity_or_order")
    for case, result in zip(expected_cases, observed):
        times = [case.get(key) for key in FIELDS]
        ordered = all(type(value) is int for value in times) and all(a <= b for a, b in zip(times, times[1:]))
        if phase == "baseline":
            # Baseline raw records the defect: it accepted both impossible rows.
            expected_ready = True
            expected_invalid = 0
        else:
            expected_ready = ordered
            expected_invalid = 0 if ordered else 1
        if result.get("expected_ready") is not case.get("expected_ready"):
            errors.append(f"expected_label:{case['id']}")
        if result.get("measurement_ready") is not expected_ready:
            errors.append(f"readiness:{case['id']}")
        if result.get("invalid_release_count") != expected_invalid:
            errors.append(f"invalid_release_count:{case['id']}")
        if result.get("hold_count") != (1 if expected_ready else 0):
            errors.append(f"hold_count:{case['id']}")
        if result.get("unmatched_admission_count") != 0:
            errors.append(f"unmatched_admission_count:{case['id']}")
    expected_count = len(expected_cases)
    if len(observed) != expected_count:
        errors.append("result_count")
    if errors:
        status = "STOP_AUDIT_INTEGRITY"
    elif phase == "baseline":
        status = "FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED"
    else:
        status = "PASS_ORDER_GATE_CONSTRUCTION_SCOPED"
    return {"schema": "owner-keyup-timestamp-order-audit-v1", "phase": phase,
            "status": status, "integrity_errors": errors,
            "case_count": len(observed),
            "false_accept_ids": [r["id"] for r in observed
                                 if r.get("expected_ready") is False and r.get("measurement_ready") is True]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--phase", choices=("baseline", "repaired"), required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.cases, args.raw, args.source, args.phase)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 1 if result["status"] == "STOP_AUDIT_INTEGRITY" else 0


if __name__ == "__main__":
    raise SystemExit(main())
