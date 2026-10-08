import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location("candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class Construction(unittest.TestCase):
    def test_fixture_is_finite_and_ids_unique(self):
        cases = json.loads((ROOT / "fixture.json").read_text()) ["cases"]
        self.assertEqual(10, len(cases))
        self.assertEqual(len(cases), len({x["id"] for x in cases}))

    def test_invalid_deletion_is_not_causal_evidence(self):
        cases = json.loads((ROOT / "fixture.json").read_text()) ["cases"]
        row = next(x for x in cases if x["id"] == "invalid-mandatory-deletion")
        self.assertEqual("UNTESTABLE", candidate.decide(row["policy"], row["facts"]))

    def test_redundant_proof_uses_alternative_set(self):
        cases = json.loads((ROOT / "fixture.json").read_text()) ["cases"]
        row = next(x for x in cases if x["id"] == "redundant-independent-proofs")
        self.assertEqual("ALLOW", candidate.decide(row["policy"], row["facts"]))
        self.assertFalse(candidate.dependency_closed_audit(row)["flag"])
        # Removing either sufficient proof leaves the independent alternative.
        self.assertEqual("ALLOW", candidate.decide(row["policy"], {"proof_a_valid": False, "proof_b_valid": True}))
        self.assertEqual("ALLOW", candidate.decide(row["policy"], {"proof_a_valid": True, "proof_b_valid": False}))

    def test_uncited_blocker_is_a_defect(self):
        cases = json.loads((ROOT / "fixture.json").read_text()) ["cases"]
        row = next(x for x in cases if x["id"] == "uncited-decisive-receipt")
        self.assertTrue(candidate.dependency_closed_audit(row)["flag"])

    def test_stale_policy_is_a_defect(self):
        cases = json.loads((ROOT / "fixture.json").read_text()) ["cases"]
        row = next(x for x in cases if x["id"] == "policy-swap-stale-explanation")
        self.assertEqual("DENY", candidate.decide(row["policy"], row["facts"]))
        self.assertEqual("policy-binding-mismatch", candidate.dependency_closed_audit(row)["reason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
