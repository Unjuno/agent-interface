from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from stage_and_run import copy_verified


class CopyVerifiedTests(unittest.TestCase):
    def test_exact_copy_preserves_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.bin"
            target = root / "target.bin"
            source.write_bytes(b"frozen bytes\x00\n")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(copy_verified(source, target, digest), digest)
            self.assertEqual(target.read_bytes(), source.read_bytes())

    def test_wrong_hash_refuses_before_destination_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.bin"
            target = root / "target.bin"
            source.write_bytes(b"frozen bytes\x00\n")
            with self.assertRaisesRegex(ValueError, "source_hash_mismatch"):
                copy_verified(source, target, "0" * 64)
            self.assertFalse(target.exists())

    def test_exclusive_destination_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.bin"
            target = root / "target.bin"
            source.write_bytes(b"frozen bytes\x00\n")
            target.write_bytes(b"preserve me")
            with self.assertRaises(FileExistsError):
                copy_verified(source, target)
            self.assertEqual(target.read_bytes(), b"preserve me")


if __name__ == "__main__":
    unittest.main()
