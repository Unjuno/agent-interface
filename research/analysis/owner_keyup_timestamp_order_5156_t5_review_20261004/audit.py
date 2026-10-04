"""Review-only classification of immutable T4 raw; never reruns candidate."""
import importlib.util
import json
import sys
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


def main():
    root = Path(__file__).resolve().parents[1]
    t4 = root / "owner_keyup_timestamp_order_5156_t4_20261004"
    cases_doc = json.loads((t4 / "cases.json").read_text())
    raw = json.loads((t4 / "output/raw.json").read_text())
    predecessor = load_predecessor(t4 / "audit.py")
    import hashlib
    source_hash = hashlib.sha256((t4 / "source/analyze_map01_direct_retained_input_v1.py").read_bytes()).hexdigest()
    errors, findings = predecessor.classify(cases_doc, raw, source_hash)
    outcomes, positive, negative = disposition(cases_doc["cases"], findings)
    result = {"schema": "owner-keyup-timestamp-order-t5-review-v1",
              "input": "T4 immutable output/raw.json", "integrity_errors": errors,
              "positive_control_failure_case_ids": positive,
              "negative_acceptance_case_ids": negative,
              "scientific_outcomes": outcomes}
    print(json.dumps(result, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
