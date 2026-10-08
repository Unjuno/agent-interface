import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text())


class FrontierTests(unittest.TestCase):
    def test_candidate_reconstructs_exactly(self):
        raw = candidate.run(FIXTURE)
        self.assertEqual(len(raw), 24)
        self.assertEqual(auditor.audit(FIXTURE, raw)["errors"], [])

    def test_supported_coarse_category(self):
        row = next(r for r in candidate.run(FIXTURE) if r["cohort_id"] == "merged" and r["eta"] == 1)
        rare = next(c for c in row["classes"] if c["label"] == "RARE")
        self.assertEqual(rare["support"], 4)
        self.assertEqual(rare["noise_status"], "DISCOVERED")

    def test_correlated_and_duplicate_are_unknown(self):
        for cohort in ("correlated", "duplicate_client"):
            row = next(r for r in candidate.run(FIXTURE) if r["cohort_id"] == cohort and r["eta"] == 0)
            self.assertTrue(all(c["noise_status"] == "UNKNOWN" for c in row["classes"]))

    def test_singleton_dp_bound(self):
        bound = auditor.singleton_bound(1, 0, 0.1)
        self.assertAlmostEqual(bound, 0.2718281828459045)
        self.assertAlmostEqual((0.9 / 2.718281828459045), 0.33109149705429813)

    def test_mutations_rejected(self):
        raw = candidate.run(FIXTURE)
        for mutation in ("omit_client_proxy", "singleton_leak", "privacy_claim", "suppressed_absent"):
            with self.subTest(mutation=mutation):
                self.assertTrue(auditor.audit(FIXTURE, auditor.corrupt(raw, mutation))["errors"])

    def test_taxonomy_split_and_no_failure_controls(self):
        rows = candidate.run(FIXTURE)
        split = next(r for r in rows if r["cohort_id"] == "split")
        self.assertIn("RARE_A|RARE_B", {c["label"] for c in split["classes"]})
        empty = next(r for r in rows if r["cohort_id"] == "no_failure")
        self.assertTrue(any(c["noise_status"] == "NO_FAILURE_CONTROL" for c in empty["classes"]))


if __name__ == "__main__":
    unittest.main()
