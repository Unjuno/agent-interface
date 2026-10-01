import copy
import json
import unittest
from pathlib import Path

from audit import audit_raw
from candidate import build_result

ROOT = Path(__file__).resolve().parent
SCREEN = json.loads((ROOT / "screen.json").read_text(encoding="utf-8"))
CONFIRM = json.loads((ROOT / "confirmatory.json").read_text(encoding="utf-8"))
ORACLE = json.loads((ROOT / "sealed_oracle.json").read_text(encoding="utf-8"))


class IndependentAuditMutationTests(unittest.TestCase):
    def setUp(self):
        self.raw = build_result(SCREEN, CONFIRM)

    def assertRejected(self):
        self.assertTrue(audit_raw(SCREEN, CONFIRM, ORACLE, self.raw))

    def test_pristine_candidate_reconstructs(self):
        self.assertEqual(audit_raw(SCREEN, CONFIRM, ORACLE, self.raw), [])

    def test_missing_attempt_rejected(self):
        self.raw["confirm_attempts"].pop()
        self.assertRejected()

    def test_duplicate_attempt_rejected(self):
        self.raw["confirm_attempts"].append(copy.deepcopy(self.raw["confirm_attempts"][0]))
        self.assertRejected()

    def test_repeated_sealed_variant_rejected(self):
        row = next(item for item in self.raw["confirm_attempts"] if item["arm"] == "B" and item["variant"] == "v2")
        row["variant"] = "v1"
        self.assertRejected()

    def test_altered_comparison_family_rejected(self):
        self.raw["family"]["family_id"] = "other-family"
        self.assertRejected()

    def test_forged_safety_record_rejected(self):
        row = next(item for item in self.raw["confirm_attempts"] if item["arm"] == "E" and item["variant"] == "v2")
        row["hard_safety_violation"] = False
        self.assertRejected()


if __name__ == "__main__":
    unittest.main(verbosity=2)
