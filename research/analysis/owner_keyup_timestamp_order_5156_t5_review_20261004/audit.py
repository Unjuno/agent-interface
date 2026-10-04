"""Review-only classification of immutable T4 raw; never reruns candidate."""
import importlib.util
import copy
import hashlib
import json
from pathlib import Path


def load_predecessor(path):
    spec = importlib.util.spec_from_file_location("t4_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def disposition(cases, findings):
    expected = {c["id"]: c["expected_ready"] for c in cases}
    positive = sorted(f.split(":", 1)[1] for f in findings
                      if expected.get(f.split(":", 1)[1]) is True)
    negative = sorted(f.split(":", 1)[1] for f in findings
                      if expected.get(f.split(":", 1)[1]) is False)
    outcomes = []
    if positive:
        outcomes.append("FAIL_POSITIVE_CONTROL")
    if negative:
        outcomes.append("FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED")
    return outcomes or ["PASS_ORDER_GATE_SCOPED"], positive, negative


def validate_raw(cases_doc, raw, t4):
    """Bind every retained row to a fresh reconstruction from frozen cases/source."""
    errors = []
    source = t4 / "source/analyze_map01_direct_retained_input_v1.py"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if raw.get("schema") != "owner-keyup-timestamp-order-raw-v1":
        errors.append("raw_schema")
    if raw.get("allocation") != cases_doc.get("allocation"):
        errors.append("allocation")
    if raw.get("analyzer_sha256") != source_hash:
        errors.append("analyzer_identity")
    analyzer = load_predecessor(source)
    expected_rows = []
    for case in cases_doc["cases"]:
        events = [
            {"event": "input_admission", "intent_token": "frozen-intent", "key": "Up",
             "admitted_ns": case["admitted_ns"], "input_ack_ns": case["input_ack_ns"]},
            {"event": "input_release_transition", "intent_token": "frozen-intent",
             "operation": "up", "key": "Up",
             "release_call_started_ns": case["release_call_started_ns"],
             "release_call_returned_ns": case["release_call_returned_ns"],
             "owner_transition_verified": True},
        ]
        expected_rows.append({"case_id": case["id"], "events": events,
                              "analyzer_output": analyzer.analyze(events)})
    if raw.get("rows") != expected_rows:
        errors.append("raw_rows_not_bound_to_frozen_cases_and_source")
    return errors, expected_rows


def main():
    root = Path(__file__).resolve().parents[1]
    t4 = root / "owner_keyup_timestamp_order_5156_t4_20261004"
    cases_doc = json.loads((t4 / "cases.json").read_text())
    raw = json.loads((t4 / "output/raw.json").read_text())
    errors, expected_rows = validate_raw(cases_doc, raw, t4)
    findings = []
    for case, row in zip(cases_doc["cases"], raw.get("rows", [])):
        if isinstance(row, dict) and isinstance(row.get("analyzer_output"), dict):
            if row["analyzer_output"].get("measurement_ready") is not case["expected_ready"]:
                findings.append("readiness_mismatch:" + case["id"])
    outcomes, positive, negative = disposition(cases_doc["cases"], findings)
    result = {"schema": "owner-keyup-timestamp-order-t5-review-v1",
              "input": "T4 immutable output/raw.json", "integrity_errors": errors,
              "positive_control_failure_case_ids": positive,
              "negative_acceptance_case_ids": negative,
              "expected_row_count": len(expected_rows),
              "scientific_outcomes": outcomes}
    print(json.dumps(result, indent=2, sort_keys=True))
    if errors:
        print(json.dumps({"audit_status": "STOP_RAW_INTEGRITY", "errors": errors}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
