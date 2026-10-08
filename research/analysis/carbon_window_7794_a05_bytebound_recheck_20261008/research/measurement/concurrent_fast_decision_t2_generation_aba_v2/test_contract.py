import unittest
from model import Candidate, StateOnlyComparator
class T(unittest.TestCase):
 def test_aba_rejected(self):
  c=Candidate(); c.frontier_request('A'); c.observe('A','CLEAR'); c.prepare('A','d1'); c.frontier_return('A','r1'); c.frontier_request('A'); c.observe('A','CLEAR'); self.assertFalse(c.try_admit('A','d1',True)['admit'])
 def test_comparator_escapes(self):
  c=StateOnlyComparator(); c.frontier_request('A'); c.observe('A','CLEAR'); c.prepare('A','d1'); c.frontier_return('A','r1'); c.frontier_request('A'); c.observe('A','CLEAR'); self.assertTrue(c.try_admit('A','d1',True)['admit'])
 def test_fresh(self):
  c=Candidate(); c.frontier_request('A'); c.observe('A','CLEAR'); c.prepare('A','d'); self.assertTrue(c.try_admit('A','d',True)['admit']); self.assertFalse(c.try_admit('A','d',True)['admit'])
 def test_state_and_authority(self):
  for state in ('WATCH','HARD'):
   c=Candidate(); c.frontier_request('A'); c.observe('A',state); c.prepare('A','d'); self.assertFalse(c.try_admit('A','d',True)['admit'])
  c=Candidate(); c.frontier_request('A'); c.observe('A','CLEAR'); c.prepare('A','d'); self.assertFalse(c.try_admit('A','d',False)['admit'])
 def test_cross_scope_and_forgery(self):
  c=Candidate(); c.frontier_request('A'); c.observe('A','CLEAR'); c.prepare('A','d'); self.assertFalse(c.try_admit('B','d',True)['admit']); self.assertFalse(c.try_admit('A','d',True,claimed_generation=99)['admit'])
 def test_duplicate_return(self):
  c=Candidate(); c.frontier_request('A'); self.assertTrue(c.frontier_return('A','r')['ok']); self.assertFalse(c.frontier_return('A','r')['ok']); self.assertEqual(c.scopes['A'].generation,1)
if __name__=='__main__': unittest.main()
