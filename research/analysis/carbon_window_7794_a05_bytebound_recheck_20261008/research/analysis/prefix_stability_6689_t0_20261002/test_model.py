"""Construction-only tests; these do not count as the frozen formal run."""

import json
import unittest
from pathlib import Path

import candidate


ROOT = Path(__file__).parent


class PrefixModelConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((ROOT / "spec.json").read_text(encoding="utf-8"))
        cls.header, cls.rows = candidate.build(cls.spec, ROOT / "spec.json")
        cls.by_prefix = {candidate.canonical(row["prefix"]): row
                         for row in cls.rows}

    def test_finite_space_and_prefix_coverage(self):
        self.assertEqual(self.header["world_count"], 40)
        self.assertGreater(self.header["trace_count"], 40)
        self.assertEqual(self.header["unique_prefix_count"], len(self.rows))
        self.assertIn(candidate.canonical([]), self.by_prefix)

    def test_source_current_mandatory_fail_can_finalize_early(self):
        row = next(row for row in self.rows
                   if row["classification"] == "STABLE_FINAL"
                   and row["reachable_terminal_dispositions"] == ["FAIL"]
                   and not row["terminal_prefix"])
        state = {(event["source"], event["type"]): event["value"]
                 for event in row["prefix"]}
        self.assertEqual(state[("generation", "status")], "CURRENT")
        self.assertIn("FAIL", (state.get(("target", "result")),
                                state.get(("effect", "result"))))

    def test_pass_requires_completed_positive_frontier(self):
        early_pass = [row for row in self.rows
                      if row["classification"] == "STABLE_FINAL"
                      and row["reachable_terminal_dispositions"] == ["PASS"]
                      and not row["terminal_prefix"]]
        self.assertEqual(early_pass, [])
        for row in self.rows:
            if (row["classification"] == "STABLE_FINAL" and
                    row["reachable_terminal_dispositions"] == ["PASS"]):
                state = {(event["source"], event["type"]): event["value"]
                         for event in row["prefix"]}
                self.assertEqual(state.get(("optional", "frontier")), "COMPLETE")

    def test_every_prefix_is_non_authorizing(self):
        self.assertTrue(all(row["consumer_authority"] is False
                            and row["consumer_side_effects"] == 0
                            for row in self.rows))
        self.assertEqual(self.header["authority_grants"], 0)
        self.assertEqual(self.header["consumer_side_effects"], 0)


if __name__ == "__main__":
    unittest.main()
