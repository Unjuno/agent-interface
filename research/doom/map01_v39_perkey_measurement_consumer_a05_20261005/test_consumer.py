"""Exact per-row identity typing regressions for the retained A03 pair."""
import copy
import json
import unittest
from pathlib import Path

import audit
import candidate

HERE = Path(__file__).resolve().parent
A03_INPUT = (HERE.parent / "map01_v39_perkey_measurement_consumer_a03_20261005"
             / "INPUT_EVENTS.jsonl")
EVENTS = [json.loads(line) for line in A03_INPUT.read_text(encoding="utf-8").splitlines()
          if line]


class ExactPairIdentityTests(unittest.TestCase):
    def test_retained_pair_has_matching_exact_identity(self):
        expected = ("cover-7", 2, "14516f1944ff48bb8a05bc16e5de8a79",
                    "intent-v39-a01", "F8")
        self.assertEqual(candidate.row_identity(EVENTS), expected)
        self.assertEqual(audit.independently_reconstruct(EVENTS), expected)

    def test_equal_float_in_up_step_is_rejected(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["step"] = float(rows[0]["step"])
        with self.assertRaises(candidate.EvidenceError):
            candidate.row_identity(rows)
        with self.assertRaises(ValueError):
            audit.independently_reconstruct(rows)

    def test_equal_boolean_alias_across_rows_is_rejected(self):
        rows = copy.deepcopy(EVENTS)
        rows[0]["step"], rows[1]["step"] = 1, True
        with self.assertRaises(candidate.EvidenceError):
            candidate.row_identity(rows)
        with self.assertRaises(ValueError):
            audit.independently_reconstruct(rows)

    def test_owner_identity_mismatch_is_rejected(self):
        rows = copy.deepcopy(EVENTS)
        rows[1]["owner_id"] = "other-owner"
        with self.assertRaises(candidate.EvidenceError):
            candidate.row_identity(rows)
        with self.assertRaises(ValueError):
            audit.independently_reconstruct(rows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
