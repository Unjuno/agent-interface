import tempfile, unittest, subprocess, sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_complete(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'f'; subprocess.run([sys.executable,'-B',str(HERE/'run_case.py'),'run',str(root)],check=True,capture_output=True,text=True)
   p=subprocess.run([sys.executable,'-B',str(HERE/'audit.py'),str(root)],check=True,capture_output=True,text=True)
   self.assertEqual(json.loads(p.stdout)['status'],'PASS_RAW_HASH_NONRECONSTRUCTIBLE_FROM_PNG_SCOPED')
if __name__=='__main__': unittest.main()
