"""Publication checks only. No measured worker or matrix is restarted."""
from pathlib import Path
import json
import shutil
import tempfile
import unittest
from restore import ROOT, restore


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'package'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('__pycache__'))
        self.out = Path(self.tmp.name) / 'restored'

    def edit_spec(self, change):
        path = self.root / 'PACKAGE.json'
        data = json.loads(path.read_bytes())
        change(data)
        path.write_text(json.dumps(data))

    def refuses(self):
        with self.assertRaises((ValueError, FileNotFoundError)):
            restore(self.out, self.root)
        self.assertFalse(self.out.exists())

    def test_exact_members(self):
        self.assertEqual(restore(self.out, self.root)['files'], 39)
        self.assertTrue((self.out / 'engineering01/RECORDS.jsonl').is_file())

    def test_existing_destination_unchanged(self):
        self.out.mkdir(); (self.out / 'sentinel').write_bytes(b'old')
        with self.assertRaises(ValueError):
            restore(self.out, self.root)
        self.assertEqual((self.out / 'sentinel').read_bytes(), b'old')

    def test_changed_segment(self):
        path = self.root / 'evidence.00.bin'
        data = bytearray(path.read_bytes()); data[80] ^= 1; path.write_bytes(data)
        self.refuses()

    def test_missing_segment(self):
        (self.root / 'evidence.00.bin').unlink(); self.refuses()

    def test_reordered_segment_manifest(self):
        self.edit_spec(lambda d: d['segments'].reverse()); self.refuses()

    def test_archive_digest(self):
        self.edit_spec(lambda d: d.__setitem__('archive_sha256', '0' * 64)); self.refuses()

    def test_member_extent(self):
        self.edit_spec(lambda d: d.__setitem__('member_count', 40)); self.refuses()

    def test_readable_mismatch(self):
        (self.root / 'adapter.py').write_bytes(b'not the original'); self.refuses()


if __name__ == '__main__':
    unittest.main()
