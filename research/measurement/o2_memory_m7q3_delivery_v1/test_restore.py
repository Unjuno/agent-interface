"""Finite packaging controls. No encoder or measurement process is started."""
from pathlib import Path
import json
import shutil
import tempfile
import unittest
from restore import restore

ROOT = Path(__file__).resolve().parent


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='m7q3-package-test-')
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'source'
        self.source.mkdir()
        shutil.copytree(ROOT / 'evidence', self.source / 'evidence')
        shutil.copyfile(ROOT / 'CAPSULE.json', self.source / 'CAPSULE.json')
        self.out = Path(self.tmp.name) / 'out'

    def change(self, field, value):
        path = self.source / 'CAPSULE.json'
        data = json.loads(path.read_text())
        self.assertNotEqual(data[field], value)
        data[field] = value
        path.write_text(json.dumps(data), encoding='utf-8')

    def refused(self, reason):
        with self.assertRaisesRegex(ValueError, reason):
            restore(self.source, self.out)
        self.assertFalse(self.out.exists())

    def test_positive(self):
        result = restore(self.source, self.out)
        self.assertEqual(result['files'], 457)
        self.assertEqual(result['bytes'], 63114042)
        self.assertEqual(result['measurement_workers_started'], 0)

    def test_existing_destination(self):
        self.out.mkdir()
        (self.out / 'sentinel').write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'DESTINATION_EXISTS'):
            restore(self.source, self.out)
        self.assertEqual((self.out / 'sentinel').read_bytes(), b'keep')

    def test_changed_part(self):
        path = self.source / 'evidence/part-00.bin'
        data = bytearray(path.read_bytes())
        data[-1] ^= 1
        path.write_bytes(data)
        self.refused('PART_DIGEST')

    def test_missing_part(self):
        (self.source / 'evidence/part-21.bin').unlink()
        with self.assertRaises(FileNotFoundError):
            restore(self.source, self.out)
        self.assertFalse(self.out.exists())

    def test_part_order(self):
        parts = json.loads((self.source / 'CAPSULE.json').read_text())['parts']
        parts[0], parts[1] = parts[1], parts[0]
        self.change('parts', parts)
        self.refused('PART_ORDER')

    def test_archive_digest(self):
        self.change('archive_sha256', '0' * 64)
        self.refused('ARCHIVE_DIGEST')

    def test_member_count(self):
        self.change('original_files', 456)
        self.refused('ORIGINAL_COUNT')

    def test_manifest_digest(self):
        self.change('original_manifest_sha256', '0' * 64)
        self.refused('MANIFEST_DIGEST')

    def test_audit_digest(self):
        self.change('audit_sha256', '0' * 64)
        self.refused('AUDIT_DIGEST')

    def test_expansion_size(self):
        self.change('tar_bytes', 1)
        self.refused('TAR_LENGTH')


if __name__ == '__main__':
    unittest.main(verbosity=2)
