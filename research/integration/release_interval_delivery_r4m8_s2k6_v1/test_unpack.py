"""Packaging-only negative tests, no GUI or original scientific runner."""
from __future__ import annotations
import io, json, lzma, shutil, tarfile, tempfile, unittest
from pathlib import Path
from unpack import ROOT, TAR_BYTES, checked_members, restore

class UnpackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def copy(self):
        p = self.base/'pub'; shutil.copytree(ROOT, p); return p
    def test_restore(self):
        self.assertEqual(restore(self.base/'out')['members'],146)
    def test_existing_destination(self):
        with self.assertRaises(ValueError):restore(self.base)
    def test_corrupted_part(self):
        p=self.copy(); f=p/'capsule/part-000.bin'; b=f.read_bytes(); f.write_bytes(bytes([b[0]^1])+b[1:])
        with self.assertRaises(ValueError):restore(self.base/'out',p)
    def test_missing_part(self):
        p=self.copy(); (p/'capsule/part-000.bin').unlink()
        with self.assertRaises(FileNotFoundError):restore(self.base/'out',p)
    def test_wrong_order(self):
        p=self.copy(); f=p/'CAPSULE.json'; m=json.loads(f.read_text()); m['parts'].reverse();f.write_text(json.dumps(m))
        with self.assertRaises(ValueError):restore(self.base/'out',p)
    def test_extra_part_record(self):
        p=self.copy();f=p/'CAPSULE.json';m=json.loads(f.read_text());m['parts'].append(m['parts'][0]);f.write_text(json.dumps(m))
        with self.assertRaises(ValueError):restore(self.base/'out',p)
    def test_short_tar(self):
        with self.assertRaises(ValueError):checked_members(b'')
    def malformed_tar(self,name,kind=tarfile.REGTYPE,twice=False):
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w') as t:
            m=tarfile.TarInfo(name);m.type=kind;m.linkname='outside' if kind==tarfile.SYMTYPE else '';m.size=0;t.addfile(m)
            if twice:t.addfile(m)
        return buf.getvalue().ljust(TAR_BYTES,b'\0')
    def test_path_traversal(self):
        with self.assertRaises(ValueError):checked_members(self.malformed_tar('../escape'))
    def test_symlink(self):
        with self.assertRaises(ValueError):checked_members(self.malformed_tar('link',tarfile.SYMTYPE))
    def test_duplicate_member(self):
        with self.assertRaises(ValueError):checked_members(self.malformed_tar('same',twice=True))
    def test_inventory_incomplete(self):
        with self.assertRaises(ValueError):checked_members(self.malformed_tar('one'))
    def test_part_symlink(self):
        p=self.copy();f=p/'capsule/part-000.bin';f.unlink();f.symlink_to(ROOT/'capsule/part-000.bin')
        with self.assertRaises(ValueError):restore(self.base/'out',p)

if __name__=='__main__':unittest.main(verbosity=2)
