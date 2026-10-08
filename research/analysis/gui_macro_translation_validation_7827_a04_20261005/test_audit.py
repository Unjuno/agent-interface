import audit, unittest
class AllocationBinding(unittest.TestCase):
 def test_expected_allocation_is_accepted(self):
  self.assertTrue(audit.allocation_matches({'allocation':'UNJUNO-7827-TV-A04-20261005-01'}))
 def test_stale_A03_allocation_is_rejected(self):
  self.assertFalse(audit.allocation_matches({'allocation':'UNJUNO-7827-TV-A03-20261005-01'}))
if __name__=='__main__': unittest.main(verbosity=2)
