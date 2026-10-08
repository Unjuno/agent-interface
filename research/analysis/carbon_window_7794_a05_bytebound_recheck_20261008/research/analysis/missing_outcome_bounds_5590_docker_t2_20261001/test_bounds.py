from __future__ import annotations

import copy
import json
import unittest
from fractions import Fraction
from pathlib import Path

from audit import audit
from candidate import compute


ROOT = Path(__file__).parent


class BoundsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads((ROOT / "ledger.json").read_text(encoding="utf-8"))
        cls.raw = compute(cls.ledger)

    def test_frozen_example_has_distinct_decisions(self):
        self.assertEqual(self.raw["observed_only"]["numerator"], 6)
        self.assertEqual(Fraction(self.raw["observed_only"]["numerator"],
                                  self.raw["observed_only"]["denominator"]), Fraction(6, 7))
        self.assertEqual(self.raw["observed_only"]["decision"], "PROMOTE")
        self.assertEqual(self.raw["missing_as_failure"]["decision"], "DO_NOT_PROMOTE")
        self.assertEqual(self.raw["sharp_bounds"]["decision"], "PROMOTION_UNIDENTIFIED")

    def test_all_compatible_completions_are_enumerated(self):
        items = self.raw["compatible_completions"]
        self.assertEqual(len(items), 8)
        rates = [Fraction(x["rate"]["numerator"], x["rate"]["denominator"]) for x in items]
        self.assertEqual(min(rates), Fraction(3, 5))
        self.assertEqual(max(rates), Fraction(9, 10))

    def test_independent_audit_accepts_raw(self):
        result = audit(self.ledger, self.raw)
        self.assertEqual(result["status"], "PASS_BOUNDS_SCOPED")

    def test_drop_unresolved_row_from_denominator_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["denominator"] -= 1
        with self.assertRaisesRegex(ValueError, "denominator mismatch"):
            audit(self.ledger, bad)

    def test_relabel_missing_as_failure_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["counts"]["failure"] += 1
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            audit(self.ledger, bad)

    def test_duplicate_identity_is_rejected(self):
        bad = copy.deepcopy(self.ledger)
        bad["episodes"][1]["episode_id"] = bad["episodes"][0]["episode_id"]
        with self.assertRaisesRegex(ValueError, "duplicate row identity"):
            audit(bad, self.raw)

    def test_threshold_boolean_is_rejected(self):
        bad = copy.deepcopy(self.ledger)
        bad["promotion_threshold"]["numerator"] = True
        with self.assertRaisesRegex(ValueError, "invalid threshold encoding"):
            audit(bad, self.raw)

    def test_duplicate_completion_mask_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["compatible_completions"][-1] = copy.deepcopy(bad["compatible_completions"][-2])
        with self.assertRaisesRegex(ValueError, "duplicate compatible completion"):
            audit(self.ledger, bad)


if __name__ == "__main__":
    unittest.main()
