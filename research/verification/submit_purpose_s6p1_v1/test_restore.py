"""Postformal data-package tests only; never reexecute scientific actors."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import restore

SOURCE = Path(__file__).resolve().parent


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for p in [SOURCE / 'PACKAGE.json', *SOURCE.glob('evidence.part*.b64')]:
            shutil.copyfile(p, self.root / p.name)
        self.old_here = restore.HERE
        restore.HERE = self.root
        self.spec = json.loads((self.root / 'PACKAGE.json').read_text())
        self.assertEqual(len(restore.load_members()), 199)

    def tearDown(self):
        restore.HERE = self.old_here
        self.temp.cleanup()

    def save(self):
        (self.root / 'PACKAGE.json').write_text(json.dumps(self.spec))

    def refuse(self):
        dest = self.root / 'out'
        with self.assertRaises((ValueError, FileNotFoundError)):
            restore.restore(dest)
        self.assertFalse(dest.exists())

    def test_positive(self):
        dest = self.root / 'out'
        members = restore.load_members()
        self.assertEqual(restore.restore(dest)['files'], 199)
        self.assertEqual({p.relative_to(dest).as_posix(): p.read_bytes() for p in dest.rglob('*') if p.is_file()}, members)

    def test_missing_part(self):
        (self.root / self.spec['parts'][0]['name']).unlink()
        self.refuse()

    def test_changed_part(self):
        p = self.root / self.spec['parts'][0]['name']
        b = bytearray(base64.b64decode(p.read_bytes())); b[11] ^= 1
        p.write_bytes(base64.b64encode(b)); self.refuse()

    def test_reordered_parts(self):
        self.spec['parts'].reverse(); self.save(); self.refuse()

    def test_member_count(self):
        self.spec['members'] += 1; self.save(); self.refuse()

    def test_boolean_bound(self):
        self.spec['archive_bytes'] = True; self.save(); self.refuse()

    def test_oversized_tar_bound(self):
        self.spec['tar_bytes'] = 20_000_001; self.save(); self.refuse()

    def test_trailing_xz_bytes(self):
        part = self.spec['parts'][-1]; p = self.root / part['name']
        data = base64.b64decode(p.read_bytes()) + b'extra'
        p.write_bytes(base64.b64encode(data))
        part.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        full = b''.join(base64.b64decode((self.root / x['name']).read_bytes()) for x in self.spec['parts'])
        self.spec.update(archive_bytes=len(full), archive_sha256=hashlib.sha256(full).hexdigest())
        self.save(); self.refuse()

    def test_parent_part_path(self):
        self.spec['parts'][0]['name'] = '../outside'
        self.save(); self.refuse()

    def test_existing_destination(self):
        out = self.root / 'out'; out.mkdir(); sentinel = out / 'sentinel'; sentinel.write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'destination exists'):
            restore.restore(out)
        self.assertEqual(sentinel.read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()
