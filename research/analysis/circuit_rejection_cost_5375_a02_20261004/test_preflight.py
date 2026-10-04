import json
import unittest
from pathlib import Path
import auditor
import candidate

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "spec.json").read_text(encoding="utf-8"))
RAW = candidate.run(SPEC)


class ConstructionPreflight(unittest.TestCase):
    def test_candidate_capacity(self):
        self.assertTrue(all(r["total_cost"] <= SPEC["capacity"] for r in RAW["rows"]))

    def test_candidate_obligation_conservation(self):
        for r in RAW["rows"]:
            self.assertEqual(r["offered"], r["completed"] + r["refused"] + r["deferred"] + r["dropped"])

    def test_candidate_authority_closed(self):
        self.assertTrue(all(r["authority"] == 0 for r in RAW["rows"]))

    def test_candidate_and_separate_oracle_agree(self):
        self.assertEqual(RAW, auditor.expected_raw(SPEC))

    def test_storm_discriminates_and_controls_do_not(self):
        result = auditor.decide(SPEC, RAW)
        self.assertTrue(all(result["checks"].values()))

    def test_planted_drop_is_explicit_and_ineligible(self):
        r = RAW["rows"][-1]
        self.assertEqual((r["scenario"], r["eligible"], r["dropped"]), ("fault_drop", False, 1))


if __name__ == "__main__":
    unittest.main()
