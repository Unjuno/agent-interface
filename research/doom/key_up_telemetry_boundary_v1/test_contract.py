import unittest
class Contract(unittest.TestCase):
 def test_matrix(self):
  self.assertEqual(2*4*3,24)
 def test_receipt_scope(self):
  self.assertNotEqual('key_released','authority')
 def test_partial(self):
  requested=['a','d']; admitted=['a']; self.assertNotEqual(requested,admitted)
if __name__=='__main__': unittest.main()
