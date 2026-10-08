import itertools
import json
import unittest
from pathlib import Path

import candidate
import oracle

HERE = Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / "fixture.json").read_text())


class ConstructionChecks(unittest.TestCase):
    def test_rank_vector_oracle_covers_all_13_weak_orders(self):
        expected = list(candidate.load_certificate().ordered_partitions(["a", "b", "c"]))
        actual = oracle.weak_orders(["a", "b", "c"])
        self.assertEqual(len(actual), 13)
        self.assertEqual(set(actual), set(expected))

    def test_report_domain_has_23_unique_preferences(self):
        orders = sorted(candidate.load_certificate().ordered_partitions(["a", "b", "c"]))
        reports = {
            candidate.key(candidate.project(order, mask))
            for order in orders
            for mask in FIXTURE["report_masks"]
        }
        self.assertEqual(len(reports), 23)

    def test_independent_certificate_matches_representative_profiles(self):
        cert = candidate.load_certificate()
        orders = sorted(cert.ordered_partitions(["a", "b", "c"]))
        samples = [
            (candidate.encode_order(orders[0]), candidate.encode_order(orders[-1])),
            (
                {"strict": [["a", "b"]], "ties": []},
                candidate.encode_order(orders[4]),
            ),
        ]
        for left, right in samples:
            prefs = {"principal_0": left, "principal_1": right}
            got = candidate.evaluate(cert, FIXTURE, prefs, FIXTURE["decision_maker"])
            want = oracle.signature(oracle.certificate(FIXTURE, prefs, FIXTURE["decision_maker"]))
            self.assertEqual(got, want)

    def test_oracle_enumeration_is_deterministic(self):
        first = oracle.weak_orders(["c", "a", "b"])
        second = oracle.weak_orders(["a", "b", "c"])
        self.assertEqual(first, second)
        self.assertEqual(len(list(itertools.product(first, repeat=2))), 169)


if __name__ == "__main__":
    unittest.main()
