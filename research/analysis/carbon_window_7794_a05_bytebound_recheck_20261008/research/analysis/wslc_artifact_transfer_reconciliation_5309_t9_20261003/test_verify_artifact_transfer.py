"""Mutation checks for the offline T7/T8 artifact reconciliation."""
from __future__ import annotations

import base64
import copy
import json
import unittest
from pathlib import Path

from verify_artifact_transfer import AuditError, audit, reconcile_bytes


FIXTURE = Path(__file__).parent / "inputs" / "artifact_snapshots.json"


class ArtifactTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.result = audit(cls.document)

    def test_frozen_artifacts_reconcile(self) -> None:
        self.assertEqual(self.result["status"], "PASS_ARTIFACT_TRANSFER_PROVENANCE_RECONCILED")
        self.assertEqual(self.result["comparison"]["appended_suffix_hex"], "0d0a")
        self.assertFalse(self.result["scope"]["t7_formal_stop_changed"])

    def test_extra_remote_byte_is_rejected(self) -> None:
        artifacts = self.document["artifacts"]
        capture = base64.b64decode(artifacts["captured_stdout"]["base64"])
        committed = base64.b64decode(artifacts["t7_committed_stdout"]["base64"])
        with self.assertRaises(AuditError):
            reconcile_bytes(capture, committed + b"x")

    def test_lf_only_suffix_is_rejected(self) -> None:
        capture = base64.b64decode(self.document["artifacts"]["captured_stdout"]["base64"])
        with self.assertRaises(AuditError):
            reconcile_bytes(capture, capture + b"\n")

    def test_content_mutation_is_rejected(self) -> None:
        capture = bytearray(base64.b64decode(self.document["artifacts"]["captured_stdout"]["base64"]))
        capture[0] ^= 1
        committed = base64.b64decode(self.document["artifacts"]["t7_committed_stdout"]["base64"])
        with self.assertRaises(AuditError):
            reconcile_bytes(bytes(capture), committed)

    def test_captured_sha256_mismatch_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["artifacts"]["captured_stdout"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(AuditError, "SHA-256"):
            audit(document)

    def test_t7_git_blob_mismatch_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["artifacts"]["t7_committed_stdout"]["git_blob_sha1"] = "0" * 40
        with self.assertRaisesRegex(AuditError, "Git blob"):
            audit(document)

    def test_corrupt_base64_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["artifacts"]["t7_committed_stdout"]["base64"] = "not base64!"
        with self.assertRaises(AuditError):
            audit(document)

    def test_distinct_receipt_values_are_rejected(self) -> None:
        with self.assertRaises(AuditError):
            reconcile_bytes(b'{"value":1}\n', b'{"value":2}\n\r\n')


if __name__ == "__main__":
    unittest.main(verbosity=2)

