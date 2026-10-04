import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate


class EqualitySaturationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((Path(__file__).parent / "fixture.json").read_text())

    def test_complete_small_equality_closure_has_cost_gain(self):
        for program in self.fixture["programs"]:
            greedy = candidate.greedy(program, self.fixture["cost_units"])
            extracted, stats = candidate.saturate_extract(
                program, self.fixture["cost_units"],
                self.fixture["limits"]["max_terms"], self.fixture["limits"]["max_rounds"])
            self.assertTrue(stats["saturated"])
            self.assertFalse(stats["extraction_failure"])
            if program["split"] == "heldout":
                self.assertLess(candidate.cost(extracted, self.fixture["cost_units"]),
                                candidate.cost(greedy, self.fixture["cost_units"]))
            self.assertEqual(auditor.compare(self.fixture, program, extracted)[0], [])

    def test_invalid_freshness_order_and_release_mutations_are_caught(self):
        heldout = next(p for p in self.fixture["programs"] if p["split"] == "heldout")
        extracted, _ = candidate.saturate_extract(
            heldout, self.fixture["cost_units"],
            self.fixture["limits"]["max_terms"], self.fixture["limits"]["max_rounds"])
        for name in ("remove_refresh", "reorder_edit_save", "drop_release"):
            with self.subTest(name=name):
                changed = auditor.corrupt(extracted, name)
                self.assertTrue(auditor.compare(self.fixture, heldout, changed)[0])

    def test_only_declared_pure_and_passive_rules_are_used(self):
        heldout = next(p for p in self.fixture["programs"] if p["split"] == "heldout")
        _, stats = candidate.saturate_extract(
            heldout, self.fixture["cost_units"],
            self.fixture["limits"]["max_terms"], self.fixture["limits"]["max_rounds"])
        self.assertGreater(stats["term_count"], 1)
        names = {name for name, _ in candidate.rewrites(heldout)}
        self.assertTrue(names <= {"deduplicate_passive_check", "idempotent_trim",
                                  "idempotent_lower", "commute_trim_lower"})


if __name__ == "__main__":
    unittest.main()
