import base64
import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from runtime.cli_v1.review import review, review_bytes
from runtime.distribution_v2.build import SOURCE_FILES, build


class PublicReviewTests(unittest.TestCase):
    def test_portable_cli_returns_exact_image_and_preserves_failed_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            for name in SOURCE_FILES:
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(Path(name).read_bytes())
            archive = root / "runtime.pyz"
            build(source, archive, root / "manifest.json", root / "sums.txt")
            pixels = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII=")
            png = root / "frame.png"
            png.write_bytes(pixels)
            report = root / "report.json"
            report.write_text(json.dumps({"status": "failed", "error": "timeout", "records": [
                {"event": "observation", "sequence": 1, "capture_ns": 12, "image": str(png)}]}))
            original = report.read_bytes()
            command = [sys.executable, str(archive), "review", "--report", str(report), "--run-directory", str(root)]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            row = json.loads(result.stdout)
            self.assertEqual(base64.b64decode(row["image"]["data"]), pixels)
            self.assertEqual(row["receipt"]["report"]["status"], "failed")
            self.assertEqual(row["authority"], "none")
            piped = subprocess.run([sys.executable, str(archive), "review", "--report", "-", "--run-directory", str(root)],
                                   input=original, cwd=root, capture_output=True)
            self.assertEqual(piped.returncode, 0, piped.stderr)
            piped_row = json.loads(piped.stdout)
            self.assertEqual(base64.b64decode(piped_row['image']['data']), pixels)
            self.assertEqual(piped_row['receipt']['source']['sha256'], hashlib.sha256(original).hexdigest())
            self.assertIsNone(piped_row['receipt']['source']['path'])
            png.unlink()
            missing = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            row = json.loads(missing.stdout)
            self.assertEqual(row["image_status"], "needs_review")
            self.assertEqual(row["receipt"]["report"]["error"], "timeout")
            self.assertEqual(report.read_bytes(), original)

    def test_public_observation_image_identity_and_cleanup_failure_survive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            png = root / "frame.png"
            pixels = b"\x89PNG\r\n\x1a\n"
            png.write_bytes(pixels)
            report = root / "report.json"
            observation = {"sha256": "raw", "capture_started_ns": 12,
                "artifact": {"mime_type": "image/png", "path": str(png),
                             "sha256": hashlib.sha256(pixels).hexdigest(),
                             "source_raw_sha256": "raw"}}
            payload = {"schema": "agent-interface/runtime-observation-v1",
                       "observation_id": "capture-id", "status": "observation_failed",
                       "cleanup_error": "close failed", "observation": observation}
            report.write_text(json.dumps(payload))
            row = review(report, root)
            self.assertEqual(base64.b64decode(row["image"]["data"]), pixels)
            self.assertEqual(row["image_reference"]["observation_id"], "capture-id")
            self.assertNotIn("sequence", row["image_reference"])
            self.assertEqual(row["receipt"]["report"]["cleanup_error"], "close failed")
            for field in ("sha256", "source_raw_sha256"):
                original = observation["artifact"][field]
                observation["artifact"][field] = "wrong"
                report.write_text(json.dumps(payload))
                refused = review(report, root)
                self.assertEqual(refused["image_status"], "needs_review")
                self.assertIsNone(refused["image"])
                observation["artifact"][field] = original

    def test_dispatch_last_capture_missing_or_invalid_never_uses_earlier_image(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            png = root / "frame.png"
            pixels = b"\x89PNG\r\n\x1a\n"
            png.write_bytes(pixels)
            capture = {"sha256": "raw", "capture_started_ns": 12,
                "artifact": {"mime_type": "image/png", "path": str(png),
                             "sha256": hashlib.sha256(pixels).hexdigest(),
                             "source_raw_sha256": "raw"}}
            capture.update(target="fixture", native_window_id=42, frame="window_client",
                           region=[20, 75, 180, 45], width=180, height=45, operation_index=4)
            payload = {"schema": "agent-interface/runtime-dispatch-result-v1", "status": "returned",
                       "result": {"status": "execution_failed", "execution": {
                           "error": "late failure", "observations": [capture, capture]}}}
            path = root / "report.json"
            path.write_text(json.dumps(payload))
            row = review(path, root)
            self.assertEqual(row["image_status"], "image")
            self.assertEqual(row["image_reference"]["execution_observation_index"], 1)
            self.assertEqual(row['image_reference']['recorded_capture']['region'], [20, 75, 180, 45])
            self.assertEqual(row['image_reference']['recorded_capture']['frame'], 'window_client')
            self.assertEqual(row['image_reference']['recorded_capture']['native_window_id'], 42)
            self.assertNotIn('capture_ended_ns', row['image_reference']['recorded_capture'])
            self.assertEqual(row['image_reference']['recorded_capture']['operation_index'], 4)
            self.assertEqual(row['image_reference']['authority'], 'none')
            self.assertNotIn("sequence", row["image_reference"])
            self.assertEqual(row["receipt"]["report"]["result"]["status"], "execution_failed")
            for last in ({"artifact_error": "encoding failed"}, None, {}):
                payload["result"]["execution"]["observations"] = [capture, last]
                path.write_text(json.dumps(payload))
                row = review(path, root)
                self.assertEqual(row["image_status"], "needs_review")
                self.assertIsNone(row["image"])
            payload["result"] = {"status": "refused", "error": "stale"}
            path.write_text(json.dumps(payload))
            row = review(path, root)
            self.assertEqual(row["image_status"], "no_observation")
            self.assertEqual(row["receipt"]["report"]["result"]["error"], "stale")

    def test_stdin_preserves_exact_byte_hash_and_full_history_without_file(self):
        with tempfile.TemporaryDirectory() as td:
            raw = b'{ "status": "failed", "records": [{"event":"command","id":"keep"}] }\n'
            command = [sys.executable, '-m', 'runtime.cli_v1', 'review', '--report', '-', '--run-directory', td]
            result = subprocess.run(command, input=raw, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            row = json.loads(result.stdout)
            source = row['receipt']['source']
            self.assertIsNone(source['path'])
            self.assertEqual(source['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(source['raw_report'], json.loads(raw))
            self.assertEqual(list(Path(td).iterdir()), [])
            bad = subprocess.run(command, input=b'{bad', capture_output=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(json.loads(bad.stdout)['status'], 'invalid_receipt')

    def test_outcome_summary_separates_returned_from_refused_and_preserves_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            payload = {'schema': 'agent-interface/runtime-dispatch-result-v1', 'status': 'returned',
                       'result': {'status': 'refused', 'error': 'BACKEND_CONSTRAINT',
                                  'detail': 'unmapped key RIGHT', 'recovery_required': False}}
            row = review_bytes(json.dumps(payload).encode(), td)
            summary = row['outcome_summary']
            self.assertEqual(summary['reported_status'], 'returned')
            self.assertEqual(summary['execution_status'], 'refused')
            self.assertEqual(summary['execution_detail'], 'unmapped key RIGHT')
            self.assertIs(summary['recovery_required'], False)
            self.assertNotIn('task_success', summary)
            payload.update(status='runtime_failed', cleanup_error='close failed')
            payload['result'] = {'status': 'completed', 'recovery_required': 'false'}
            row = review_bytes(json.dumps(payload).encode(), td)
            self.assertEqual(row['outcome_summary']['reported_status'], 'runtime_failed')
            self.assertEqual(row['outcome_summary']['execution_status'], 'completed')
            self.assertEqual(row['outcome_summary']['cleanup_error'], 'close failed')
            self.assertIsNone(row['outcome_summary']['recovery_required'])
            self.assertEqual(row['receipt']['source']['raw_report'], payload)

    def test_newest_missing_image_never_falls_back_to_older_capture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            png = root / "old.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n")
            report = root / "report.json"
            report.write_text(json.dumps({"status": "boundary", "records": [
                {"event": "observation", "sequence": 1, "capture_ns": 12, "image": str(png)},
                {"event": "observation", "sequence": 2, "capture_ns": 13, "image": str(root / "missing.png") }]}))
            row = review(report, root)
            self.assertEqual(row["image_status"], "needs_review")
            self.assertIsNone(row["image"])


if __name__ == "__main__":
    unittest.main()
