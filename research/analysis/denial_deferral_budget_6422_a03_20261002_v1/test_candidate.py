import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class DeferralBudgetContractTests(unittest.TestCase):
    def test_only_one_scoped_fresh_request_is_presented_and_effect_is_never_authorized(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.json"
            run = subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--input", str(ROOT / "fixtures.json"), "--output", str(out)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads(out.read_text(encoding="utf-8"))
        rows = {row["case_id"]: row for row in result["rows"]}
        self.assertEqual(rows["first-permitted"]["bounded"]["decision"], "ASK_FRESH_APPROVAL")
        self.assertEqual(rows["first-permitted"]["bounded"]["fresh_request"]["label"], "FRESH_APPROVAL_AFTER_STATED_DEFERRAL")
        self.assertEqual(rows["first-permitted"]["bounded"]["post_consumed_evidence_ids"], ["receipt-A"])
        self.assertEqual(rows["repeat-budget-exhausted"]["unbounded"]["decision"], "ASK_FRESH_APPROVAL")
        self.assertEqual(rows["repeat-budget-exhausted"]["bounded"]["decision"], "HOLD_BUDGET_EXHAUSTED")
        self.assertEqual(rows["same-evidence-replay-new-request-id"]["unbounded"]["decision"], "ASK_FRESH_APPROVAL")
        self.assertEqual(rows["same-evidence-replay-new-request-id"]["bounded"]["decision"], "HOLD_EVIDENCE_ALREADY_CONSUMED")
        self.assertEqual(rows["same-evidence-replay-new-request-id"]["case"]["request_id"], "req-99")
        self.assertEqual(rows["new-evidence-first-use"]["bounded"]["decision"], "ASK_FRESH_APPROVAL")
        for case_id in ("observer-not-source", "condition-not-source-stated", "agent-asserted", "budget-unbound"):
            self.assertEqual(rows[case_id]["bounded"]["decision"], "HOLD_DEFERRAL_NOT_ELIGIBLE")
        self.assertEqual(rows["safety-release-at-cap"]["bounded"]["decision"], "ALLOW_SAFETY_RELEASE")
        self.assertTrue(all(row["bounded"]["effect_authorized"] is False for row in rows.values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
