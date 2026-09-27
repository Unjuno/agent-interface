import unittest
from logic import *
class T(unittest.TestCase):
 def test_serial_orders(self):
  self.assertEqual(classify_candidate(0,'bookx'),'APPEND_THEN_REPLACE_NO_MATCH')
  self.assertEqual(classify_candidate(1,'bookkeeperofficex'),'REPLACE_THEN_APPEND')
 def test_hybrid_rejected(self): self.assertEqual(classify_candidate(1,'bookxkeeperoffice'),'UNSAFE_OR_UNEXPECTED')
 def test_lost_append_rejected_candidate(self): self.assertEqual(classify_candidate(1,'bookkeeperoffice'),'UNSAFE_OR_UNEXPECTED')
 def test_baseline_negative_gate(self): self.assertTrue(gate('baseline_gap',None,'bookkeeperoffice'))
 def test_race_allows_both_serial_orders(self):
  self.assertTrue(gate('race_simultaneous',0,'bookx')); self.assertTrue(gate('race_simultaneous',1,'bookkeeperofficex'))
 def test_stale_uid(self): self.assertTrue(gate('stale_uid',None,'book',True))
if __name__=='__main__':unittest.main()
