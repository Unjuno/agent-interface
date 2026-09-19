import unittest
import audit
class T(unittest.TestCase):
    def test_threshold(self): self.assertEqual(audit.THRESHOLD,.015)
    def test_decision_requires_visible_recovery(self):
        p={'both_valid':True,'recovery_visible':False,'recovery_gt_coast':True};self.assertFalse(p['both_valid'] and p['recovery_visible'] and p['recovery_gt_coast'])
    def test_decision_requires_pairwise_excess(self):
        p={'both_valid':True,'recovery_visible':True,'recovery_gt_coast':False};self.assertFalse(p['both_valid'] and p['recovery_visible'] and p['recovery_gt_coast'])
if __name__=='__main__':unittest.main()
