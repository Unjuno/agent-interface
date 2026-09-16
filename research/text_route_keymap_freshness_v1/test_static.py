import unittest
from pathlib import Path
import hashlib
HERE=Path(__file__).resolve().parent
def blob(p):
 b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
class T(unittest.TestCase):
 def test_dependencies(self):
  self.assertEqual(blob(HERE/'preflight_dependency.py'),'35c7375e50f3e0c58f57c8139a6dc8abeef87771')
  self.assertEqual(blob(HERE/'routing.py'),'57a1a13af4190f81e436bc9461688e4b8d1ffb82')
 def test_fixed_cases(self):
  import run_matrix;self.assertEqual(run_matrix.CASES,[('us',''),('de',''),('fr','')])
if __name__=='__main__':unittest.main()
