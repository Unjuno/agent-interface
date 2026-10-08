import unittest
from audit import EXPECTED
class ContractTests(unittest.TestCase):
    def test_matrix(self): self.assertEqual(len(EXPECTED),9)
    def test_stable_all_true(self): self.assertTrue(all(v for (p,s),v in EXPECTED.items() if s=="STABLE"))
    def test_move_before(self):
        self.assertFalse(EXPECTED[("PINNED_SCREEN","MOVE_BEFORE")]); self.assertTrue(EXPECTED[("REFRESH_SCREEN","MOVE_BEFORE")]); self.assertTrue(EXPECTED[("WINDOW_CLIENT","MOVE_BEFORE")])
    def test_move_between(self):
        self.assertFalse(EXPECTED[("PINNED_SCREEN","MOVE_BETWEEN")]); self.assertFalse(EXPECTED[("REFRESH_SCREEN","MOVE_BETWEEN")]); self.assertTrue(EXPECTED[("WINDOW_CLIENT","MOVE_BETWEEN")])
    def test_window_client_all_true(self): self.assertTrue(all(v for (p,s),v in EXPECTED.items() if p=="WINDOW_CLIENT"))
    def test_negative_count(self): self.assertEqual(sum(not v for v in EXPECTED.values()),3)
if __name__=="__main__": unittest.main()
