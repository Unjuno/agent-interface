import unittest
from policy import Receipt, receipt_token
class T(unittest.TestCase):
 def test_token(self): self.assertEqual(receipt_token([Receipt('A','a1',1),Receipt('B','b1',2)]),{'A':1,'B':2})
 def test_duplicate(self):
  with self.assertRaises(ValueError): receipt_token([Receipt('A','a1',1),Receipt('A','a1',1)])
if __name__=='__main__': unittest.main()
