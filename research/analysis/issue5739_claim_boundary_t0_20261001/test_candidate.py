import json
import unittest
from pathlib import Path

from candidate import build_result

ROOT = Path(__file__).resolve().parent


class CandidateConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.screen = json.loads((ROOT / "screen.json").read_text(encoding="utf-8"))
        cls.confirmatory = json.loads((ROOT / "confirmatory.json").read_text(encoding="utf-8"))
        cls.result = build_result(cls.screen, cls.confirmatory)

    def test_survivor_family_promotion_is_withheld(self):
        self.assertEqual(self.result["family"]["members"], ["B", "C", "E"])
        self.assertEqual(self.result["family"]["claim"], "WITHHELD_NO_FAMILYWISE_INFERENCE")

    def test_screened_arm_is_not_claimed_global_best(self):
        self.assertEqual(self.result["screened_out"], ["D"])
        self.assertEqual(self.result["global_best_claim"], "NOT_ESTABLISHED_SCREENED_ARM_NOT_CONFIRMED")

    def test_hard_safety_failure_overrides_fastest_latency(self):
        self.assertEqual(self.result["per_arm"]["E"]["disposition"], "WITHHOLD_HARD_SAFETY_FAILURE")
        self.assertEqual(self.result["promotion"], "WITHHELD")

    def test_shared_cohort_has_four_unique_variants_per_survivor(self):
        rows = self.result["confirm_attempts"]
        for arm in ("B", "C"):
            variants = [row["variant"] for row in rows if row["arm"] == arm]
            self.assertEqual(variants, ["v1", "v2", "v3", "v4"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
