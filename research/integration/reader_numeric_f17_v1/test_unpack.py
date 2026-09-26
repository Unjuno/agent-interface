"""Post-result packaging tests only; never starts the measured CLI."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import unpack

class Restoration(unittest.TestCase):
    def test_exact_members(self):
        self.assertEqual(len(unpack.decode()), 73)
    def test_existing_destination(self):
        with tempfile.TemporaryDirectory() as path:
            with self.assertRaises(FileExistsError):
                unpack.restore(Path(path))
    def test_missing_part(self):
        with tempfile.TemporaryDirectory() as path:
            dest = Path(path)
            shutil.copy(unpack.ROOT/'CAPSULE.json', dest/'CAPSULE.json')
            with self.assertRaises(FileNotFoundError):
                unpack.decode(dest)
    def test_changed_part(self):
        with tempfile.TemporaryDirectory() as path:
            dest=Path(path)
            manifest=json.loads((unpack.ROOT/'CAPSULE.json').read_text())
            shutil.copy(unpack.ROOT/'CAPSULE.json', dest/'CAPSULE.json')
            for part in manifest['parts']:
                shutil.copy(unpack.ROOT/part['name'], dest/part['name'])
            target=dest/manifest['parts'][0]['name']
            data=target.read_bytes();target.write_bytes(bytes([data[0]^1])+data[1:])
            with self.assertRaisesRegex(ValueError, 'part identity'):
                unpack.decode(dest)
    def test_part_order(self):
        with tempfile.TemporaryDirectory() as path:
            dest=Path(path)
            manifest=json.loads((unpack.ROOT/'CAPSULE.json').read_text())
            for part in manifest['parts']:
                shutil.copy(unpack.ROOT/part['name'], dest/part['name'])
            manifest['parts'].reverse()
            (dest/'CAPSULE.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'capsule identity'):
                unpack.decode(dest)

if __name__ == '__main__':
    unittest.main()
