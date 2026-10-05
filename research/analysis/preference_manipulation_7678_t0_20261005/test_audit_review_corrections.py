import copy
import unittest

from audit import (
    candidate_domain_matches,
    encode_preference,
    expected_world_rows,
    rank_vector_orders,
    report_domain,
)


class IndependentDomainReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {
            "principals": ["p0", "p1"],
            "partial_information_mask": ["a", "b"],
            "report_masks": [["a", "b"], []],
        }
        self.orders = rank_vector_orders(["a", "b"])
        self.reports = report_domain(self.orders, self.fixture["report_masks"])
        self.document = {
            "orders": [
                {"order_id": f"O{i:02d}", "tiers": [list(t) for t in tiers],
                 "preference": encode_preference(tiers)}
                for i, (tiers, _) in enumerate(self.orders)
            ],
            "reports": self.reports,
            "worlds": expected_world_rows(self.fixture, self.orders),
        }

    def test_reconstructed_rank_and_signal_maps_match_valid_domain(self):
        self.assertTrue(candidate_domain_matches(
            self.document, self.fixture, self.orders, self.reports
        ))

    def test_candidate_authored_order_tiers_cannot_change_utility_mapping(self):
        corrupted = copy.deepcopy(self.document)
        corrupted["orders"][0]["tiers"] = [["b"], ["a"]]
        self.assertFalse(candidate_domain_matches(
            corrupted, self.fixture, self.orders, self.reports
        ))

    def test_candidate_authored_partial_signals_cannot_change_information_cells(self):
        corrupted = copy.deepcopy(self.document)
        corrupted["worlds"][0]["partial_signals"]["0"] = {
            "strict": [], "ties": []
        }
        self.assertFalse(candidate_domain_matches(
            corrupted, self.fixture, self.orders, self.reports
        ))


if __name__ == "__main__":
    unittest.main()
