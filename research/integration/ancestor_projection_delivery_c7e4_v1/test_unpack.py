"""Packaging-only refusal checks. No GUI/scientific allocation is executed."""
import hashlib
import io
import json
import lzma
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unpack import load_members, restore

ROOT = Path(__file__).resolve().parent


class Packaging(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        shutil.copytree(ROOT, self.source, ignore=shutil.ignore_patterns('__pycache__'))
        self.meta = json.loads((self.source / 'EVIDENCE_MANIFEST.json').read_text())

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        (self.source / 'EVIDENCE_MANIFEST.json').write_text(json.dumps(self.meta))

    def rejected(self):
        with self.assertRaises((ValueError, FileNotFoundError, lzma.LZMAError, tarfile.TarError)):
            restore(self.source, self.root / 'out')
        self.assertFalse((self.root / 'out').exists())

    def test_exact_and_existing_destination(self):
        result = restore(self.source, self.root / 'out')
        self.assertEqual(result['files'], 335)
        with self.assertRaises(ValueError):
            restore(self.source, self.root / 'out')

    def test_changed_part(self):
        p = self.source / self.meta['parts'][0]['path']
        b = bytearray(p.read_bytes()); b[2] ^= 1; p.write_bytes(b)
        self.rejected()

    def test_missing_part(self):
        (self.source / self.meta['parts'][0]['path']).unlink()
        self.rejected()

    def test_wrong_archive_digest(self):
        self.meta['archive_sha256'] = '0' * 64; self.save(); self.rejected()

    def test_duplicate_part(self):
        self.meta['parts'][1] = dict(self.meta['parts'][0]); self.save(); self.rejected()

    def test_boolean_count(self):
        self.meta['files'] = True; self.save(); self.rejected()

    def test_expansion_limit(self):
        self.meta['tar_bytes'] -= 1; self.save(); self.rejected()

    def replace_archive(self, entries):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for name, kind in entries:
                item = tarfile.TarInfo(name)
                if kind == 'link':
                    item.type = tarfile.SYMTYPE; item.linkname = '../outside'
                    archive.addfile(item)
                else:
                    item.size = 1; archive.addfile(item, io.BytesIO(b'x'))
        raw = buffer.getvalue(); packed = lzma.compress(raw)
        path = 'capsule/replaced.bin'; (self.source / path).write_bytes(packed)
        sha = hashlib.sha256(packed).hexdigest()
        self.meta.update(archive_bytes=len(packed), archive_sha256=sha, tar_bytes=len(raw),
                         files=len(entries), member_bytes=sum(k != 'link' for _, k in entries),
                         parts=[{'path': path, 'bytes': len(packed), 'sha256': sha}])
        self.save()

    def test_traversal_member(self):
        self.replace_archive([('../escape', 'file')]); self.rejected()

    def test_duplicate_member(self):
        self.replace_archive([('same', 'file'), ('same', 'file')]); self.rejected()

    def test_link_member(self):
        self.replace_archive([('link', 'link')]); self.rejected()


if __name__ == '__main__':
    unittest.main()
