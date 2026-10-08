"""Postformal archive-delivery controls; no application or experiment execution."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import unpack

HERE = Path(__file__).resolve().parent

class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='inkscape-delivery-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        for path in HERE.glob('evidence-*.xz.part'):
            shutil.copyfile(path, self.source / path.name)
        self.manifest = json.loads((HERE / 'ARCHIVE.json').read_bytes())
        self.write_manifest()

    def write_manifest(self):
        (self.source / 'ARCHIVE.json').write_text(json.dumps(self.manifest), encoding='utf-8')

    def refused(self, reason):
        destination = self.root / 'output'
        with self.assertRaisesRegex(ValueError, reason):
            unpack.restore(self.source, destination)
        self.assertFalse(destination.exists())

    def test_part_digest(self):
        path = self.source / self.manifest['parts'][0]['path']
        data = bytearray(path.read_bytes())
        data[-1] ^= 1
        path.write_bytes(data)
        self.refused('part digest')

    def test_part_order(self):
        self.manifest['parts'].reverse()
        self.write_manifest()
        self.refused('archive identity')

    def test_member_count(self):
        self.manifest['members'] += 1
        self.write_manifest()
        self.refused('member count')

    def test_expansion_bound(self):
        self.manifest['expanded_bytes'] = unpack.MAX_EXPANDED + 1
        self.write_manifest()
        self.refused('invalid bound: expanded_bytes')

    def test_boolean_count(self):
        self.manifest['members'] = True
        self.write_manifest()
        self.refused('invalid bound: members')

    def test_parent_part_path(self):
        self.manifest['parts'][0]['path'] = '../outside'
        self.write_manifest()
        self.refused('part path')

    def test_existing_destination(self):
        destination = self.root / 'output'
        destination.mkdir()
        sentinel = destination / 'sentinel'
        sentinel.write_bytes(b'unchanged')
        with self.assertRaisesRegex(ValueError, 'destination exists'):
            unpack.restore(self.source, destination)
        self.assertEqual(sentinel.read_bytes(), b'unchanged')
        self.assertEqual(list(destination.iterdir()), [sentinel])

if __name__ == '__main__':
    unittest.main()
