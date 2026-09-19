import unittest,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
def blob(p):
 b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
class T(unittest.TestCase):
 def test_dep(self):self.assertEqual(blob(HERE/'preflight_dependency.py'),'35c7375e50f3e0c58f57c8139a6dc8abeef87771')
 def test_cases(self):
  import run_matrix;self.assertEqual(run_matrix.CASES,[('us',''),('de',''),('fr','')])
if __name__=='__main__':unittest.main()
