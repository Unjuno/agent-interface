import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


class CandidateConstructionTests(unittest.TestCase):
    def run_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(HERE / "candidate.py"),
                    "--fixture",
                    str(HERE / "fixture.json"),
                    "--output",
                    str(output),
                ],
                cwd=HERE,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(output.read_text(encoding="utf-8"))

    def test_safe_separator_resolves_spurious_loss_with_one_predicate(self):
        rows = {row["case_id"]: row for row in self.run_candidate()["cases"]}
        row = rows["spurious_loss_safe_separator"]
        self.assertEqual(row["coarse"]["verdict"], "NOT_RECOVERABLE")
        self.assertEqual(row["fixed_fine"]["verdict"], "RECOVERABLE")
        self.assertEqual(row["cegar"]["verdict"], "RECOVERABLE")
        self.assertEqual(row["cegar"]["predicates_used"], ["p_color"])

    def test_false_recovery_without_safe_separator_abstains(self):
        rows = {row["case_id"]: row for row in self.run_candidate()["cases"]}
        row = rows["spurious_recovery_unsafe_only_separator"]
        self.assertEqual(row["coarse"]["verdict"], "RECOVERABLE")
        self.assertEqual(row["fixed_fine"]["verdict"], "NOT_RECOVERABLE")
        self.assertEqual(row["cegar"]["verdict"], "UNKNOWN")
        self.assertEqual(row["cegar"]["predicates_used"], [])
        self.assertNotIn("p_secret", row["cegar"]["predicates_used"])

    def test_genuine_loss_and_action_equivalent_aliases_are_not_overrefined(self):
        rows = {row["case_id"]: row for row in self.run_candidate()["cases"]}
        self.assertEqual(rows["genuine_nonrecoverable"]["cegar"]["verdict"], "NOT_RECOVERABLE")
        self.assertEqual(rows["genuine_nonrecoverable"]["cegar"]["predicates_used"], [])
        self.assertEqual(rows["action_equivalent_aliases"]["cegar"]["verdict"], "RECOVERABLE")
        self.assertEqual(rows["action_equivalent_aliases"]["cegar"]["predicates_used"], [])

    def test_deadline_case_does_not_claim_recovery(self):
        rows = {row["case_id"]: row for row in self.run_candidate()["cases"]}
        row = rows["deadline_exhaustion"]
        self.assertEqual(row["fixed_fine"]["verdict"], "NOT_RECOVERABLE")
        self.assertEqual(row["cegar"]["verdict"], "NOT_RECOVERABLE")


if __name__ == "__main__":
    unittest.main()
