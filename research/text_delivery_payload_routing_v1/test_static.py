from pathlib import Path
import hashlib,unittest
HERE=Path(__file__).resolve().parent
def blob(p):
 d=p.read_bytes();return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
class Static(unittest.TestCase):
 def test_exact_dependencies(self):
  self.assertEqual(blob(HERE/'preflight_dependency.py'),'35c7375e50f3e0c58f57c8139a6dc8abeef87771');self.assertEqual(blob(HERE/'coarse_model_dependency.py'),'6ed3fccd7dd0acd7b6c4911a895ff3c96c8c31fd')
 def test_matrix_fixed(self):
  import run_matrix;self.assertEqual(run_matrix.ARMS,[('us',''),('de',''),('fr',''),('us','dvorak')])
 def test_no_shared_runtime_import(self):
  text=(HERE/'routing.py').read_text();self.assertNotIn('runtime.',text)
if __name__=='__main__':unittest.main()
