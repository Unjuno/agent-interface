import unittest
from run_matrix import SCHEDULE
class T(unittest.TestCase):
 def test_counts(self):
  self.assertEqual(len(SCHEDULE),9)
  self.assertEqual({x:SCHEDULE.count(x) for x in set(SCHEDULE)},{'compare_set':3,'recheck_set':3,'controllers_lock_set':3})
 def test_fixed_order(self): self.assertEqual(SCHEDULE[:3],['compare_set','recheck_set','controllers_lock_set'])
 def test_no_duplicate_names(self): self.assertEqual(set(SCHEDULE),{'compare_set','recheck_set','controllers_lock_set'})
if __name__=='__main__': unittest.main()
