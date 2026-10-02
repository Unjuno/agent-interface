import copy
import json
import unittest
from pathlib import Path

from audit_raw import audit_rows


RAW = json.loads(Path(__file__).with_name("raw.json").read_text(encoding="utf-8"))


class RawAuditTests(unittest.TestCase):
    def test_accepts_exact_four_row_replay(self):
        self.assertEqual(audit_rows(RAW), [])

    def test_rejects_missing_policy_row(self):
        self.assertTrue(audit_rows(RAW[:-1]))

    def test_rejects_duplicate_tick(self):
        changed = copy.deepcopy(RAW)
        changed[1]["schedule"][1]["tick"] = 0
        self.assertTrue(audit_rows(changed))

    def test_rejects_false_verifier_completion(self):
        changed = copy.deepcopy(RAW)
        changed[1]["verifier"]["at"] = 5
        self.assertTrue(audit_rows(changed))

    def test_rejects_starvation_transferred_to_medium_job(self):
        changed = copy.deepcopy(RAW)
        row = changed[2]
        for step in row["schedule"]:
            if step["tick"] > 6:
                step["job"] = "U"
        self.assertTrue(audit_rows(changed))


if __name__ == "__main__":
    unittest.main()
