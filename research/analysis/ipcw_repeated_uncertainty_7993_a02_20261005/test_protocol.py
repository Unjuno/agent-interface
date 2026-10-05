import copy
import math
import random
import unittest
from unittest.mock import patch

import auditor
import candidate
import generate


def one_case(ka=20, kb=15):
    # All units resolved; the first ka/kb outcomes are errors.
    a_resolved = (1 << 200) - 1
    b_resolved = (1 << 200) - 1
    return (
        {"schema": "unjuno.issue8049.public.a02.v1", "cohorts": [{
            "cohort": 0, "strata": {
                "A": {"resolved_mask": f"{a_resolved:050x}",
                      "resolved_error_mask": f"{((1 << ka)-1):050x}"},
                "B": {"resolved_mask": f"{b_resolved:050x}",
                      "resolved_error_mask": f"{((1 << kb)-1):050x}"},
            }}]},
        {"schema": "unjuno.issue8049.oracle.a02.v1", "cohorts": [{
            "cohort": 0, "strata": {
                "A": {"outcome_mask": f"{((1 << ka)-1):050x}"},
                "B": {"outcome_mask": f"{((1 << kb)-1):050x}"},
            }}]},
    )


class ProtocolTests(unittest.TestCase):
    def test_generator_is_fresh_fixed_and_candidate_truth_is_separate(self):
        self.assertNotEqual(generate.SEED, 8_049_001)
        self.assertEqual(generate.COHORTS, 20_000)
        with patch.object(generate, "COHORTS", 2):
            first = generate.generate()
            second = generate.generate()
        self.assertEqual(first, second)
        self.assertNotIn("outcome_mask", first[0]["cohorts"][0]["strata"]["A"])

    def test_weighted_point_and_bootstrap_endpoints_are_integer_ticks(self):
        public, _ = one_case()
        row = candidate.estimate(public)["records"][0]
        self.assertEqual(row["ht_numerator"], 3*20+15)
        self.assertTrue(0 <= row["bootstrap_lo_numerator"] <= row["bootstrap_hi_numerator"] <= 300)
        self.assertTrue(all(type(row[k]) is int for k in (
            "ht_numerator", "bootstrap_lo_numerator", "bootstrap_hi_numerator")))

    def test_candidate_and_independent_cdf_auditor_agree_across_edges(self):
        cases = [(0, 0), (1, 1), (20, 15), (50, 35), (199, 198), (200, 200)]
        rng = random.Random(804902)
        cases.extend((rng.randrange(201), rng.randrange(201)) for _ in range(16))
        for ka, kb in cases:
            self.assertEqual(candidate.interval_ticks(ka, kb), auditor.verified_interval_ticks(ka, kb))

    def test_oracle_reconstruction_and_typed_mutations(self):
        public, oracle = one_case()
        rows = candidate.estimate(public)
        self.assertEqual(auditor.reconstruct(public["cohorts"][0], oracle["cohorts"][0]),
                         rows["records"][0])
        with patch.object(auditor, "M", 1):
            report = auditor.audit(public, oracle, rows)
        self.assertTrue(report["all_mutations_rejected"])
        self.assertEqual(len(report["mutation_controls"]), 4)

    def test_malformed_public_masks_fail_closed(self):
        public, _ = one_case()
        public["cohorts"][0]["strata"]["A"]["resolved_mask"] = "0" * 50
        public["cohorts"][0]["strata"]["A"]["resolved_error_mask"] = "1" + "0"*49
        with self.assertRaises(ValueError):
            candidate.estimate(public)

    def test_candidate_source_never_names_oracle_input(self):
        from pathlib import Path
        source = Path(candidate.__file__).read_text()
        self.assertNotIn("oracle_input", source)
        self.assertNotIn("outcome_mask", source)


if __name__ == "__main__":
    unittest.main()
