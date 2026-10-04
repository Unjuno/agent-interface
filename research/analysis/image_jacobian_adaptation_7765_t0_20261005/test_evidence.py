import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).parent


class RetainedEvidenceTests(unittest.TestCase):
    def test_raw_hash_and_independent_audit_are_retained(self):
        raw = ROOT / "formal_01/RAW.jsonl"
        audit = json.loads((ROOT / "formal_01/AUDIT.json").read_text())
        receipt = json.loads((ROOT / "formal_01/CANDIDATE_RECEIPT.json").read_text())
        self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(), receipt["sha256"])
        self.assertEqual(audit["raw_sha256"], receipt["sha256"])
        self.assertEqual(audit["rows"], 240)
        self.assertEqual(audit["errors"], [])
        self.assertEqual(audit["status"], "PASS_METHOD_SCOPED")

    def test_scientific_hold_is_explicit_and_preserved(self):
        text = (ROOT / "formal_01/DISPOSITION.txt").read_text()
        report = (ROOT / "REPORT.md").read_text()
        self.assertTrue(text.startswith("HOLD_METHOD_DESIGN_CONFOUNDED"))
        self.assertIn("0.48", report)
        self.assertIn("0.75", report)
        self.assertIn("not promoted", report)


if __name__ == "__main__":
    unittest.main()
