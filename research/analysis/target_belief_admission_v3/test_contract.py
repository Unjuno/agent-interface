import unittest,experiment as e
class T(unittest.TestCase):
 def test_exact_margin_closed(self): self.assertEqual(e.belief_margin_admit([100,80],'VALID',False),'ALLOW')
 def test_narrow_probe_split(self):
  self.assertEqual(e.belief_margin_admit([100,85],'VALID',True),'PROBE');self.assertEqual(e.belief_margin_admit([100,85],'VALID',False),'NEEDS_DECISION')
 def test_ties_ambiguous(self): self.assertEqual(e.belief_margin_admit([100,100],'VALID',True),'PROBE')
 def test_invalid_provenance_reject(self): self.assertEqual(e.belief_margin_admit([100],'STALE',True),'REJECT')
 def test_below_and_empty_reject(self): self.assertEqual(e.belief_margin_admit([70,20],'VALID',True),'REJECT');self.assertEqual(e.belief_margin_admit([],'VALID',True),'REJECT')
 def test_top1_negative_control(self): self.assertEqual(e.top1_score_admit([100,100],'VALID',False),'ALLOW')
if __name__=='__main__':unittest.main(verbosity=2)
