import hashlib, importlib.util, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('study',ROOT/'study.py');study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)

class T(unittest.TestCase):
 def test_git_blob(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_bytes(b'hello')
   want=hashlib.sha1(b'blob 5\0hello').hexdigest();self.assertEqual(study.git_blob(p),want)
 def test_expected_identity_constants(self):
  self.assertEqual(study.EXPECTED['jar']['bytes'],87022576)
  self.assertEqual(study.EXPECTED['jar']['sha256'],'7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539')
  self.assertEqual(study.EXPECTED_ORACLE['width'],300);self.assertEqual(study.EXPECTED_ORACLE['height'],250)
 def test_wait_true(self): self.assertTrue(study.wait_until(lambda:True,.01))
 def test_wait_false(self): self.assertFalse(study.wait_until(lambda:False,.01,.002))

if __name__=='__main__':unittest.main()
