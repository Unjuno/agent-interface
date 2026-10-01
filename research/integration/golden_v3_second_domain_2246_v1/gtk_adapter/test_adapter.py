import unittest
from .adapter import CASES, audit_receipt

def receipt(case):
    return {"case":case,"session_id":"gtk-session-01","window_id":"0x42","observation_revision":3,"binding_revision":3,"input_ledger":[],"effect_receipt":{"artifact_sha256":"a"*64},"cleanup":{"status":"clean"},"authority_grants":0}

class GtkAdapterAuditTests(unittest.TestCase):
    def test_matrix_preserves_declared_outcomes(self):
        expected = {"USEFUL_EFFECT":"USEFUL","UNAVAILABLE_BEFORE_INPUT":"UNAVAILABLE","GUARDED_REFUSAL":"REFUSED","ACCEPTED_NO_EFFECT":"NO_EFFECT","PARTIAL_COLLATERAL":"PARTIAL","STALE_REPAIR":"REPAIRED","AMBIGUOUS_DELIVERY":"UNKNOWN","TERMINAL_CLEANUP_FAILURE":"CLEANUP_FAILURE"}
        self.assertEqual(set(CASES), set(expected))
        for case, outcome in expected.items():
            self.assertEqual(audit_receipt(receipt(case)).outcome, outcome)
    def test_authority_and_lineage_fail_closed(self):
        r = receipt("USEFUL_EFFECT"); r["authority_grants"] = 1
        self.assertFalse(audit_receipt(r).ready)
        r = receipt("USEFUL_EFFECT"); r["binding_revision"] = 2
        self.assertEqual(audit_receipt(r).reason, "stale_binding")
    def test_ambiguous_delivery_never_replays(self):
        result = audit_receipt(receipt("AMBIGUOUS_DELIVERY"))
        self.assertFalse(result.ready)
        self.assertEqual(result.reason, "ambiguous_no_replay")

if __name__ == "__main__":
    unittest.main()
