"""Data-only packaging checks; no scientific worker is launched."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify import restore, ROOT, sha


class DeliveryTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'out'
            self.assertEqual(restore(ROOT, dest), 94)
            manifest = json.loads((ROOT / 'EVIDENCE.json').read_bytes())
            self.assertEqual(sha((dest / 'formal/case-4/case.json').read_bytes()),
                             manifest['members']['formal/case-4/case.json']['sha256'])
            with self.assertRaises(FileExistsError):
                restore(ROOT, dest)

    def test_corruptions(self):
        for kind in ('part', 'missing', 'archive', 'decoded', 'member', 'source', 'path', 'inventory'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'published'
                root.mkdir()
                manifest = json.loads((ROOT / 'EVIDENCE.json').read_bytes())
                names = list(manifest['sources']) + [p['path'] for p in manifest['parts']]
                for name in names:
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / name, path)
                first = root / manifest['parts'][0]['path']
                if kind == 'part':
                    first.write_bytes(b'x' + first.read_bytes()[1:])
                elif kind == 'missing':
                    first.unlink()
                elif kind == 'archive':
                    manifest['archive_sha256'] = '0' * 64
                elif kind == 'decoded':
                    manifest['decoded_bytes'] += 1
                elif kind == 'member':
                    manifest['members']['AUDIT.json']['sha256'] = '0' * 64
                elif kind == 'source':
                    (root / 'audit.py').write_bytes(b'changed')
                elif kind == 'path':
                    manifest['parts'][0]['path'] = '../escape'
                else:
                    del manifest['members']['AUDIT.json']
                (root / 'EVIDENCE.json').write_text(json.dumps(manifest))
                with self.assertRaises((ValueError, FileNotFoundError)):
                    restore(root, Path(tmp) / 'out')


if __name__ == '__main__':
    unittest.main()
