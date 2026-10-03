"""Construction checks for the WSLc staging wrapper; no candidate/audit run."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import run_wslc


class WrapperConstructionTests(unittest.TestCase):
    def test_frozen_source_hashes_match_main_checkout(self) -> None:
        root = Path(__file__).resolve().parents[1] / "belief_external_drift_5368_t0_20261003"
        for name, expected in run_wslc.SOURCE_HASHES.items():
            with self.subTest(name=name):
                self.assertEqual(run_wslc.sha256(root / name), expected)

    def test_source_verification_rejects_modified_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixture.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source_hash_mismatch"):
                run_wslc.verify_source(path, "fixture.json")

    def test_exclusive_copy_preserves_bytes_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            destination = root / "destination"
            source.write_bytes(b"frozen\x00bytes\n")
            digest = run_wslc.copy_exclusive(source, destination)
            expected = hashlib.sha256(b"frozen\x00bytes\n").hexdigest()
            self.assertEqual(digest, expected)
            self.assertEqual(destination.read_bytes(), source.read_bytes())

    def test_exclusive_copy_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            destination = root / "destination"
            source.write_text("new", encoding="utf-8")
            destination.write_text("preserved", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                run_wslc.copy_exclusive(source, destination)
            self.assertEqual(destination.read_text(encoding="utf-8"), "preserved")


if __name__ == "__main__":
    unittest.main()
