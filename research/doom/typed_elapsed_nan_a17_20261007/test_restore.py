"""Post-result packaging checks; no subject/matrix invocation."""
from copy import deepcopy
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import lzma

import restore_results

ROOT = Path(__file__).resolve().parent


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.meta = json.loads((ROOT / 'PACK.json').read_text())
        self.wire = ''.join((ROOT / ('results.xz.b64.part%02d' % i)).read_text() for i in (1, 2, 3, 4))

    def test_complete_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'new'
            restore_results.restore(self.meta, self.wire, out)
            self.assertEqual(sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()), sorted(self.meta['files']))
            for name, row in self.meta['files'].items():
                b = (out / name).read_bytes()
                self.assertEqual(len(b), row['bytes'])
                self.assertEqual(hashlib.sha256(b).hexdigest(), row['sha256'])

    def test_bad_digest(self):
        m = deepcopy(self.meta); m['compressed_sha256'] = '0' * 64
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                restore_results.restore(m, self.wire, Path(tmp) / 'new')

    def test_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError):
                restore_results.restore(self.meta, self.wire, Path(tmp))

    def test_bound(self):
        m = deepcopy(self.meta); m['expanded_bytes'] = 1
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                restore_results.restore(m, self.wire, Path(tmp) / 'new')

    def test_malformed_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                restore_results.restore(self.meta, '!' + self.wire, Path(tmp) / 'new')

    def test_unsafe_path_with_rehashed_payload(self):
        payload = {'../escape.txt': 'x'}
        data = json.dumps(payload).encode(); packed = lzma.compress(data)
        m = {'schema': 'typed-elapsed-results-pack-v2', 'expanded_bytes': len(data),
             'compressed_sha256': hashlib.sha256(packed).hexdigest(),
             'expanded_sha256': hashlib.sha256(data).hexdigest(),
             'files': {'../escape.txt': {'bytes': 1, 'sha256': hashlib.sha256(b'x').hexdigest()}}}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                restore_results.restore(m, base64.b64encode(packed).decode(), Path(tmp) / 'new')
            self.assertFalse((Path(tmp) / 'escape.txt').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
