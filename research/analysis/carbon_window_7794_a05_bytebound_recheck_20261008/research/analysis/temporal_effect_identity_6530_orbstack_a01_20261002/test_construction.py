"""Pre-freeze construction checks only; never formal evidence."""
import json
import unittest
from pathlib import Path

import candidate


ROOT = Path(__file__).parent


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))

    def test_case_roster(self):
        self.assertEqual(
            {"ordinary", "fold-first", "fold-second", "fold-unresolved",
             "spring-gap", "local-recurrence", "no-save", "duplicate"},
            {case["id"] for case in self.fixture["cases"]},
        )

    def test_fold_has_two_distinct_instants(self):
        actual = candidate.possible_instants(
            "2026-11-01T01:30:00", "America/New_York")
        self.assertEqual(["2026-11-01T05:30:00Z", "2026-11-01T06:30:00Z"], actual)

    def test_gap_has_no_valid_instant(self):
        self.assertEqual([], candidate.possible_instants(
            "2026-03-08T02:30:00", "America/New_York"))

    def test_wrong_local_recurrence_discriminates(self):
        case = next(x for x in self.fixture["cases"] if x["id"] == "local-recurrence")
        self.assertEqual("WRONG_RECURRENCE", candidate.classify(case)["classification"])
        self.assertTrue(candidate.baselines(case)["string_only_accept"])
        self.assertTrue(candidate.baselines(case)["offset_only_accept"])

    def test_unknown_no_effect_and_duplicate(self):
        by_id = {case["id"]: case for case in self.fixture["cases"]}
        self.assertEqual("AMBIGUOUS_UNRESOLVED",
                         candidate.classify(by_id["fold-unresolved"])["classification"])
        self.assertEqual("NO_EFFECT", candidate.classify(by_id["no-save"])["classification"])
        self.assertEqual("DUPLICATE_EFFECT", candidate.classify(by_id["duplicate"])["classification"])


if __name__ == "__main__":
    unittest.main()
