"""Construction-only tests over inline synthetic inputs; never reads fixtures.json."""
import unittest

from candidate import initial_freezes, unfreeze_step


class ContractTests(unittest.TestCase):
    def test_count_and_ordinal_policies_can_rank_routes_oppositely(self):
        fixture = {
            "history": {"exposures_per_route": 8},
            "policy": {"weights": {"ok": 0, "recoverable": 1, "severe": 4, "catastrophic": 10},
                       "unweighted_count_threshold": 6, "ordinal_severity_threshold": 11},
        }
        rows = ([{"route": "route-a", "outcome": "recoverable"}] * 8
                + [{"route": "route-b", "outcome": "catastrophic"}, {"route": "route-b", "outcome": "recoverable"}]
                + [{"route": "route-b", "outcome": "ok"}] * 6)
        count, _ = initial_freezes(rows, fixture, "UNWEIGHTED_COUNT")
        ordinal, _ = initial_freezes(rows, fixture, "ORDINAL_SEVERITY")
        hard, _ = initial_freezes(rows, fixture, "HARD_CATASTROPHIC")
        self.assertEqual(count, {"route-a": True})
        self.assertEqual(ordinal, {"route-b": True})
        self.assertEqual(hard, {"route-b": True})

    def test_current_generation_quorum_unfreezes_after_second_probe(self):
        probes = [
            {"step": 4, "generation": "g1", "positive": True, "source_verified": True},
            {"step": 5, "generation": "g1", "positive": True, "source_verified": True},
        ]
        self.assertEqual(unfreeze_step(probes, "g1", 2, 8), 6)

    def test_stale_or_unverified_probe_does_not_unfreeze(self):
        probes = [
            {"step": 4, "generation": "old", "positive": True, "source_verified": True},
            {"step": 5, "generation": "g1", "positive": True, "source_verified": False},
        ]
        self.assertIsNone(unfreeze_step(probes, "g1", 2, 8))


if __name__ == "__main__":
    unittest.main()
