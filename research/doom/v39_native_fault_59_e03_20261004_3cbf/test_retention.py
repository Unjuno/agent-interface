import hashlib
from pathlib import Path
import tempfile
import unittest
from verify_retention import check_manifest


class HashRetentionTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'raw.bin').write_bytes(b'evidence\n')
        digest = hashlib.sha256(b'evidence\n').hexdigest()
        path = root / 'MANIFEST'; path.write_text(digest + '  raw.bin\n')
        return path

    def test_accepts_exact_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); manifest = self.fixture(root)
            self.assertEqual(check_manifest(root, manifest), 1)

    def test_rejects_changed_missing_and_escaped_payload(self):
        for mode in ('changed', 'missing', 'escape', 'duplicate'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); manifest = self.fixture(root)
                if mode == 'changed': (root / 'raw.bin').write_bytes(b'changed\n')
                elif mode == 'missing': (root / 'raw.bin').unlink()
                elif mode == 'escape': manifest.write_text('0' * 64 + '  ../outside.bin\n')
                elif mode == 'duplicate': manifest.write_text(manifest.read_text() * 2)
                with self.assertRaises((ValueError, FileNotFoundError)):
                    check_manifest(root, manifest)


if __name__ == '__main__':
    unittest.main()
