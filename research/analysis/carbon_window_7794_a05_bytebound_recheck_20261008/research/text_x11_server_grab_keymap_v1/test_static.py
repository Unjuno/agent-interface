import hashlib,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
def blob(p):
 b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
class T(unittest.TestCase):
 def test_dependency(self):self.assertEqual(blob(HERE/'preflight_dependency.py'),'35c7375e50f3e0c58f57c8139a6dc8abeef87771')
 def test_schedule(self):
  import aggregate;self.assertEqual(len(aggregate.SCHEDULE),12);self.assertEqual(sum(x[0]=='de' for x in aggregate.SCHEDULE),5);self.assertEqual(sum(x[0]=='fr' for x in aggregate.SCHEDULE),5);self.assertEqual(sum(x[0]=='us' for x in aggregate.SCHEDULE),2)
 def test_grab_semantic_probe_present(self):
  s=(HERE/'run_session.py').read_text();self.assertIn('grab_server()',s);self.assertIn('peek_shadow',s);self.assertIn('ungrab_server()',s)
if __name__=='__main__':unittest.main()
