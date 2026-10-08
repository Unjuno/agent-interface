import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gate import run_gated


COMMIT = "5ff239141f49c1603c0f6b078268f4a2f6e082df"
MANIFEST = {"commit": COMMIT, "files": {"runner.py": "a" * 64}}
MANIFEST_SHA = hashlib.sha256(json.dumps(MANIFEST, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
INVENTORY = {"returncode": 0, "stdout": b'{"compute_processes":[]}', "stderr": b""}
VALID_JSON = b'{"schema":"synthetic-v1","result":"ok"}'


class GateConstructionTests(unittest.TestCase):
    def execute(self, inventory=INVENTORY, manifest=MANIFEST, manifest_sha=MANIFEST_SHA,
                candidate_result=None, mutate_output=None):
        calls = []
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "raw.json"

            def candidate():
                calls.append("called")
                return candidate_result if candidate_result is not None else {"returncode": 0, "stdout": VALID_JSON}

            result = run_gated(inventory, manifest, manifest_sha, candidate, output)
            if mutate_output and output.exists():
                mutate_output(output)
            return result, calls, output.exists()

    def test_empty_inventory_stops_before_candidate(self):
        inv = {"returncode": 0, "stdout": b"", "stderr": b""}
        result, calls, exists = self.execute(inventory=inv)
        self.assertEqual(result["status"], "STOP_INVENTORY_OUTPUT_EMPTY_OR_MISSING")
        self.assertEqual(calls, [])
        self.assertFalse(exists)

    def test_inventory_command_failure_stops_before_candidate(self):
        result, calls, _ = self.execute(inventory={"returncode": 2, "stdout": b"{}"})
        self.assertEqual(result["status"], "STOP_INVENTORY_COMMAND_FAILED")
        self.assertEqual(calls, [])

    def test_malformed_inventory_stops_before_candidate(self):
        result, calls, _ = self.execute(inventory={"returncode": 0, "stdout": b"{"})
        self.assertEqual(result["status"], "STOP_INVENTORY_OUTPUT_MALFORMED")
        self.assertEqual(calls, [])

    def test_inventory_schema_mismatch_stops_before_candidate(self):
        result, calls, _ = self.execute(inventory={"returncode": 0, "stdout": b'{"processes":[]}'} )
        self.assertEqual(result["status"], "STOP_INVENTORY_SCHEMA_INVALID")
        self.assertEqual(calls, [])

    def test_incomplete_source_identity_stops_before_candidate(self):
        result, calls, _ = self.execute(manifest={"commit": "", "files": {}})
        self.assertEqual(result["status"], "STOP_SOURCE_IDENTITY_INCOMPLETE")
        self.assertEqual(calls, [])

    def test_changed_source_digest_stops_before_candidate(self):
        result, calls, _ = self.execute(manifest_sha="0" * 64)
        self.assertEqual(result["status"], "STOP_SOURCE_IDENTITY_CHANGED")
        self.assertEqual(calls, [])

    def test_candidate_nonzero_is_not_evaluated(self):
        result, calls, exists = self.execute(candidate_result={"returncode": 7, "stdout": VALID_JSON})
        self.assertEqual(result["status"], "STOP_CANDIDATE_NONZERO")
        self.assertEqual(result["scientific_result"], "NOT_EVALUATED")
        self.assertIsNone(result["raw_sha256"])
        self.assertEqual(len(calls), 1)
        self.assertFalse(exists)

    def test_absent_candidate_output_is_not_evaluated(self):
        result, calls, exists = self.execute(candidate_result={"returncode": 0, "stdout": b""})
        self.assertEqual(result["status"], "STOP_OUTPUT_MISSING_OR_TRUNCATED")
        self.assertIsNone(result["raw_sha256"])
        self.assertEqual(len(calls), 1)
        self.assertFalse(exists)

    def test_truncated_candidate_json_is_not_published(self):
        result, calls, exists = self.execute(candidate_result={"returncode": 0, "stdout": b'{"result":'})
        self.assertEqual(result["status"], "STOP_OUTPUT_MISSING_OR_TRUNCATED")
        self.assertIsNone(result["raw_sha256"])
        self.assertEqual(len(calls), 1)
        self.assertFalse(exists)

    def test_success_is_atomically_published_and_hashed(self):
        result, calls, exists = self.execute()
        self.assertEqual(result["status"], "ARTIFACT_PUBLISHED")
        self.assertEqual(result["scientific_result"], "READY_FOR_INDEPENDENT_AUDIT")
        self.assertEqual(result["raw_sha256"], hashlib.sha256(VALID_JSON).hexdigest())
        self.assertEqual(len(calls), 1)
        self.assertTrue(exists)

    def test_postwrite_digest_mismatch_is_not_evaluated(self):
        calls = []
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "raw.json"
            original_replace = __import__("os").replace

            def replace_then_corrupt(source, destination):
                original_replace(source, destination)
                Path(destination).write_bytes(b"tampered-after-replace")

            def candidate():
                calls.append("called")
                return {"returncode": 0, "stdout": VALID_JSON}

            with patch("gate.os.replace", side_effect=replace_then_corrupt):
                result = run_gated(INVENTORY, MANIFEST, MANIFEST_SHA, candidate, output)
            self.assertEqual(result["status"], "STOP_POSTWRITE_DIGEST_MISMATCH")
            self.assertEqual(result["scientific_result"], "NOT_EVALUATED")
            self.assertIsNone(result["raw_sha256"])
            self.assertEqual(calls, ["called"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
