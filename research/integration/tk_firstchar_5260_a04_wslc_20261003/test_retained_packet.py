import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from verify_packet import manifest_errors, stream_errors, visual_file_errors, run_statistics_errors


class RetainedPacketTests(unittest.TestCase):
    def test_summary_cannot_drift_from_audit_or_focus_receipts(self):
        raw = {"allocation": "a", "fixture": {"payload": "hxy"}, "rows": [
            {"app": {"saved_text": "xy", "events": [
                {"kind": "KeyPress", "widget": "decoy", "char": "h", "monotonic_ns": 10},
                {"kind": "FocusIn", "widget": "target", "monotonic_ns": 20}]}},
            {"app": {"saved_text": "hxy", "events": []}}]}
        audit = {"rows": 2, "exact_save_failures": 1, "baseline_image_integrity_rows": 2, "errors": []}
        retained = {"first_visual_ocr_rows": [{"ocr_status": "UNRESOLVED_OR_MISMATCH"}]}
        run = {"allocation": "a", "freeze_sha256": "f", "rows": 2, "exact_save": 1,
            "nonexact_save": 1, "baseline_integrity_rows": 2, "ready_custody_failures": 0,
            "ocr_matches": 0, "first_h_in_decoy_before_target_focus_failures": 1,
            "formal_candidate_invocations": 1, "formal_auditor_invocations": 1, "retries": 0}
        self.assertEqual(run_statistics_errors(run, audit, retained, raw, "f"), [])
        for key, value in (("exact_save", 2), ("rows", 3), ("ocr_matches", 1),
                           ("first_h_in_decoy_before_target_focus_failures", 0),
                           ("freeze_sha256", "other"), ("formal_candidate_invocations", True)):
            self.assertTrue(run_statistics_errors({**run, key: value}, audit, retained, raw, "f"))

    def test_manifest_requires_exact_complete_safe_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "exact.bin").write_bytes(b"exact\r\n\x00")
            line = hashlib.sha256((root / "exact.bin").read_bytes()).hexdigest() + "  exact.bin"
            self.assertEqual(manifest_errors(root, [line]), [])
            for lines in ([], [line, line], ["0" * 64 + "  exact.bin"], ["0" * 64 + "  ../other"]):
                self.assertTrue(manifest_errors(root, lines))
            (root / "nested").mkdir()
            (root / "nested/SHA256SUMS").write_text("not the root manifest")
            self.assertTrue(manifest_errors(root, [line]))

    def test_host_streams_and_attempt_cannot_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempt = {"argv": ["owned"], "started_utc": "2026-10-03T14:00:00+00:00"}
            for name, value in (("attempt.json", json.dumps(attempt).encode()),
                                ("stdout.bin", b"output\n"), ("stderr.bin", b"warning\n")):
                (root / name).write_bytes(value)
            receipt = {**attempt, "finished_utc": "2026-10-03T14:00:01+00:00",
                "wall_seconds": 1, "exit_code": 0, "launch_error": None,
                "output_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}}
            self.assertEqual(stream_errors(root, receipt), [])
            self.assertTrue(stream_errors(root, {**receipt, "exit_code": 1}))
            self.assertTrue(stream_errors(root, {**receipt, "argv": ["different"]}))
            self.assertTrue(stream_errors(root, {**receipt, "finished_utc": "2026-10-03T13:59:00+00:00"}))
            self.assertTrue(stream_errors(root, {**receipt, "output_sha256": {}}))
            (root / "stderr.bin").write_bytes(b"")
            self.assertTrue(stream_errors(root, receipt))

    def test_first_visual_file_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            row = {"app": {"first_visual": {"target_value": "h", "observed_ns": 5}}}
            (root / "first_visual.json").write_text(json.dumps(row["app"]["first_visual"]))
            self.assertEqual(visual_file_errors(root, row), [])
            (root / "first_visual.json").write_text("{}")
            self.assertTrue(visual_file_errors(root, row))


if __name__ == "__main__":
    unittest.main()
