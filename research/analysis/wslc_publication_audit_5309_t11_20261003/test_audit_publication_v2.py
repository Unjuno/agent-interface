"""Regression and mutation tests for retained T7 publication-byte audits."""
from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path


AUDITOR_PATH = Path(os.environ.get("T7_AUDITOR_UNDER_TEST", str(Path(__file__).with_name("audit_publication.py"))))
INPUT_PATH = Path(__file__).parent / "inputs" / "t7_remote_blob_manifest.json"
spec = importlib.util.spec_from_file_location("publication_auditor_under_test", AUDITOR_PATH)
assert spec is not None and spec.loader is not None
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)
SOURCE = b'{"receipt":"ok"}\n'


class PublicationAuditV2Tests(unittest.TestCase):
    def test_exact_source_is_accepted(self) -> None:
        self.assertEqual(auditor.classify_remote_blob(SOURCE, auditor.git_blob_sha1(SOURCE), len(SOURCE)), "EXACT_SOURCE")

    def test_source_plus_crlf_is_accepted(self) -> None:
        changed = SOURCE + b"\r\n"
        self.assertEqual(auditor.classify_remote_blob(SOURCE, auditor.git_blob_sha1(changed), len(changed)), "SOURCE_PLUS_CRLF")

    def test_source_plus_lf_is_rejected(self) -> None:
        with self.assertRaises(auditor.AuditError):
            auditor.classify_remote_blob(SOURCE, auditor.git_blob_sha1(SOURCE + b"\n"), len(SOURCE) + 1)

    def test_non_newline_content_change_is_rejected(self) -> None:
        changed = b'{"receipt":"no"}\r\n'
        with self.assertRaises(auditor.AuditError):
            auditor.classify_remote_blob(SOURCE, auditor.git_blob_sha1(changed), len(changed))

    def test_extra_bytes_after_crlf_are_rejected(self) -> None:
        changed = SOURCE + b"\r\nx"
        with self.assertRaises(auditor.AuditError):
            auditor.classify_remote_blob(SOURCE, auditor.git_blob_sha1(changed), len(changed))

    def test_remote_blob_id_mismatch_is_rejected(self) -> None:
        with self.assertRaises(auditor.AuditError):
            auditor.classify_remote_blob(SOURCE, "0" * 40, len(SOURCE))

    def test_invalid_remote_blob_id_is_rejected(self) -> None:
        with self.assertRaises(auditor.AuditError):
            auditor.classify_remote_blob(SOURCE, "not-a-git-blob", len(SOURCE))

    def test_local_source_hash_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(auditor.AuditError, "SHA-256"):
            auditor.validate_source(SOURCE, len(SOURCE), "0" * 64)

    def test_classification_survives_through_manifest_phase(self) -> None:
        document = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
        try:
            result = auditor.audit(document)
        except KeyError as exc:
            self.fail(f"manifest verification lost a previously computed file classification: {exc}")
        self.assertEqual(result["status"], "PASS_T7_PUBLICATION_BYTES_CLASSIFIED")
        self.assertEqual(result["file_count"], 11)
        self.assertEqual(result["source_plus_crlf_count"], 11)
        self.assertEqual(result["exact_source_count"], 0)
        self.assertTrue(result["manifest_claims_checked"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
