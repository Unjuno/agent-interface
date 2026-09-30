import unittest

from harness import classify_counterexample, coarse_decide
from oracle import independent_oracle


class VerificationRefinementTests(unittest.TestCase):
    def test_independent_oracle_rejects_missing_authority_even_when_target_is_current(self):
        case = {
            "authority_current": False,
            "target_current": True,
            "evidence_current": True,
            "effect_safe": True,
            "well_formed": True,
            "family": "authority_revocation",
        }
        self.assertEqual(coarse_decide(case), "ADMIT")
        self.assertEqual(independent_oracle(case), "REJECT")

    def test_ambiguous_counterexample_remains_unknown_and_cannot_refine(self):
        case = {
            "authority_current": False,
            "target_current": True,
            "evidence_current": True,
            "effect_safe": True,
            "well_formed": True,
            "oracle_confidence": "ambiguous",
            "family": "authority_revocation",
        }
        result = classify_counterexample(case, coarse_decide(case), independent_oracle(case))
        self.assertEqual(result["classification"], "UNRESOLVED_UNKNOWN")
        self.assertIsNone(result["refinement"])

    def test_replayed_concrete_counterexample_proposes_only_the_missing_predicate(self):
        case = {
            "authority_current": False,
            "target_current": True,
            "evidence_current": True,
            "effect_safe": True,
            "well_formed": True,
            "oracle_confidence": "replayed",
            "family": "authority_revocation",
        }
        result = classify_counterexample(case, coarse_decide(case), independent_oracle(case))
        self.assertEqual(result["classification"], "SPURIOUS_ABSTRACTION")
        self.assertEqual(result["refinement"], "authority_current")


if __name__ == "__main__":
    unittest.main()
