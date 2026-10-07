import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("auditor", ROOT / "audit.py")
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)
cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
source_sha = hashlib.sha256((ROOT / "source/analyze_map01_direct_retained_input_v1.py").read_bytes()).hexdigest()


def make_raw():
    rows = []
    for case in cases["cases"]:
        lower = (case["release_call_started_ns"]-case["input_ack_ns"])/1e6
        upper = (case["release_call_returned_ns"]-case["admitted_ns"])/1e6
        rows.append({"case_id":case["id"], "analyzer_output":{
            "measurement_ready":True,
            "holds":[{"retained_lower_ms":lower,"retained_upper_ms":upper}],
        }})
    return {"schema":"owner-keyup-timestamp-order-raw-v1",
            "allocation":cases["allocation"], "analyzer_sha256":source_sha, "rows":rows}


class AuditorClassificationPreflight(unittest.TestCase):
    def test_observed_invalid_orders_are_findings_not_integrity_errors(self):
        errors, findings = auditor.classify(cases, make_raw(), source_sha)
        self.assertEqual(errors, [])
        self.assertEqual(findings, ["readiness_mismatch:ack_before_admission", "readiness_mismatch:release_return_before_start"])
        self.assertEqual(auditor.hypothesis_outcome(findings), "FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED")

    def test_joint_classification_mutation_changes_disposition(self):
        raw = make_raw()
        for case_id in ("ack_before_admission", "release_return_before_start"):
            next(row for row in raw["rows"] if row["case_id"] == case_id)["analyzer_output"]["measurement_ready"] = False
        errors, findings = auditor.classify(cases, raw, source_sha)
        self.assertEqual(errors, [])
        self.assertEqual(findings, [])
        self.assertEqual(auditor.hypothesis_outcome(findings), "PASS_ORDER_GATE_SCOPED")

    def test_missing_row_is_integrity_error(self):
        raw = make_raw(); raw["rows"].pop()
        errors, _ = auditor.classify(cases, raw, source_sha)
        self.assertIn("row_inventory", errors)

    def test_wrong_source_is_integrity_error(self):
        raw = make_raw(); raw["analyzer_sha256"] = "0"*64
        errors, _ = auditor.classify(cases, raw, source_sha)
        self.assertIn("analyzer_identity", errors)

    def test_bad_interval_is_integrity_error(self):
        raw = make_raw()
        raw["rows"][0]["analyzer_output"]["holds"][0]["retained_lower_ms"] += 1
        errors, _ = auditor.classify(cases, raw, source_sha)
        self.assertIn("bound_arithmetic:ordinary_order", errors)


if __name__ == "__main__":
    unittest.main()
