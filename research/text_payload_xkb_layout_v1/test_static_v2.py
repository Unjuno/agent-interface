import hashlib, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_dependency(self):
  d=(HERE/'preflight_dependency.py').read_bytes(); self.assertEqual(hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest(),'35c7375e50f3e0c58f57c8139a6dc8abeef87771')
 def test_schedule(self):
  import run_matrix_v2; self.assertEqual(run_matrix_v2.SCHEDULE,[('us',''),('de',''),('fr',''),('us','dvorak')])
 def test_v1_not_reused(self):
  self.assertIn('separately allocated successor',(HERE/'PLAN_V2.md').read_text())
if __name__=='__main__': unittest.main()
