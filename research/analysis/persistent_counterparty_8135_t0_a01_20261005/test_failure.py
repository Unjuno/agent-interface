import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class PreservedFailureTests(unittest.TestCase):
    def test_one_shot_candidate_and_auditor_schema_failure(self):
        record = json.loads((ROOT / "RUN_RECORD.json").read_text())
        self.assertEqual((record["candidate_invocations"], record["auditor_invocations"], record["retries"]), (1, 1, 0))
        self.assertEqual((record["candidate_exit"], record["auditor_exit"]), (0, 1))
        self.assertEqual(record["state"], "FAIL_OR_STOP_AUDITOR")
        self.assertTrue((ROOT / "results/candidate-out/candidate.json").is_file())
        self.assertFalse((ROOT / "results/audit-out/audit.json").exists())
        self.assertIn("episode_field_set", (ROOT / "results/auditor.stderr.txt").read_text())


if __name__ == "__main__":
    unittest.main()
