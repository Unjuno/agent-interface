"""Post-experiment packaging controls; never invoke scientific actors."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('verify', ROOT/'verify.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class Packaging(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)/'pub'
        self.root.mkdir()
        for name in v.PARTS:
            shutil.copyfile(ROOT/name, self.root/name)
        self.out = Path(self.tmp.name)/'out'
    def tearDown(self):
        self.tmp.cleanup()
    def reject(self):
        with self.assertRaises((ValueError, OSError)):
            v.restore(self.root, self.out)
        self.assertFalse(self.out.exists())
    def test_bit_change(self):
        p = self.root/v.PARTS[1]
        data = p.read_text();p.write_text(('A' if data[0]!='A' else 'B')+data[1:])
        self.reject()
    def test_missing_part(self):
        (self.root/v.PARTS[0]).unlink();self.reject()
    def test_extra_part(self):
        (self.root/'evidence.999.b64').write_text('AAAA');self.reject()
    def test_short_part(self):
        p=self.root/v.PARTS[0];p.write_text(p.read_text()[:-4]);self.reject()
    def test_non_base64(self):
        p=self.root/v.PARTS[0];p.write_text('!'+p.read_text()[1:]);self.reject()
    def test_existing_destination(self):
        self.out.mkdir();marker=self.out/'keep';marker.write_text('retain')
        with self.assertRaises(ValueError):v.restore(self.root,self.out)
        self.assertEqual(marker.read_text(),'retain')
    def test_exact_restore(self):
        m=v.restore(self.root,self.out)
        self.assertEqual(len(m),100)
        self.assertEqual(len(list(p for p in self.out.rglob('*') if p.is_file())),101)

if __name__=='__main__':unittest.main()
