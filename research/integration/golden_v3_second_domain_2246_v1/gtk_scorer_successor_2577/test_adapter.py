import unittest
from .adapter import audit_receipt

def row(case="USEFUL_EFFECT"):
    return {"case":case,"authority_grants":0,"cleanup":{"status":"clean"},"effect_receipt":{"outcome":"USEFUL"},"input_ledger":[],"session_id":"s","window_id":"w","observation_revision":3,"binding_revision":3}

class Tests(unittest.TestCase):
    def test_valid_useful(self): self.assertEqual(audit_receipt(row()).outcome,"USEFUL")
    def test_missing_authority_is_rejected(self):
        r=row(); del r["authority_grants"]; self.assertFalse(audit_receipt(r).ready)
    def test_cleanup_evidence_overrides_label(self):
        r=row(); r["cleanup"]={"status":"failed"}; self.assertEqual(audit_receipt(r).outcome,"CLEANUP_FAILURE")
    def test_label_cannot_launder_effect(self):
        r=row("ACCEPTED_NO_EFFECT"); self.assertEqual(audit_receipt(r).reason,"effect_mismatch")
    def test_empty_effect_cannot_be_useful(self):
        r=row(); r["effect_receipt"]={}; self.assertEqual(audit_receipt(r).reason,"effect_mismatch")
    def test_repair_lineage_required(self):
        r=row("STALE_REPAIR"); self.assertEqual(audit_receipt(r).reason,"repair_lineage")
    def test_repair_lineage_is_explicit(self):
        r=row("STALE_REPAIR"); r["repair"]={"bounded":True,"prior_observation_revision":2}; r["effect_receipt"]={"outcome":"REPAIRED"}; self.assertTrue(audit_receipt(r).ready)
if __name__=="__main__": unittest.main()
