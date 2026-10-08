"""Post-evaluation packaging tests; no scientific receiver is invoked."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from restore import restore

ROOT = Path(__file__).resolve().parent

class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        for name in ['CAPSULE.json'] + [f'evidence-{i:02}.xzpart' for i in range(7)]:
            shutil.copyfile(ROOT / name, self.source / name)
        self.dest = self.root / 'out'

    def test_complete(self):
        result = restore(self.source, self.dest)
        self.assertEqual(result['files'], 38)
        self.assertEqual(len(list(p for p in self.dest.rglob('*') if p.is_file())), 38)
        self.assertEqual((self.dest / 'FREEZE.json').read_bytes(), (ROOT / 'FREEZE.json').read_bytes())

    def test_changed_part(self):
        p = self.source / 'evidence-00.xzpart'
        data = bytearray(p.read_bytes()); data[40] ^= 1; p.write_bytes(data)
        with self.assertRaises(ValueError): restore(self.source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_reordered_parts(self):
        p = self.source / 'CAPSULE.json'; obj = json.loads(p.read_text())
        obj['parts'].reverse(); p.write_text(json.dumps(obj))
        with self.assertRaises(ValueError): restore(self.source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_count(self):
        p = self.source / 'CAPSULE.json'; obj = json.loads(p.read_text())
        obj['files'] = 37; p.write_text(json.dumps(obj))
        with self.assertRaises(ValueError): restore(self.source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_budget(self):
        p = self.source / 'CAPSULE.json'; obj = json.loads(p.read_text())
        obj['expanded_bytes'] = 10**12; p.write_text(json.dumps(obj))
        with self.assertRaises(ValueError): restore(self.source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_existing(self):
        self.dest.mkdir(); marker = self.dest / 'untouched'; marker.write_text('keep')
        with self.assertRaises(FileExistsError): restore(self.source, self.dest)
        self.assertEqual(marker.read_text(), 'keep')

if __name__ == '__main__': unittest.main()
