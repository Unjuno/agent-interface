"""Packaging-only regressions. No experimental actors are started."""
import io
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from restore import ROOT, members, relative, restore

class RestoreTests(unittest.TestCase):
    def archive(self, names):
        data=io.BytesIO()
        with tarfile.open(fileobj=data,mode='w') as tar:
            for name in names:
                info=tarfile.TarInfo(name); info.size=1
                tar.addfile(info,io.BytesIO(b'x'))
        return data.getvalue()
    def test_regular(self):
        self.assertEqual(members(self.archive(['a','b']),2,2),[('a',b'x'),('b',b'x')])
    def test_absolute(self):
        with self.assertRaises(ValueError): members(self.archive(['/a']),1,1)
    def test_traversal(self):
        with self.assertRaises(ValueError): members(self.archive(['../a']),1,1)
    def test_duplicate(self):
        with self.assertRaises(ValueError): members(self.archive(['a','a']),2,2)
    def test_count(self):
        with self.assertRaises(ValueError): members(self.archive(['a']),2,1)
    def test_size(self):
        with self.assertRaises(ValueError): members(self.archive(['a']),1,2)
    def test_noncanonical(self):
        for name in ['a//b','./a','a\\b','']:
            with self.subTest(name=name),self.assertRaises(ValueError): relative(name)
    def test_link(self):
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w') as tar:
            info=tarfile.TarInfo('link');info.type=tarfile.SYMTYPE;info.linkname='elsewhere';tar.addfile(info)
        with self.assertRaises(ValueError):members(buffer.getvalue(),1,0)
    def test_existing_destination(self):
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaises(ValueError):restore(ROOT,Path(work))
    def test_exact_restore_and_corruption(self):
        with tempfile.TemporaryDirectory() as work:
            work=Path(work); copy=work/'source'; shutil.copytree(ROOT,copy)
            output=restore(copy,work/'exact')
            self.assertEqual(len([p for p in output.rglob('*') if p.is_file()]),972)
            manifest=json.loads((copy/'MANIFEST.json').read_bytes())
            part=copy/manifest['parts'][0]['path']; raw=bytearray(part.read_bytes());raw[-1]^=1;part.write_bytes(raw)
            with self.assertRaises(ValueError):restore(copy,work/'corrupted')
    def test_readable_copy(self):
        with tempfile.TemporaryDirectory() as work:
            work=Path(work);copy=work/'source';shutil.copytree(ROOT,copy)
            (copy/'original_policy.py').write_text('different\n')
            with self.assertRaises(ValueError):restore(copy,work/'mismatch')

if __name__=='__main__':unittest.main()
