from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from verify_transport import materialize, payload


class TransportVerificationTests(unittest.TestCase):
    def test_accepts_exact_payload_and_one_transport_suffix(self):
        content = b"frozen bytes\n"
        digest = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.txt"
            path.write_bytes(content + b"\r\n")
            normalized, suffix = payload(path, digest, len(content))
            self.assertEqual(normalized, content)
            self.assertTrue(suffix)

    def test_rejects_more_than_one_extra_suffix(self):
        content = b"frozen bytes\n"
        digest = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.txt"
            path.write_bytes(content + b"\r\n\r\n")
            with self.assertRaisesRegex(ValueError, "sha256 mismatch"):
                payload(path, digest, len(content))

    def test_materialize_refuses_destination_inside_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            with self.assertRaisesRegex(ValueError, "outside"):
                materialize(root, root / "copy")


if __name__ == "__main__":
    unittest.main(verbosity=2)

