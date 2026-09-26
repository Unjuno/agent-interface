"""Packaging regressions; never executes the scientific receiver."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import restore

ROOT = Path(__file__).resolve().parent

class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='e5d7-package-test-')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.pub = self.work / 'publication'
        self.pub.mkdir()
        shutil.copy(ROOT / 'EVIDENCE.json', self.pub)
        for file in ROOT.glob('evidence-*.xzpart'):
            shutil.copy(file, self.pub)
        self.dst = self.work / 'restored'
    def amend(self, fn):
        p = self.pub / 'EVIDENCE.json'
        data = json.loads(p.read_text())
        fn(data)
        p.write_text(json.dumps(data))
    def test_complete(self):
        self.assertEqual(restore.unpack(self.pub, self.dst)['members'], 714)
    def test_existing_destination(self):
        self.dst.mkdir()
        with self.assertRaises(ValueError): restore.unpack(self.pub, self.dst)
    def test_missing_piece(self):
        (self.pub / 'evidence-00.xzpart').unlink()
        with self.assertRaises(FileNotFoundError): restore.unpack(self.pub, self.dst)
    def test_changed_piece(self):
        p = self.pub / 'evidence-01.xzpart'
        p.write_bytes(b'x' + p.read_bytes()[1:])
        with self.assertRaises(ValueError): restore.unpack(self.pub, self.dst)
    def test_archive_digest(self):
        self.amend(lambda m: m.__setitem__('archive_sha256', '0'*64))
        with self.assertRaises(ValueError): restore.unpack(self.pub, self.dst)
    def test_member_count(self):
        self.amend(lambda m: m.__setitem__('members', 713))
        with self.assertRaises(ValueError): restore.unpack(self.pub, self.dst)
    def test_part_path(self):
        self.amend(lambda m: m['parts'][0].__setitem__('file', '../evidence-00.xzpart'))
        with self.assertRaises(ValueError): restore.unpack(self.pub, self.dst)
    def test_duplicate_part(self):
        self.amend(lambda m: m['parts'].append(m['parts'][0]))
        with self.assertRaises(ValueError): restore.unpack(self.pub, self.dst)

if __name__ == '__main__':
    unittest.main(verbosity=2)
