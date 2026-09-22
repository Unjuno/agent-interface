import tempfile, unittest, subprocess, sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def build(self):
  td=tempfile.TemporaryDirectory(); root=Path(td.name)/'f'
  subprocess.run([sys.executable,'-B',str(HERE/'run_case.py'),'run',str(root)],check=True,capture_output=True,text=True)
  return td,root
 def test_complete(self):
  td,root=self.build()
  try:
   p=subprocess.run([sys.executable,'-B',str(HERE/'audit.py'),str(root)],check=True,capture_output=True,text=True)
   self.assertEqual(json.loads(p.stdout)['status'],'PASS_RAW_HASH_NONRECONSTRUCTIBLE_FROM_PNG_SCOPED')
  finally: td.cleanup()
 def test_controls(self):
  td,root=self.build()
  try:
   p=subprocess.run([sys.executable,'-B',str(HERE/'audit.py'),str(root),'--controls'],check=True,capture_output=True,text=True)
   row=json.loads(p.stdout); self.assertTrue(row['all_rejected']); self.assertEqual(len(row['controls']),7)
  finally: td.cleanup()
if __name__=='__main__': unittest.main()
