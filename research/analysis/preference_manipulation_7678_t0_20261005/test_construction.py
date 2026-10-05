import unittest

import candidate


class ConstructionTests(unittest.TestCase):
    def test_three_route_order_domain_has_thirteen_complete_weak_orders(self):
        class Canonical:
            @staticmethod
            def ordered_partitions(items):
                import itertools
                items = tuple(sorted(items))
                if not items:
                    yield ()
                    return
                for size in range(1, len(items) + 1):
                    for top in itertools.combinations(items, size):
                        remaining = tuple(item for item in items if item not in top)
                        for tail in Canonical.ordered_partitions(remaining):
                            yield (tuple(sorted(top)),) + tail

        orders, reports = candidate.report_domain(Canonical, {
            "routes": {"a": {}, "b": {}, "c": {}},
            "report_masks": [["a", "b", "c"], ["a", "b"], ["a", "c"], ["b", "c"], []],
        })
        self.assertEqual(13, len(orders))
        self.assertEqual(23, len(reports))
        self.assertEqual(len(reports), len({candidate.preference_key(r["preference"]) for r in reports}))

    def test_projection_drops_unobserved_comparisons_without_filling_them(self):
        order = (("a",), ("b",), ("c",))
        partial = candidate.project_order(order, ["a", "b"])
        self.assertEqual({"strict": [["a", "b"]], "ties": []}, partial)
        self.assertNotIn(["a", "c"], partial["strict"])
        self.assertNotIn(["b", "c"], partial["strict"])

    def test_tied_and_empty_reports_remain_distinct(self):
        order = (("a", "b", "c"),)
        self.assertEqual({"strict": [], "ties": [["a", "b"], ["a", "c"], ["b", "c"]]},
                         candidate.project_order(order, ["a", "b", "c"]))
        self.assertEqual({"strict": [], "ties": []}, candidate.project_order(order, []))


if __name__ == "__main__":
    unittest.main()
