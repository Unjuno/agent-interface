import itertools
import unittest

import audit


class ReferenceAuditTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            audit.reference_row(capacity, bits)
            for capacity in (2, 3)
            for bits in itertools.product((0, 1), repeat=4)
        ]

    def test_full_reference_population(self):
        self.assertEqual(audit.validate(self.rows), [])

    def test_missing_row_rejected(self):
        self.assertIn("row_count_or_unique_id_mismatch", audit.validate(self.rows[:-1]))

    def test_duplicate_row_rejected(self):
        self.assertIn("row_count_or_unique_id_mismatch", audit.validate(self.rows + [self.rows[0]]))

    def test_mutated_contract_decision_rejected(self):
        row = next(item for item in self.rows if item["capacity_per_tick"] == 2 and sum(item["hi_arrivals"]) == 1)
        row["temporal_contract"]["status"] = "SAT"
        self.assertTrue(audit.validate(self.rows))

    def test_required_observation_omission_rejected(self):
        row = next(item for item in self.rows if item["capacity_per_tick"] == 3 and sum(item["hi_arrivals"]) == 0)
        row["temporal_contract"]["dispatch"][0]["observer"] = 0
        self.assertTrue(audit.validate(self.rows))

    def test_planner_minimum_omission_rejected(self):
        row = next(item for item in self.rows if item["capacity_per_tick"] == 3 and sum(item["hi_arrivals"]) == 0)
        row["temporal_contract"]["dispatch"] = [
            {**entry, "planner": 0, "background": entry["background"] + entry["planner"]}
            for entry in row["temporal_contract"]["dispatch"]
        ]
        self.assertTrue(audit.validate(self.rows))


if __name__ == "__main__":
    unittest.main()
