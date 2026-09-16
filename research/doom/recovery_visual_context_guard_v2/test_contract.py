import unittest
import audit, experiment
class T(unittest.TestCase):
    def test_threshold_identity(self):
        self.assertEqual(audit.THRESHOLD,.015); self.assertEqual(experiment.VISIBLE_CHANGE_THRESHOLD,.015)
    def test_boundary_admit(self): self.assertEqual(experiment.visual_context_verdict(.015),'ADMIT')
    def test_above_reject(self): self.assertEqual(experiment.visual_context_verdict(.015000001),'REJECT_CONTEXT_CHANGED')
    def test_audit_verdict(self):
        self.assertEqual(audit.verdict(.014),'ADMIT'); self.assertEqual(audit.verdict(.016),'REJECT_CONTEXT_CHANGED')
if __name__=='__main__': unittest.main()
