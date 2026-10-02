import copy
import json
import unittest
from pathlib import Path

from candidate import run
from audit import verify


class MethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (Path(__file__).parent / "cases.json").open(encoding="utf-8") as f:
            cls.fixture = json.load(f)
        cls.raw = run(cls.fixture)

    def test_denominator_and_independent_reconstruction(self):
        errors, metrics, rows = verify(self.fixture, self.raw)
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 12)
        self.assertEqual(metrics["mutation_controls_rejected"], 5)

    def test_bad_receipt_and_pixels_are_detected(self):
        bad = copy.deepcopy(self.raw)
        bad["rows"][0]["receipt"]["delivery"] = "failed"
        self.assertTrue(verify(self.fixture, bad)[0])
        bad = copy.deepcopy(self.raw)
        bad["rows"][0]["frames"][1][12][16] = 0
        self.assertTrue(verify(self.fixture, bad)[0])

    def test_unknown_or_stale_delivery_does_not_get_transform_binding(self):
        for row in self.raw["rows"]:
            if not row["receipt"]["valid"]:
                self.assertEqual(row["predicted_dx"], 0)

    def test_all_alarms_respect_declared_budget(self):
        for row in self.raw["rows"]:
            for mask in row["alarms"].values():
                self.assertLessEqual(sum(map(sum, mask)), self.fixture["alarm_budget_cells"])


if __name__ == "__main__":
    unittest.main()
