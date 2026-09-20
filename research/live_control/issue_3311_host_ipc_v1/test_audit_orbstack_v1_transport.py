"""Portable, non-mutating checks for the retained transport auditor."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from research.live_control.issue_3311_host_ipc_v1.audit_orbstack_v1_transport import (
    verify_raw_manifest,
)


class RawManifestAuditTest(unittest.TestCase):
    def test_manifest_detects_tampering_without_rewriting_baseline(self):
        with tempfile.TemporaryDirectory(prefix="3311-v1-manifest-") as temp:
            root = Path(temp)
            captured = root / "ipc" / "container.stdout.txt"
            captured.parent.mkdir()
            captured.write_text("original evidence\n", encoding="utf-8")
            manifest = root / "raw-sha256.json"
            manifest.write_text(json.dumps({
                "ipc/container.stdout.txt": hashlib.sha256(captured.read_bytes()).hexdigest(),
            }, indent=2) + "\n", encoding="utf-8")
            original_manifest = manifest.read_bytes()

            self.assertTrue(verify_raw_manifest(root))
            captured.write_text("tampered evidence\n", encoding="utf-8")
            self.assertFalse(verify_raw_manifest(root))
            self.assertEqual(manifest.read_bytes(), original_manifest)

    def test_missing_or_malformed_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="3311-v1-manifest-") as temp:
            root = Path(temp)
            self.assertFalse(verify_raw_manifest(root))
            (root / "raw-sha256.json").write_text("not-json", encoding="utf-8")
            self.assertFalse(verify_raw_manifest(root))


if __name__ == "__main__":
    unittest.main()
