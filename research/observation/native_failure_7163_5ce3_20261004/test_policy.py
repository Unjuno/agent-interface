import unittest
from policy import choose
class Policy(unittest.TestCase):
    def test_current_target_can_resume_despite_prior_failure(self):
        self.assertEqual(choose(101,101,True),'TRY')
    def test_recurring_cover_blocks(self):
        self.assertEqual(choose(102,101,True),'BLOCK')
    def test_fresh_guard_without_memory_also_blocks_cover(self):
        self.assertEqual(choose(102,101,False),'BLOCK')
    def test_fresh_guard_without_memory_allows_target(self):
        self.assertEqual(choose(101,101,False),'TRY')
    def test_missing_current_is_unknown(self):
        self.assertEqual(choose(None,101,True),'UNKNOWN')
    def test_boolean_id_not_integer_identity(self):
        self.assertEqual(choose(True,1,True),'UNKNOWN')
if __name__=='__main__':unittest.main()
