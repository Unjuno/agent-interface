"""Successor contract tests for the frozen Issue #5730 gate."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gate
from gate import run_gated

COMMIT = "733981dda72414c33d12c0687430989f12366db0"
MANIFEST = {"commit": COMMIT, "files": {"runner.py": "a" * 64}}
MANIFEST_SHA = hashlib.sha256(json.dumps(MANIFEST, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
INVENTORY = {"returncode": 0, "stdout": b'{"compute_processes":[]}', "stderr": b""}
VALID_JSON = b'{"schema":"synthetic-v1","result":"ok"}'


class GateCorrectionTests(unittest.TestCase):
    def test_successful_empty_inventory_is_idle_not_stop(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.json"
            result = run_gated(
                {"returncode": 0, "stdout": b"", "stderr": b""}, MANIFEST, MANIFEST_SHA,
                lambda: calls.append("called") or {"returncode": 0, "stdout": VALID_JSON}, output,
            )
        self.assertEqual(result["status"], "ARTIFACT_PUBLISHED")
        self.assertEqual(calls, ["called"])

    def test_tampered_post_replace_artifact_is_removed_after_stop(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.json"
            original_link = gate.os.link

            def link_then_corrupt(source, destination):
                original_link(source, destination)
                Path(destination).write_bytes(b"tampered-after-replace")

            with patch.object(gate.os, "link", side_effect=link_then_corrupt):
                result = run_gated(
                    INVENTORY, MANIFEST, MANIFEST_SHA,
                    lambda: calls.append("called") or {"returncode": 0, "stdout": VALID_JSON}, output,
                )
            self.assertEqual(result["status"], "STOP_POSTWRITE_DIGEST_MISMATCH")
            self.assertEqual(calls, ["called"])
            self.assertFalse(output.exists(), "STOP must leave no published artifact residue")

    def test_missing_inventory_stdout_is_stop_before_candidate(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            result = run_gated(
                {"returncode": 0, "stdout": None}, MANIFEST, MANIFEST_SHA,
                lambda: calls.append("called") or {"returncode": 0, "stdout": VALID_JSON},
                Path(directory) / "raw.json",
            )
        self.assertEqual(result["status"], "STOP_INVENTORY_OUTPUT_MISSING")
        self.assertEqual(result["candidate_invocations"], 0)
        self.assertEqual(calls, [])

    def test_nonzero_inventory_exit_is_stop_before_candidate(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            result = run_gated(
                {"returncode": 9, "stdout": b""}, MANIFEST, MANIFEST_SHA,
                lambda: calls.append("called") or {"returncode": 0, "stdout": VALID_JSON},
                Path(directory) / "raw.json",
            )
        self.assertEqual(result["status"], "STOP_INVENTORY_COMMAND_FAILED")
        self.assertEqual(calls, [])

    def test_existing_output_is_preserved_and_candidate_result_not_published(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.json"
            output.write_bytes(b"pre-existing")
            result = run_gated(
                INVENTORY, MANIFEST, MANIFEST_SHA,
                lambda: calls.append("called") or {"returncode": 0, "stdout": VALID_JSON}, output,
            )
            self.assertEqual(result["status"], "STOP_OUTPUT_PATH_ALREADY_EXISTS")
            self.assertEqual(output.read_bytes(), b"pre-existing")
        self.assertEqual(calls, ["called"])

    def test_success_publishes_exact_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.json"
            result = run_gated(
                INVENTORY, MANIFEST, MANIFEST_SHA,
                lambda: {"returncode": 0, "stdout": VALID_JSON}, output,
            )
            self.assertEqual(result["status"], "ARTIFACT_PUBLISHED")
            self.assertEqual(result["scientific_result"], "READY_FOR_INDEPENDENT_AUDIT")
            self.assertEqual(result["raw_sha256"], hashlib.sha256(VALID_JSON).hexdigest())
            self.assertEqual(output.read_bytes(), VALID_JSON)

    def test_cleanup_failure_has_typed_stop_and_no_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.json"
            original_link = gate.os.link

            def link_then_corrupt(source, destination):
                original_link(source, destination)
                Path(destination).write_bytes(b"tampered-after-link")

            with patch.object(gate.os, "link", side_effect=link_then_corrupt), \
                 patch.object(Path, "unlink", side_effect=PermissionError("synthetic cleanup denial")):
                result = run_gated(
                    INVENTORY, MANIFEST, MANIFEST_SHA,
                    lambda: {"returncode": 0, "stdout": VALID_JSON}, output,
                )
            self.assertEqual(result["status"], "STOP_OUTPUT_CLEANUP_FAILED")
            self.assertEqual(result["scientific_result"], "NOT_EVALUATED")
            self.assertIsNone(result["raw_sha256"])
            self.assertTrue(output.exists(), "cleanup STOP explicitly records residue still exists")

    def test_atomic_publish_denial_is_typed_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.json"
            with patch.object(gate.os, "link", side_effect=PermissionError("synthetic filesystem denial")):
                result = run_gated(
                    INVENTORY, MANIFEST, MANIFEST_SHA,
                    lambda: {"returncode": 0, "stdout": VALID_JSON}, output,
                )
            self.assertEqual(result["status"], "STOP_OUTPUT_PUBLISH_FAILED")
            self.assertEqual(result["scientific_result"], "NOT_EVALUATED")
            self.assertIsNone(result["raw_sha256"])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
