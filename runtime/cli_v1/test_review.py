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

    def test_release_summary_requires_all_records_and_preserves_unknown(self):
        from runtime.cli_v1.review import outcome_summary
        good = {'verified': True, 'keys_down': [], 'buttons_down': []}
        cases = [(None, None), ([], None), ([good], True),
                 ([good, {'verified': False}], False),
                 ([{'verified': False}, good], False),
                 ([good, {}], None), ([dict(good, verified=1)], None),
                 ([dict(good, keys_down=['CTRL'])], None), ([False], None)]
        for releases, expected in cases:
            with self.subTest(releases=releases):
                report = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                          'result': {'status': 'completed', 'recovery_required': True,
                                     'execution': {'releases': releases}}}
                summary = outcome_summary(report)
                self.assertIs(summary['input_release_verified'], expected)
                self.assertIs(summary['recovery_required'], True)
                self.assertEqual(summary['execution_status'], 'completed')


    def test_compact_review_chooses_smaller_lossless_receipt(self):
        from runtime.cli_v1.receipt_references import expand_receipt
        with tempfile.TemporaryDirectory() as td:
            event = {'event': 'independent_evaluation', 'success': False, 'reason': 'x' * 2000}
            for report, schema in (({'status': 'failed'}, 'agent-interface/receipt-view-v1'),
                    ({'status': 'failed', 'records': [event], 'outcome': event},
                     'agent-interface/receipt-view-v2-event-refs')):
                raw = json.dumps(report).encode()
                full = review_bytes(raw, td)
                compact = review_bytes(raw, td, compact=True)
                self.assertEqual(compact['receipt']['schema'], schema)
                self.assertEqual(expand_receipt(compact['receipt']), full['receipt'])
                self.assertLessEqual(len(json.dumps(compact, sort_keys=True, separators=(',', ':'))),
                                     len(json.dumps(full, sort_keys=True, separators=(',', ':'))))

    def test_live_compact_review_preserves_failure_and_calls_backend_once(self):
        from unittest.mock import patch
        from runtime.cli_v1 import __main__ as cli
        with tempfile.TemporaryDirectory() as td:
            payload = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                       'status': 'returned', 'result': {'status': 'execution_failed',
                       'recovery_required': True, 'execution': {'completed_ops': [0]}}}
            cases = [('dispatch', ['--program', 'p', '--targets', 't',
                      '--current-observation-seq', '1', '--current-binding-revision', '0'], payload, 3),
                     ('observe', ['--targets', 't', '--target', 'app', '--frame', 'window_client',
                      '--region', '0', '0', '10', '10'], {'status': 'capture_failed'}, 2)]
            for command, arguments, result, code in cases:
                argv = ['agent-interface', command, *arguments, '--review', '--compact', '--capture-directory', td]
                with patch.object(sys, 'argv', argv), patch.object(cli, '_read_json', return_value={}), \
                     patch.object(cli, command, return_value=result) as backend, patch.object(cli, '_emit') as emit:
                    self.assertEqual(cli.main(), code)
                    backend.assert_called_once()
                    returned = emit.call_args.args[0]
                    self.assertEqual(returned['receipt']['source']['raw_report'], result)
                    self.assertEqual(returned['outcome_summary']['reported_status'], result['status'])
                with patch.object(sys, 'argv', ['agent-interface', command, *arguments, '--compact']), \
                     patch.object(cli, command) as backend, patch.object(cli, '_read_json') as read, \
                     patch('sys.stderr'):
                    with self.assertRaises(SystemExit) as error:
                        cli.main()
                    self.assertEqual(error.exception.code, 2)
                    backend.assert_not_called()
                    read.assert_not_called()

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
            from runtime.cli_v1.receipt_references import expand_receipt
            for compact_command, input_bytes, expected in (
                    (command + ['--compact'], None, row),
                    ([sys.executable, str(archive), 'review', '--report', '-',
                      '--run-directory', str(root), '--compact'], original, piped_row)):
                compact_run = subprocess.run(compact_command, input=input_bytes,
                                             cwd=root, capture_output=True)
                self.assertEqual(compact_run.returncode, 0, compact_run.stderr)
                compact = json.loads(compact_run.stdout)
                self.assertEqual(expand_receipt(compact['receipt']), expected['receipt'])
                self.assertEqual(compact['image'], expected['image'])
                self.assertEqual(compact['outcome_summary'], expected['outcome_summary'])
            png.unlink()
            missing = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            row = json.loads(missing.stdout)
            self.assertEqual(row["image_status"], "needs_review")
            self.assertEqual(row["receipt"]["report"]["error"], "timeout")
            self.assertEqual(report.read_bytes(), original)
            compact_missing = subprocess.run(command + ['--compact'], cwd=root, capture_output=True)
            self.assertEqual(compact_missing.returncode, 2)
            compact_row = json.loads(compact_missing.stdout)
            self.assertEqual(expand_receipt(compact_row['receipt']), row['receipt'])
            self.assertIsNone(compact_row['image'])

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

    def test_partial_failure_summary_preserves_uncertainty_without_retry_advice(self):
        with tempfile.TemporaryDirectory() as td:
            payload = {'schema': 'agent-interface/runtime-dispatch-result-v1', 'status': 'runtime_failed',
                       'cleanup_error': 'close failed', 'result': {'status': 'execution_failed',
                       'error': 'BACKEND_EXECUTION_FAILED', 'execution': {'error': 'after partial emission',
                       'failed_op': 3, 'failed_op_effect': 'unknown; may have emitted partial input',
                       'completed_ops': [0, 1, 2]}}}
            for value, expected in ((3, 3), (False, None), (-1, None), ('3', None), (None, None)):
                payload['result']['execution']['failed_op'] = value
                row = review_bytes(json.dumps(payload).encode(), td)
                summary = row['outcome_summary']
                self.assertEqual(summary['failure_detail'], 'after partial emission')
                self.assertEqual(summary['failed_operation_index'], expected)
                self.assertEqual(summary['failed_operation_effect'], 'unknown; may have emitted partial input')
                self.assertEqual(summary['cleanup_error'], 'close failed')
                self.assertNotIn('retry', summary)
                self.assertIsNone(summary['recovery_required'])
                self.assertEqual(row['receipt']['source']['raw_report'], payload)

    def test_repeat_failure_maps_to_original_instruction_without_replay(self):
        from copy import deepcopy
        from runtime.cli_v1.review import outcome_summary
        payload = {'schema': 'agent-interface/runtime-dispatch-result-v1', 'status': 'returned',
                   'result': {'status': 'execution_failed', 'execution': {
                       'failed_op': 2, 'failed_op_effect': 'unknown'}},
                   'compilation': {'kind': 'bounded_key_repeat', 'source_program': {'ops': [
                       {'op': 'focus', 'target': 'fixture'},
                       {'op': 'key_chord', 'keys': ['Left'], 'repeat': 3},
                       {'op': 'release_all'}]}, 'operation_sources': [0, 1, 1, 1, 2]}}
        original = deepcopy(payload)
        summary = outcome_summary(payload)
        self.assertEqual(summary['failed_source_operation'], {
            'source_operation_index': 1, 'occurrence': 2, 'occurrence_count': 3})
        self.assertEqual(summary['failed_operation_index'], 2)
        self.assertEqual(summary['failed_operation_effect'], 'unknown')
        self.assertEqual(payload, original)
        for failed in (None, False, -1, 5, '2'):
            changed = deepcopy(payload)
            changed['result']['execution']['failed_op'] = failed
            self.assertIsNone(outcome_summary(changed)['failed_source_operation'])
        for mapping in ([0, 1, 2, 1, 2], [False, 1, 1, 1, 2], [0], None):
            changed = deepcopy(payload)
            changed['compilation']['operation_sources'] = mapping
            self.assertIsNone(outcome_summary(changed)['failed_source_operation'])
        changed = deepcopy(payload)
        changed['compilation']['source_program']['ops'][1]['repeat'] = 10**10
        self.assertIsNone(outcome_summary(changed)['failed_source_operation'])

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
