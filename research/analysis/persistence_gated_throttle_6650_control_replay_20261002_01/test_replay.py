from __future__ import annotations

import json
import sys
from copy import deepcopy
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from replay import differences, reconstruct  # noqa: E402


class IndependentReplayConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = HERE.parent / "persistence_gated_throttle_6650_t0_v1"
        cls.fixture = json.loads((src / "fixture.json").read_text())
        cls.raw = json.loads((src / "RAW.json").read_text())
        cls.expected = reconstruct(cls.fixture)

    def test_all_nine_traces_four_policies_reconstruct_exactly(self):
        self.assertEqual(9, len(self.fixture["traces"]))
        self.assertEqual([], differences(self.expected, self.raw))

    def test_adverse_primary_comparison_is_retained(self):
        runs = self.raw["traces"]["sustained_overload"]
        self.assertEqual(13, runs["fixed"]["summary"]["stale_optional_delivered"])
        self.assertEqual(3, runs["queue_length"]["summary"]["stale_optional_delivered"])
        self.assertEqual(6, runs["persistence"]["summary"]["stale_optional_delivered"])

    def test_replayer_is_not_importing_predecessor_implementations(self):
        import replay
        self.assertFalse(hasattr(replay, "simulate"))
        self.assertFalse(hasattr(replay, "audit"))

    def test_nine_independent_mutation_shapes_change_reconstructed_record(self):
        edits = [
            lambda x: x["traces"]["sustained_overload"]["persistence"]["requests"][0].__setitem__("tier_at_offer", 99),
            lambda x: x["traces"]["sustained_overload"]["persistence"]["states"][0].__setitem__("signal", True),
            lambda x: x["traces"]["sustained_overload"]["persistence"]["transitions"][0].__setitem__("at", 999),
            lambda x: x["traces"]["sustained_overload"]["persistence"]["requests"][0].__setitem__("status", "SUPPRESSED"),
            lambda x: x["traces"]["session_isolation"]["persistence"]["states"][0].__setitem__("session", "OTHER"),
            lambda x: next(row for row in x["traces"]["mandatory_flood"]["persistence"]["requests"] if row["kind"] == "mandatory").__setitem__("status", "SUPPRESSED"),
            lambda x: x["traces"]["sustained_overload"]["queue_length"]["services"].__setitem__(slice(0, 2), reversed(x["traces"]["sustained_overload"]["queue_length"]["services"][:2])),
            lambda x: x["traces"]["semantic_invalidation"]["persistence"]["services"][0].__setitem__("generation_at_start", 55),
            lambda x: x["traces"]["sustained_overload"]["fixed"]["services"][7].__setitem__("outcome", "SERVICED_WITHIN_FRESHNESS"),
        ]
        for index, edit in enumerate(edits):
            altered = deepcopy(self.expected)
            edit(altered)
            with self.subTest(mutation=index):
                self.assertTrue(differences(self.expected, altered))


if __name__ == "__main__":
    unittest.main()
