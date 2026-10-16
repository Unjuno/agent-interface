"""Reject an incomplete or unequal scientific block before native work."""
import copy
import json
from pathlib import Path
import unittest

from producer import check_plan


class PlanTests(unittest.TestCase):
    def test_complete_finite_family_is_eligible(self):
        check_plan(json.loads(Path(__file__).with_name("fixture.json").read_text()))

    def test_missing_duplicate_and_wrong_budget_are_refused(self):
        original = json.loads(Path(__file__).with_name("fixture.json").read_text())
        variants = []
        f = copy.deepcopy(original); f["cases"].pop(); variants.append(f)
        f = copy.deepcopy(original); f["cases"][5] = f["cases"][4]; variants.append(f)
        f = copy.deepcopy(original); f["cases"][3]["offsets"] = [0, 0, 0, True]; variants.append(f)
        f = copy.deepcopy(original); f["samples_per_cell"] = 9; variants.append(f)
        for i, f in enumerate(variants):
            with self.subTest(i=i):
                with self.assertRaises(ValueError):
                    check_plan(f)


if __name__ == "__main__":
    unittest.main()
