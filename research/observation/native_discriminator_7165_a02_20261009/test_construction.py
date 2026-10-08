"""Construction checks; not the single formal candidate allocation."""
import unittest

from candidate import memory_gated


class ContractConstructionTests(unittest.TestCase):
    def setUp(self):
        self.fresh = {"title": "A", "parent": "A"}
        self.current = {"title": "CURRENT", "parent": "CURRENT"}

    def decide(self, *, requirement=("title", "parent"), generation=7,
               current=7, source=True, status=None, fresh=None):
        return memory_gated(
            requirement, generation, current, source,
            status or self.current, fresh or self.fresh,
        )

    def test_current_complete_consensus_uses_targeted_route(self):
        self.assertEqual(self.decide(), ("A", "targeted_current_complete"))

    def test_incomplete_requirement_falls_back(self):
        self.assertEqual(self.decide(requirement=("title",))[1], "fresh_full_fallback")

    def test_stale_generation_falls_back(self):
        self.assertEqual(self.decide(generation=6)[1], "fresh_full_fallback")

    def test_wrong_source_falls_back(self):
        self.assertEqual(self.decide(source=False)[1], "fresh_full_fallback")

    def test_stale_read_falls_back(self):
        self.assertEqual(self.decide(status={"title": "STALE", "parent": "CURRENT"})[1],
                         "fresh_full_fallback")

    def test_conflict_and_missing_refuse_even_after_fallback(self):
        self.assertEqual(self.decide(fresh={"title": "A", "parent": "B"})[0], "UNKNOWN")
        self.assertEqual(self.decide(fresh={"title": "A", "parent": "MISSING"})[0], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
