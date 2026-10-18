import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("t5_audit", HERE / "audit.py")
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


class AuditTests(unittest.TestCase):
    def test_baseline_classifies_both_false_acceptances(self):
        result = audit_module.audit(HERE / "cases.json", HERE / "output/baseline_raw.json",
                                    HERE / "baseline/analyze_map01_direct_retained_input_v1.py", "baseline")
        self.assertEqual(result["status"], "FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED")
        self.assertEqual(result["integrity_errors"], [])
        self.assertEqual(result["false_accept_ids"], ["ack_before_admission", "release_return_before_start"])

    def test_repaired_classifies_all_four_rows(self):
        result = audit_module.audit(HERE / "cases.json", HERE / "output/repaired_raw.json",
                                    HERE / "repaired/analyze_map01_direct_retained_input_v1.py", "repaired")
        self.assertEqual(result["status"], "PASS_ORDER_GATE_CONSTRUCTION_SCOPED")
        self.assertEqual(result["integrity_errors"], [])

    def test_mutated_repaired_finding_fails_audit(self):
        raw = json.loads((HERE / "output/repaired_raw.json").read_text(encoding="utf-8"))
        raw["results"][2]["measurement_ready"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mutated.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            result = audit_module.audit(HERE / "cases.json", path,
                                        HERE / "repaired/analyze_map01_direct_retained_input_v1.py", "repaired")
        self.assertEqual(result["status"], "STOP_AUDIT_INTEGRITY")
        self.assertIn("readiness:ack_before_admission", result["integrity_errors"])

    def test_mutated_case_bytes_fail_audit(self):
        raw = json.loads((HERE / "output/repaired_raw.json").read_text(encoding="utf-8"))
        cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        cases["cases"][0]["admitted_ns"] = 101
        with tempfile.TemporaryDirectory() as directory:
            case_path = Path(directory) / "cases.json"
            raw_path = Path(directory) / "raw.json"
            case_path.write_text(json.dumps(cases), encoding="utf-8")
            raw_path.write_text(json.dumps(raw), encoding="utf-8")
            result = audit_module.audit(case_path, raw_path,
                                        HERE / "repaired/analyze_map01_direct_retained_input_v1.py", "repaired")
        self.assertEqual(result["status"], "STOP_AUDIT_INTEGRITY")
        self.assertIn("cases_hash", result["integrity_errors"])


if __name__ == "__main__":
    unittest.main()
