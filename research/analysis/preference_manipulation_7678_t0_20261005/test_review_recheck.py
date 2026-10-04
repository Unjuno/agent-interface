import copy
import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "results/review-correction-04"))
from audit import order_preference, rank_vector_orders, report_domain
from recheck_sincere_reports import sincere_metadata_mismatches


class SincereReportRecheckTests(unittest.TestCase):
    def setUp(self):
        self.orders = rank_vector_orders(["a", "b"])
        self.reports = report_domain(self.orders, [["a", "b"], []])
        self.document = {"deviations": []}
        for indices in itertools.product(range(len(self.orders)), repeat=2):
            for reporter in range(2):
                expected = next(row["report_id"] for row in self.reports
                                if row["label"] == "full"
                                and row["preference"] == order_preference(self.orders[indices[reporter]][0]))
                for report in self.reports:
                    self.document["deviations"].append({
                        "order_indices": list(indices), "reporter": reporter,
                        "report_id": report["report_id"], "sincere_report_id": expected,
                        "is_sincere": report["report_id"] == expected,
                    })

    def test_reconstructed_sincere_ids_accept_valid_document(self):
        self.assertEqual(sincere_metadata_mismatches(self.document, self.orders, self.reports), [])

    def test_candidate_chosen_sincere_ids_are_rejected(self):
        damaged = copy.deepcopy(self.document)
        first = damaged["deviations"][0]
        first["sincere_report_id"] = next(
            row["report_id"] for row in self.reports
            if row["report_id"] != first["sincere_report_id"]
        )
        self.assertTrue(sincere_metadata_mismatches(damaged, self.orders, self.reports))

    def test_sincerity_flag_is_reconstructed_too(self):
        damaged = copy.deepcopy(self.document)
        damaged["deviations"][0]["is_sincere"] = not damaged["deviations"][0]["is_sincere"]
        self.assertTrue(sincere_metadata_mismatches(damaged, self.orders, self.reports))


if __name__ == "__main__":
    unittest.main()
