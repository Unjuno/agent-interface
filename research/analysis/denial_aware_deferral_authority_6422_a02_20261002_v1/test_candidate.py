import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class DeferralAuthorityTests(unittest.TestCase):
    def test_candidate_distinguishes_authorized_deferral_and_never_authorizes_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "raw.json"
            run = subprocess.run(
                [sys.executable, str(ROOT / "candidate.py"), "--input", str(ROOT / "fixtures.json"), "--output", str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
        rows = {row["case_id"]: row for row in data["rows"]}
        self.assertEqual(rows["authorized-valid"]["guarded"], "ASK_FRESH_APPROVAL")
        for case_id in ("observer-valid", "unknown-valid", "missing-authority", "wrong-predicate", "agent-asserted", "wrong-evidence-kind", "condition-not-source-stated"):
            self.assertEqual(rows[case_id]["guarded"], "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER")
        self.assertEqual(rows["observer-valid"]["a01_baseline"], "ASK_FRESH_APPROVAL")
        self.assertTrue(all(not row["effect_authorized"] for row in rows.values()))

    def test_literal_eight_case_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "raw.json"
            subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--input", str(ROOT / "fixtures.json"), "--output", str(output)], check=True)
            rows = json.loads(output.read_text(encoding="utf-8"))["rows"]
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({row["case_id"] for row in rows}), 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)

