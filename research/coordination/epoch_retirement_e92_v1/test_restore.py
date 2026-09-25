import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify import restore
ROOT=Path(__file__).resolve().parent

class Restore(unittest.TestCase):
    def copy(self, root):
        pub=Path(root)/'pub';pub.mkdir()
        for p in [ROOT/'CAPSULE.json', *ROOT.glob('evidence-*.bin')]:
            shutil.copyfile(p,pub/p.name)
        return pub
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'data'
            self.assertEqual(restore(ROOT,d)['members'],185)
    def test_existing_destination(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):restore(ROOT,Path(t))
    def test_segment_change(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.copy(t);f=p/'evidence-00.bin';b=bytearray(f.read_bytes());b[0]^=1;f.write_bytes(b)
            with self.assertRaises(ValueError):restore(p,Path(t)/'data')
    def test_truncated_segment(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.copy(t);f=p/'evidence-01.bin';f.write_bytes(f.read_bytes()[:-1])
            with self.assertRaises(ValueError):restore(p,Path(t)/'data')
    def test_missing_segment(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.copy(t);(p/'evidence-02.bin').unlink()
            with self.assertRaises(FileNotFoundError):restore(p,Path(t)/'data')
    def test_archive_hash(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.copy(t);m=json.loads((p/'CAPSULE.json').read_text());m['archive_sha256']='0'*64
            (p/'CAPSULE.json').write_text(json.dumps(m))
            with self.assertRaises(ValueError):restore(p,Path(t)/'data')
    def test_member_count(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.copy(t);m=json.loads((p/'CAPSULE.json').read_text());m['members']+=1
            (p/'CAPSULE.json').write_text(json.dumps(m))
            with self.assertRaises(ValueError):restore(p,Path(t)/'data')
    def test_manifest_hash(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.copy(t);m=json.loads((p/'CAPSULE.json').read_text());m['manifest_sha256']='0'*64
            (p/'CAPSULE.json').write_text(json.dumps(m))
            with self.assertRaises(ValueError):restore(p,Path(t)/'data')

if __name__=='__main__':unittest.main(verbosity=2)
