import copy
import json
import unittest
from pathlib import Path

from .audit import validate


class AmmoValidityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((Path(__file__).parent / "RESULT.json").read_text(encoding="utf-8"))

    def test_sequential_soft_to_hard_boundary(self):
        self.assertTrue(validate(self.result))

    def test_early_drop_mutation_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["rows"][0]["disposition"] = "hard_invalidation"
        with self.assertRaisesRegex(ValueError, "boundary mismatch"):
            validate(result)

    def test_zero_ammo_soft_mutation_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["rows"][2]["disposition"] = "soft_change"
        with self.assertRaisesRegex(ValueError, "boundary mismatch"):
            validate(result)

    def test_soft_event_count_mutation_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["rows"][1]["soft_event_count"] = 1
        with self.assertRaisesRegex(ValueError, "boundary mismatch"):
            validate(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
