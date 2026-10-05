import unittest
from interval_ttc import interval_ttc,classify
class T(unittest.TestCase):
 def test_exact(self): self.assertEqual(interval_ttc(10,0,12,1,0),(6.,6.))
 def test_contains_nominal(self):
  x=interval_ttc(10,0,12,1,.25); self.assertIsNotNone(x); self.assertLessEqual(x[0],6); self.assertGreaterEqual(x[1],6)
 def test_zero_or_nonexpansion(self): self.assertIsNone(interval_ttc(10,0,10.5,1,.5)); self.assertIsNone(interval_ttc(10,0,9,1,0))
 def test_invalid(self): self.assertIsNone(interval_ttc(1,2,2,1,0)); self.assertIsNone(interval_ttc(float('nan'),0,2,1,0))
 def test_classification(self):
  self.assertEqual(classify((1,2)),"YIELD"); self.assertEqual(classify((2.01,3)),"CLEAR"); self.assertEqual(classify((1.9,2.1)),"UNKNOWN"); self.assertEqual(classify(None),"UNKNOWN")
if __name__=='__main__': unittest.main()
