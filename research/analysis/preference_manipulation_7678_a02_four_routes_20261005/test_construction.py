"""No-allocation construction checks for the #7678 four-route A02 fixture."""
import json
import unittest
from pathlib import Path

import audit
import candidate

HERE = Path(__file__).resolve().parent


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
        cls.certificate = candidate.load_frozen(
            cls.fixture["candidate_path"], cls.fixture["candidate_sha256"],
            cls.fixture["source_commit"])

    def test_true_types_are_six_distinct_valid_weak_orders(self):
        orders = self.fixture["truth_orders"]
        self.assertEqual(len(orders), 6)
        self.assertEqual(len({json.dumps(x) for x in orders}), 6)
        for order in orders:
            self.assertEqual(sorted(route for tier in order for route in tier),
                             sorted(self.fixture["routes"]))

    def test_report_domains_agree_at_92_relations(self):
        _, candidate_reports = candidate.report_domain(self.certificate, self.fixture)
        oracle_reports = audit.independent_report_domain(self.fixture)
        self.assertEqual(candidate_reports, oracle_reports)
        self.assertEqual(len(candidate_reports), 92)
        self.assertEqual({row["label"] for row in candidate_reports},
                         {"full", "mask_abc", "mask_ab", "empty"})

    def test_deviation_matrix_size_is_frozen(self):
        self.assertEqual(6 * 6 * 2 * 92, 6624)


if __name__ == "__main__":
    unittest.main()
