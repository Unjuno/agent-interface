import unittest
from .scorer import CASES, score

def receipt(case):
    return {"case":case,"session_id":"s","window_id":"0x42","observation_revision":1,"binding_revision":1,"input_ledger":[],"effect_receipt":{"artifact_sha256":"a"*64},"cleanup":{"status":"clean"},"authority_grants":0}

class IndependentScorerTests(unittest.TestCase):
    def test_all_eight_outcomes(self):
        expected = {"USEFUL_EFFECT":"USEFUL","UNAVAILABLE_BEFORE_INPUT":"UNAVAILABLE","GUARDED_REFUSAL":"REFUSED","ACCEPTED_NO_EFFECT":"NO_EFFECT","PARTIAL_COLLATERAL":"PARTIAL","STALE_REPAIR":"REPAIRED","AMBIGUOUS_DELIVERY":"UNKNOWN","TERMINAL_CLEANUP_FAILURE":"CLEANUP_FAILURE"}
        self.assertEqual(set(CASES), set(expected))
        for case, outcome in expected.items():
            self.assertEqual(score(receipt(case))["outcome"], outcome)
    def test_ambiguous_and_cleanup_are_not_ready(self):
        self.assertFalse(score(receipt("AMBIGUOUS_DELIVERY"))["ready"])
        self.assertFalse(score(receipt("TERMINAL_CLEANUP_FAILURE"))["ready"])
    def test_lineage_and_authority_fail_closed(self):
        r=receipt("USEFUL_EFFECT"); r["authority_grants"]=1
        self.assertFalse(score(r)["ready"])
        r=receipt("USEFUL_EFFECT"); r["binding_revision"]=2
        self.assertEqual(score(r)["reason"], "stale_binding")

if __name__ == "__main__":
    unittest.main()
