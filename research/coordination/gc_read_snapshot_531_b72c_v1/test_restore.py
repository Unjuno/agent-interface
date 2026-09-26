"""Publication checks only: no actor, runner, model or GUI execution."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from restore import decode, restore

ROOT = Path(__file__).resolve().parent

class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'bundle'
        self.root.mkdir()
        for path in ROOT.iterdir():
            if path.is_file(): shutil.copyfile(path, self.root / path.name)

    def tearDown(self): self.tmp.cleanup()

    def change_meta(self, update):
        path = self.root / 'CAPSULE.json'
        meta = json.loads(path.read_text()); update(meta)
        path.write_text(json.dumps(meta))

    def assert_rejected(self):
        with self.assertRaises(ValueError): decode(self.root)

    def test_intact(self):
        files = decode(self.root)
        self.assertEqual(len(files), 917)
        self.assertNotIn('PREDECESSOR_A61E.tar.xz', files)

    def test_restore(self):
        out = Path(self.tmp.name) / 'result'
        result = restore(self.root, out)
        self.assertEqual(result['restored_files'], 917)
        self.assertEqual((out / 'AUDIT.json').read_bytes(), (ROOT / 'AUDIT.json').read_bytes())

    def test_changed_part(self):
        path = self.root / 'capsule-00.bin'; data = bytearray(path.read_bytes())
        data[20] ^= 1; path.write_bytes(data); self.assert_rejected()

    def test_truncated_part(self):
        path = self.root / 'capsule-06.bin'; path.write_bytes(path.read_bytes()[:-1])
        self.assert_rejected()

    def test_reordered_parts(self):
        self.change_meta(lambda m: m['parts'].reverse()); self.assert_rejected()

    def test_boolean_count(self):
        self.change_meta(lambda m: m.update(file_count=True)); self.assert_rejected()

    def test_wrong_manifest(self):
        self.change_meta(lambda m: m.update(original_manifest_sha256='0'*64)); self.assert_rejected()

    def test_hidden_exclusion(self):
        self.change_meta(lambda m: m['excluded_ancestor'].update(path='formal/RAW.jsonl'))
        self.assert_rejected()

    def test_changed_readable_source(self):
        path = self.root / 'actor.py'; path.write_bytes(path.read_bytes()+b'\n')
        self.assert_rejected()

    def test_existing_destination(self):
        out = Path(self.tmp.name) / 'existing'; out.mkdir()
        with self.assertRaises(ValueError): restore(self.root, out)
        self.assertEqual(list(out.iterdir()), [])

if __name__ == '__main__': unittest.main(verbosity=2)
