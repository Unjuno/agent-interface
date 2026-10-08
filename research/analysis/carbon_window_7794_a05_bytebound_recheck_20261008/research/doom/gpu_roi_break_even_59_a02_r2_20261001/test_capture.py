import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from run_capture import publish_candidate_stdout


SOURCE_SHA = "a" * 64
ALLOC = "MAP01-ROI-BREAK-EVEN-59-GPU-20261001-02"
SCHEMA = "map01-roi-gpu-break-even-raw-v2"


def candidate_bytes(parity=True, source_sha=SOURCE_SHA):
    status = "DIAGNOSTIC_COMPLETE" if parity else "FAIL_GPU_CPU_PARITY"
    return json.dumps({
        "schema": SCHEMA,
        "allocation": ALLOC,
        "source_sha256": source_sha,
        "parity": parity,
        "status": status,
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")


class CapturePublicationTests(unittest.TestCase):
    def test_complete_candidate_is_atomically_published_with_matching_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            stdout = candidate_bytes()
            result = publish_candidate_stdout(stdout, b"", 0, Path(temp), SOURCE_SHA)
            raw = Path(temp, "candidate.json").read_bytes()
            receipt = json.loads(Path(temp, "publication_receipt.json").read_text())
            self.assertTrue(result["raw_published"])
            self.assertEqual(raw, stdout)
            self.assertEqual(receipt["raw_sha256"], hashlib.sha256(raw).hexdigest())

    def test_truncated_json_is_preserved_as_partial_but_never_scientific_raw(self):
        with tempfile.TemporaryDirectory() as temp:
            result = publish_candidate_stdout(b'{"schema":"broken"', b"warn", 0, Path(temp), SOURCE_SHA)
            self.assertFalse(result["raw_published"])
            self.assertFalse(Path(temp, "candidate.json").exists())
            self.assertEqual(Path(temp, "candidate.stdout.partial").read_bytes(), b'{"schema":"broken"')

    def test_setup_stop_exit_is_not_published_as_completed_result(self):
        with tempfile.TemporaryDirectory() as temp:
            result = publish_candidate_stdout(b'{"status":"STOP_CUDA_UNAVAILABLE"}', b"", 2, Path(temp), SOURCE_SHA)
            self.assertFalse(result["raw_published"])
            self.assertFalse(Path(temp, "candidate.json").exists())

    def test_source_digest_mismatch_is_retained_but_not_published(self):
        with tempfile.TemporaryDirectory() as temp:
            result = publish_candidate_stdout(candidate_bytes(source_sha="b" * 64), b"", 0, Path(temp), SOURCE_SHA)
            self.assertFalse(result["raw_published"])
            self.assertIn("source_sha256", result["stop_reason"])
            self.assertFalse(Path(temp, "candidate.json").exists())

    def test_complete_parity_failure_is_published_for_independent_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            result = publish_candidate_stdout(candidate_bytes(parity=False), b"", 1, Path(temp), SOURCE_SHA)
            self.assertTrue(result["raw_published"])
            self.assertEqual(json.loads(Path(temp, "candidate.json").read_bytes())["status"], "FAIL_GPU_CPU_PARITY")

    def test_existing_raw_is_never_overwritten_by_a_later_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            raw_path = Path(temp, "candidate.json")
            raw_path.write_bytes(b"immutable prior evidence")
            result = publish_candidate_stdout(candidate_bytes(), b"", 0, Path(temp), SOURCE_SHA)
            self.assertFalse(result["raw_published"])
            self.assertEqual(result["stop_reason"], "output_path_already_exists")
            self.assertEqual(raw_path.read_bytes(), b"immutable prior evidence")


if __name__ == "__main__":
    unittest.main()

