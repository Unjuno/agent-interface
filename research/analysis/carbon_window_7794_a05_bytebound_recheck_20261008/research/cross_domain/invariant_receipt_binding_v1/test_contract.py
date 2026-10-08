import json, tempfile, unittest
from pathlib import Path
import experiment, audit
class T(unittest.TestCase):
    def one(self,policy,scenario):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'x'; r=experiment.one({'id':'x','policy':policy,'scenario':scenario},d); a=audit.audit_case(d); return r,a
    def test_clean_posthoc(self): self.assertTrue(self.one('posthoc_authored','clean')[0]['ground_truth_correct'])
    def test_clean_receipt(self): self.assertTrue(self.one('receipt_bound','clean')[0]['ground_truth_correct'])
    def test_damage_posthoc_false_accept(self): self.assertFalse(self.one('posthoc_authored','collateral_damaged')[0]['ground_truth_correct'])
    def test_damage_receipt_rejects(self): self.assertTrue(self.one('receipt_bound','collateral_damaged')[0]['ground_truth_correct'])
    def test_receipt_includes_collateral(self): self.assertIn('collateral',self.one('receipt_bound','collateral_damaged')[0]['requirement_source']['requirements'])
    def test_audit_passes(self): self.assertTrue(self.one('receipt_bound','clean')[1]['pass'])
if __name__=='__main__': unittest.main()
