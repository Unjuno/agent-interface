import unittest
from auditor import audit

class AuditTests(unittest.TestCase):
    def rows(self):
        return [{'case_id':f'{a}-{d}','arm':a,'dwell_tics':d,'emitted_vector':[1,0,0,0],'declared_button':a,'ready':True,'pre':{},'post':{},'screen_hash_before':'a','screen_hash_after':'b','process_identity':'p','cleanup_ok':True} for a in ('forward','use','left','right','noop') for d in (4,16)]
    def test_exact_set_passes(self): self.assertTrue(audit(self.rows())['passed'])
    def test_missing_raw_row_fails(self): self.assertFalse(audit(self.rows()[:-1])['passed'])
    def test_mapping_fails(self):
        r=self.rows(); r[0]['declared_button']='wrong'; self.assertIn('BUTTON_MAPPING',audit(r)['issues'])
    def test_missing_evidence_field_fails(self):
        r=self.rows(); del r[0]['screen_hash_after']; self.assertIn('MISSING_FIELDS',audit(r)['issues'])

if __name__=='__main__': unittest.main()
