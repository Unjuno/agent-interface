import copy
import json
import unittest
from pathlib import Path

from audit_raw import audit
from run_candidate import run

ROOT = Path(__file__).parent
CASES = json.loads((ROOT / "cases.json").read_text())


class RawAuditTests(unittest.TestCase):
    def test_candidate_raw_reconstructs(self):
        result = audit(CASES, run(CASES))
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED", result["errors"])

    def test_rejects_common_mode_wrong_action(self):
        raw = run(CASES)
        row = next(r for r in raw["rows"] if r["case_id"] == "common_mode_wrong_agreement" and r["arm"] == "agreement_lease")
        row["actions"] = ["advance"]
        row["decision_ticks"] = [0]
        self.assertEqual(audit(CASES, raw)["status"], "FAIL_METHOD")

    def test_rejects_missing_release_obligation(self):
        raw = run(CASES)
        raw["rows"][0]["release_required"] = False
        self.assertEqual(audit(CASES, raw)["status"], "FAIL_METHOD")

    def test_rejects_missing_case_arm(self):
        raw = run(CASES)
        raw["rows"].pop()
        self.assertEqual(audit(CASES, raw)["status"], "FAIL_METHOD")

    def test_rejects_duplicate_case_arm(self):
        raw = run(CASES)
        raw["rows"].append(copy.deepcopy(raw["rows"][0]))
        self.assertEqual(audit(CASES, raw)["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
