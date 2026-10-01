"""Publication-only negative controls; no scientific process is restarted."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from restore import restore

ROOT = Path(__file__).resolve().parent


class RestoreTests(unittest.TestCase):
    def probe(self, mutate=None, existing=False):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            src = p / 'capsule'
            src.mkdir()
            for name in ['CAPSULE.json'] + [x.name for x in ROOT.glob('evidence-*.xz.part')]:
                shutil.copyfile(ROOT / name, src / name)
            dest = p / 'restored'
            if existing:
                dest.mkdir()
            if mutate:
                mutate(src)
            return restore(src, dest)

    def change(self, key, value):
        def mutate(p):
            m = json.loads((p / 'CAPSULE.json').read_text())
            m[key] = value
            (p / 'CAPSULE.json').write_text(json.dumps(m))
        return mutate

    def test_intact(self):
        self.assertEqual(self.probe()['files'], 651)

    def test_changed_part(self):
        def change(p):
            f = p / 'evidence-00.xz.part'
            b = bytearray(f.read_bytes()); b[100] ^= 1; f.write_bytes(b)
        with self.assertRaisesRegex(ValueError, 'PART_DIGEST'):
            self.probe(change)

    def test_reordered_parts(self):
        def change(p):
            m = json.loads((p / 'CAPSULE.json').read_text()); m['parts'].reverse()
            (p / 'CAPSULE.json').write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, 'PART_ORDER'):
            self.probe(change)

    def test_wrong_count(self):
        with self.assertRaisesRegex(ValueError, 'MEMBER_COUNT'):
            self.probe(self.change('members', 650))

    def test_expanded_bound(self):
        with self.assertRaisesRegex(ValueError, 'EXPANDED_DIGEST_OR_BOUND'):
            self.probe(self.change('tar_bytes', 1024))

    def test_bool_count(self):
        with self.assertRaisesRegex(ValueError, 'BOUND'):
            self.probe(self.change('members', True))

    def test_existing_destination(self):
        with self.assertRaisesRegex(ValueError, 'DESTINATION_EXISTS'):
            self.probe(existing=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
