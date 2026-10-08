"""Mutation controls for the read-only V40 source identity gate."""
import unittest

from .verify_identity import evaluate


class IdentityGateTests(unittest.TestCase):
    def test_detects_stale_audit_and_readme_claims(self):
        result = evaluate("a" * 64, "b" * 64, "b" * 64)
        self.assertEqual(result["decision"], "FAIL_SOURCE_IDENTITY")
        self.assertFalse(result["checks"]["audit_matches_candidate"])
        self.assertFalse(result["checks"]["readme_matches_candidate"])

    def test_accepts_exact_matching_claims(self):
        result = evaluate("a" * 64, "a" * 64, "a" * 64)
        self.assertEqual(result["decision"], "PASS_SOURCE_IDENTITY")
        self.assertTrue(all(result["checks"].values()))

    def test_detects_split_claims_even_when_one_matches_candidate(self):
        result = evaluate("a" * 64, "a" * 64, "b" * 64)
        self.assertEqual(result["decision"], "FAIL_SOURCE_IDENTITY")
        self.assertTrue(result["checks"]["audit_matches_candidate"])
        self.assertFalse(result["checks"]["readme_matches_candidate"])
        self.assertFalse(result["checks"]["audit_matches_readme"])


if __name__ == "__main__":
    unittest.main()
