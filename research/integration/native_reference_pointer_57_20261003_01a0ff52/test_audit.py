"""Mutated evidence must not pass the separate raw-only oracle."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from audit import audit

ROOT = Path(__file__).resolve().parent


class AuditControls(unittest.TestCase):
    def setUp(self):
        self.fixtures = (ROOT / "fixtures.json").read_bytes()
        self.raw = json.loads((ROOT / "execution/fixed-raw.json").read_bytes())
        self.sha = self.raw["source_sha256"]

    def check(self, raw):
        return audit(raw, self.fixtures, self.sha)

    def test_retained_clean_control(self):
        result = self.check(self.raw)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["violations"], [])

    def test_corrupted_evidence_is_rejected(self):
        returned = next(i for i, row in enumerate(self.raw["rows"]) if row["status"] == "returned")
        rejected = next(i for i, row in enumerate(self.raw["rows"]) if row["status"] == "exception")
        for mutation in ("remove_row", "duplicate_row", "wrong_id", "source", "fixture",
                         "exception", "output", "input_mutated", "unknown_field"):
            raw = copy.deepcopy(self.raw)
            if mutation == "remove_row":
                raw["rows"].pop()
            elif mutation == "duplicate_row":
                raw["rows"][-1] = copy.deepcopy(raw["rows"][0])
            elif mutation == "wrong_id":
                raw["rows"][0]["id"] = "foreign"
            elif mutation == "source":
                raw["source_sha256"] = "0" * 64
            elif mutation == "fixture":
                raw["fixture_sha256"] = "0" * 64
            elif mutation == "exception":
                raw["rows"][rejected]["exception"] = "IndexError"
            elif mutation == "output":
                raw["rows"][returned]["output"]["native_result"]["observation"]["sequence"] = 99
            elif mutation == "input_mutated":
                raw["rows"][0]["input_unchanged"] = False
            else:
                raw["rows"][0]["fabricated"] = True
            with self.subTest(mutation=mutation):
                result = self.check(raw)
                self.assertTrue(result["errors"] or result["violations"])


if __name__ == "__main__":
    unittest.main()
