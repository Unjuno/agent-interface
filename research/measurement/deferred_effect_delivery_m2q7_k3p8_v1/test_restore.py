"""Packaging regressions only: no GUI, scientific runner, or native input."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import verify_evidence as v

class RestoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.loads((v.ROOT/'ARCHIVE.json').read_text())
        cls.data = b''.join((v.ROOT/r['path']).read_bytes() for r in cls.m['parts'])
    def test_original(self):
        self.assertEqual(len(v.decode(self.data, self.m)),270)
    def test_truncated(self):
        with self.assertRaises(ValueError): v.decode(self.data[:-1],self.m)
    def test_changed(self):
        b=bytearray(self.data);b[32]^=1
        with self.assertRaises(ValueError): v.decode(bytes(b),self.m)
    def test_extra_stream(self):
        m=copy.deepcopy(self.m);b=self.data+self.data
        m.update(archive_bytes=len(b),archive_sha256=v.digest(b))
        with self.assertRaises(ValueError): v.decode(b,m)
    def test_member_count(self):
        m=copy.deepcopy(self.m);m['original_files']=269
        with self.assertRaises(ValueError): v.decode(self.data,m)
    def test_member_bytes(self):
        m=copy.deepcopy(self.m);m['original_total_bytes']+=1
        with self.assertRaises(ValueError): v.decode(self.data,m)
    def test_freeze(self):
        m=copy.deepcopy(self.m);m['original_freeze_sha256']='0'*64
        with self.assertRaises(ValueError): v.decode(self.data,m)
    def test_path(self):
        for name in ('../bad','/bad','a//b','a/../b','a\\b','.'):
            with self.subTest(name=name),self.assertRaises(ValueError): v.canonical(name)
    def test_new_destination_only(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(FileExistsError):v.restore(v.ROOT,Path(t))
    def test_fresh_restore(self):
        with tempfile.TemporaryDirectory() as t:
            dest=Path(t)/'fresh';v.restore(v.ROOT,dest)
            self.assertEqual(len([f for f in dest.rglob('*') if f.is_file()]),270)

if __name__ == '__main__':unittest.main(verbosity=2)
