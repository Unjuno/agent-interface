import hashlib
import tempfile
import unittest
from pathlib import Path

from audit import classify_protocol_deviation, verify_raw_checksums


class ProtocolDeviationTests(unittest.TestCase):
    def setUp(self):
        self.freeze = {
            "purpose": "identify startup stage; no planner turn or model call",
            "diagnostic_adapter": {"diagnostic_sha256": "expected-marker-source"},
        }
        self.adapter = {"file": "research/doom/session_map01_v12.py"}

    def test_matching_model_free_diagnostic_source_is_not_a_deviation(self):
        reasons, deviation, expected, actual = classify_protocol_deviation(
            self.freeze, self.adapter,
            {"doom/session_map01_v12.py": "expected-marker-source"}, 0,
        )
        self.assertFalse(deviation)
        self.assertEqual(reasons, {
            "planner_turns_when_forbidden": False,
            "declared_diagnostic_source_not_executed": False,
        })
        self.assertEqual((expected, actual), ("expected-marker-source", "expected-marker-source"))

    def test_unexpected_planner_turn_is_a_deviation(self):
        _, deviation, _, _ = classify_protocol_deviation(
            self.freeze, self.adapter,
            {"doom/session_map01_v12.py": "expected-marker-source"}, 1,
        )
        self.assertTrue(deviation)

    def test_wrong_or_missing_diagnostic_source_is_a_deviation_without_turns(self):
        for runtime_sources in (
            {"doom/session_map01_v12.py": "ordinary-source"},
            {},
        ):
            with self.subTest(runtime_sources=runtime_sources):
                reasons, deviation, expected, actual = classify_protocol_deviation(
                    self.freeze, self.adapter, runtime_sources, 0,
                )
                self.assertTrue(deviation)
                self.assertTrue(reasons["declared_diagnostic_source_not_executed"])
                self.assertEqual(expected, "expected-marker-source")
                self.assertEqual(actual, runtime_sources.get("doom/session_map01_v12.py"))


class RawChecksumTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "raw").mkdir()
        (self.root / "raw" / "event.jsonl").write_bytes(b"{}\n")
        digest = hashlib.sha256(b"{}\n").hexdigest()
        self.manifest = self.root / "RAW_SHA256SUMS.txt"
        self.manifest.write_bytes(f"{digest}  raw/event.jsonl\r\n".encode())

    def test_crlf_manifest_with_exact_raw_set_passes(self):
        result = verify_raw_checksums(self.root, self.manifest)
        self.assertTrue(result["passed"])
        self.assertEqual(result["manifest_entries"], 1)
        self.assertEqual(result["matched_files"], 1)

    def test_changed_raw_bytes_fail(self):
        (self.root / "raw" / "event.jsonl").write_bytes(b"tampered\n")
        result = verify_raw_checksums(self.root, self.manifest)
        self.assertFalse(result["passed"])
        self.assertEqual(result["mismatched_paths"], ["raw/event.jsonl"])

    def test_unlisted_raw_file_fails(self):
        (self.root / "raw" / "extra.bin").write_bytes(b"extra")
        result = verify_raw_checksums(self.root, self.manifest)
        self.assertFalse(result["passed"])
        self.assertEqual(result["unlisted_paths"], ["raw/extra.bin"])

    def test_path_traversal_in_manifest_is_rejected(self):
        digest = hashlib.sha256(b"outside").hexdigest()
        self.manifest.write_text(f"{digest}  raw/../outside\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid checksum manifest entry"):
            verify_raw_checksums(self.root, self.manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
