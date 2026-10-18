"""Post-run package integrity checks; never re-runs candidate or auditor."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class RetainedEvidenceTests(unittest.TestCase):
    def test_all_frozen_inputs_match_freeze_manifest(self):
        freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
        for name, expected in freeze["frozen_sha256"].items():
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_candidate_and_auditor_receipts_are_one_shot_and_agree(self):
        candidate = json.loads((ROOT / "result/CANDIDATE_RECEIPT.json").read_text())
        auditor = json.loads((ROOT / "result/AUDITOR_RECEIPT.json").read_text())
        result = json.loads((ROOT / "result/RESULT.json").read_text())
        audit = json.loads((ROOT / "result/audit.json").read_text())
        self.assertEqual(candidate["execution_count"], 1)
        self.assertEqual(auditor["execution_count"], 1)
        self.assertEqual(candidate["exit_code"], 0)
        self.assertEqual(auditor["exit_code"], 0)
        self.assertEqual(audit["errors"], [])
        self.assertEqual(audit["method_status"], "PASS_METHOD_SCOPED")
        self.assertEqual(audit["hypothesis_status"], "H_PASS_SCOPED")
        self.assertEqual(result["method_status"], audit["method_status"])
        self.assertEqual(result["hypothesis_status"], audit["hypothesis_status"])
        self.assertEqual(result["raw_rows"], 108)
        self.assertEqual(len(audit["case_metrics"]), 108)
        self.assertEqual(audit["feasible_guard_deadline_failures"], [])
        self.assertFalse(result["container_run"])

    def test_raw_receipt_hashes_and_frozen_positive_subset(self):
        candidate = json.loads((ROOT / "result/CANDIDATE_RECEIPT.json").read_text())
        result = json.loads((ROOT / "result/RESULT.json").read_text())
        raw = (ROOT / "result/raw.jsonl").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), candidate["raw_sha256"])
        rows = [json.loads(line) for line in raw.splitlines() if line]
        self.assertEqual(len(rows), 108)
        self.assertEqual(len({row["row_id"] for row in rows}), 108)
        self.assertEqual(result["positive_slack_static_payload_units"], 192)
        self.assertEqual(result["positive_slack_guarded_payload_units"], 222)
        self.assertEqual(result["positive_slack_payload_delta"], 30)

    def test_package_sha256_manifest(self):
        lines = (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        self.assertTrue(lines)
        for line in lines:
            expected, name = line.split("  ", 1)
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)


if __name__ == "__main__":
    unittest.main()
