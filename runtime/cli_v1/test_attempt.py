import json
import io
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from runtime.cli_v1.attempt import invoke, _write_json, inspect_attempt
from runtime.cli_v1.__main__ import main
from runtime.cli_v1.__main__ import _present_result


class RetainedAttemptTests(unittest.TestCase):
    def test_flush_failure_surfaces_after_report_retention_without_retry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'attempt'
            report = {'status': 'returned', 'result': {'status': 'completed'}}
            backend = Mock(return_value=report)
            retained_report, retention = invoke(backend, {}, root, operation='dispatch')
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            writer = Mock()
            writer.write.side_effect = lambda value: len(value)
            writer.flush.side_effect = BrokenPipeError('buffered delivery failed')
            with patch.object(sys, 'stdout', writer):
                with self.assertRaisesRegex(BrokenPipeError, 'buffered delivery failed'):
                    _present_result(retained_report, with_review=False, capture_directory=None,
                                    exit_code=0, retention=retention)
            backend.assert_called_once()
            writer.write.assert_called_once()
            writer.flush.assert_called_once()
            self.assertEqual(inspect_attempt(root)['files']['report.json']['value'], report)
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    def test_short_write_is_detected_and_read_only_recovery_preserves_report(self):
        class ShortWriter(io.StringIO):
            def write(self, text):
                return super().write(text[:17])
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / 'attempt'
            (root / 'program.json').write_text('{}')
            (root / 'targets.json').write_text('{}')
            report = {'status': 'returned', 'result': {'status': 'completed'}}
            args = ['agent-interface', 'dispatch', '--program', str(root / 'program.json'),
                    '--targets', str(root / 'targets.json'), '--current-observation-seq', '1',
                    '--current-binding-revision', '0', '--run-directory', str(run)]
            delivered = ShortWriter()
            with patch.object(sys, 'argv', args), patch.object(sys, 'stdout', delivered), \
                 patch('runtime.cli_v1.__main__.dispatch', return_value=report) as call:
                with self.assertRaisesRegex(OSError, 'INCOMPLETE_STDOUT_WRITE'):
                    main()
            call.assert_called_once()
            with self.assertRaises(json.JSONDecodeError):
                json.loads(delivered.getvalue())
            before = {p.name: p.read_bytes() for p in run.iterdir()}
            recovered = subprocess.run([sys.executable, '-m', 'runtime.cli_v1',
                                        'attempt-status', '--run-directory', str(run)],
                                       cwd=Path(__file__).resolve().parents[2],
                                       capture_output=True, check=True, timeout=15)
            row = json.loads(recovered.stdout)
            self.assertEqual(row['files']['report.json']['value'], report)
            self.assertFalse(row['replay_allowed'])
            self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})

    def test_abrupt_exit_retains_unknown_attempt_without_replay(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'run'
            script = ('import os, sys; from runtime.cli_v1.attempt import invoke; '
                      'invoke(lambda **kw: os._exit(23), {}, sys.argv[1], operation="dispatch")')
            child = subprocess.run([sys.executable, '-c', script, str(root)],
                                   cwd=Path(__file__).resolve().parents[2], timeout=15)
            self.assertEqual(child.returncode, 23)
            before = (root / 'request.json').read_bytes()
            with patch('runtime.cli_v1.__main__.dispatch') as dispatch, \
                 patch('runtime.cli_v1.__main__.observe') as observe, \
                 patch.object(sys, 'argv', ['agent-interface', 'attempt-status', '--run-directory', str(root)]), \
                 patch('runtime.cli_v1.__main__._emit') as emit:
                self.assertEqual(main(), 2)
            dispatch.assert_not_called()
            observe.assert_not_called()
            row = emit.call_args.args[0]
            self.assertEqual(row['status'], 'unknown_or_incomplete')
            self.assertEqual(row['process_state'], 'unknown')
            self.assertFalse(row['replay_allowed'])
            self.assertEqual(row['files']['report.json']['state'], 'missing')
            self.assertEqual((root / 'request.json').read_bytes(), before)
            retry = Mock()
            invoke(retry, {}, root, operation='dispatch')
            retry.assert_not_called()

    def test_failed_report_replace_surfaces_residue_without_modifying_it(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'run'
            original_replace = os.replace
            def replace(source, destination):
                if destination.name == 'report.json':
                    raise OSError('injected replace failure')
                return original_replace(source, destination)
            call = Mock(return_value={'status': 'runtime_failed', 'effect_status': 'unknown'})
            with patch('runtime.cli_v1.attempt.os.replace', side_effect=replace):
                _, retention = invoke(call, {}, root, operation='dispatch')
            call.assert_called_once()
            self.assertFalse(retention['report_persisted'])
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            row = inspect_attempt(root)
            self.assertEqual(row['status'], 'unknown_or_incomplete')
            self.assertEqual(row['temporary_files'], ['.report.json.tmp'])
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    def test_recorded_failure_is_not_claimed_as_task_completion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'run'
            report = {'status': 'runtime_failed', 'effect_status': 'unknown'}
            invoke(Mock(return_value=report), {}, root, operation='dispatch')
            row = inspect_attempt(root)
            self.assertEqual(row['status'], 'report_recorded')
            self.assertEqual(row['files']['report.json']['value'], report)
            self.assertFalse(row['replay_allowed'])
            (root / 'report.json').write_text('{')
            self.assertEqual(inspect_attempt(root)['status'], 'invalid_record')
            self.assertEqual(inspect_attempt(root / 'missing')['status'], 'invalid_record')

    @unittest.skipUnless(sys.platform == 'linux', 'Linux pipe transport control')
    def test_portable_report_survives_actual_closed_stdout_pipe(self):
        from runtime.distribution_v2.build import SOURCE_FILES, build
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repository = Path(__file__).resolve().parents[2]
            source = root / 'source'
            for name in SOURCE_FILES:
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((repository / name).read_bytes())
            archive = root / 'runtime.pyz'
            build(source, archive, root / 'manifest.json', root / 'sha256.txt')
            (root / 'program.json').write_text('{}')
            (root / 'targets.json').write_text('{"fixture":123}')
            run = root / 'attempt'
            command = [sys.executable, str(archive), 'dispatch',
                       '--program', str(root / 'program.json'), '--targets', str(root / 'targets.json'),
                       '--current-observation-seq', '-1', '--current-binding-revision', '0',
                       '--run-directory', str(run), '--review']
            with (root / 'stderr.txt').open('wb') as errors:
                reader, writer = os.pipe()
                os.close(reader)  # No reader exists even if the child runs immediately.
                try:
                    process = subprocess.Popen(command, cwd=root, stdout=writer, stderr=errors)
                finally:
                    os.close(writer)
                try:
                    code = process.wait(timeout=15)
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait(timeout=5)
            self.assertNotEqual(code, 0)
            self.assertIn('BrokenPipeError', (root / 'stderr.txt').read_text())
            original = (run / 'report.json').read_bytes()
            request = (run / 'request.json').read_bytes()
            self.assertEqual(json.loads(original)['error'], 'INVALID_OBSERVATION_SEQ')
            recovered = subprocess.run([sys.executable, str(archive), 'review', '--report',
                                        str(run / 'report.json'), '--run-directory', str(run)],
                                       cwd=root, capture_output=True, check=True, timeout=15)
            self.assertEqual(json.loads(recovered.stdout)['outcome_summary']['error'],
                             'INVALID_OBSERVATION_SEQ')
            self.assertEqual((run / 'report.json').read_bytes(), original)
            self.assertEqual((run / 'request.json').read_bytes(), request)
            inspected = subprocess.run([sys.executable, str(archive), 'attempt-status',
                                        '--run-directory', str(run)], cwd=root,
                                       capture_output=True, check=True, timeout=15)
            self.assertEqual(json.loads(inspected.stdout)['status'], 'report_recorded')
            self.assertEqual((run / 'report.json').read_bytes(), original)

    def test_setup_failure_never_calls_api_or_overwrites_existing_run(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'run'; root.mkdir()
            (root / 'request.json').write_text('original')
            call = Mock()
            result, retained = invoke(call, {}, root, operation='dispatch')
            call.assert_not_called()
            self.assertFalse(result['operation_invoked'])
            self.assertFalse(retained['request_persisted'])
            self.assertEqual((root / 'request.json').read_text(), 'original')
            with patch('runtime.cli_v1.attempt._write_json', side_effect=OSError('disk full')):
                result, _ = invoke(call, {}, Path(td) / 'new', operation='dispatch')
            call.assert_not_called()
            self.assertEqual(result['error'], 'REQUEST_PERSISTENCE_FAILED')

    def test_request_precedes_api_and_report_precedes_broken_stdout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); run = root / 'run'
            (root / 'program.json').write_text('{}')
            (root / 'targets.json').write_text('{"fixture":123}')
            report = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                      'status': 'runtime_failed', 'error': 'partial input',
                      'result': {'recovery_required': True}}
            def backend(**kwargs):
                request = json.loads((run / 'request.json').read_text())
                self.assertEqual(request['arguments'], kwargs)
                self.assertFalse((run / 'report.json').exists())
                return report
            args = ['agent-interface', 'dispatch', '--program', str(root / 'program.json'),
                    '--targets', str(root / 'targets.json'), '--current-observation-seq', '1',
                    '--current-binding-revision', '0', '--run-directory', str(run), '--review']
            with patch.object(sys, 'argv', args), patch('runtime.cli_v1.__main__.dispatch', side_effect=backend) as call, \
                 patch('runtime.cli_v1.__main__._emit', side_effect=BrokenPipeError):
                with self.assertRaises(BrokenPipeError):
                    main()
            call.assert_called_once()
            self.assertEqual(json.loads((run / 'report.json').read_text()), report)

    def test_report_write_failure_preserves_outcome_and_unknown_exception(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'run'
            def write(path, value):
                if path.name == 'report.json':
                    raise OSError('disk full after call')
                _write_json(path, value)
            call = Mock(side_effect=RuntimeError('unknown partial effect'))
            with patch('runtime.cli_v1.attempt._write_json', side_effect=write):
                report, retained = invoke(call, {}, root, operation='dispatch')
            call.assert_called_once()
            self.assertTrue(retained['request_persisted'])
            self.assertFalse(retained['report_persisted'])
            self.assertIn('disk full', retained['persistence_error'])
            self.assertEqual(report['effect_status'], 'unknown')
            self.assertTrue(report['operation_invoked'])
            self.assertFalse((root / 'report.json').exists())

    def test_missing_persistence_is_nonzero_even_for_completed_action(self):
        report = {'status': 'returned', 'result': {'status': 'completed'}}
        retained = {'report_persisted': False, 'persistence_error': 'disk full'}
        with patch('runtime.cli_v1.__main__._emit') as emit:
            code = _present_result(report, with_review=False, capture_directory=None,
                                   exit_code=0, retention=retained)
        self.assertEqual(code, 2)
        self.assertEqual(emit.call_args.args[0]['result']['status'], 'completed')
        self.assertNotIn('retention', report)

    def test_partial_report_temp_write_failure_is_visible_and_read_only(self):
        class PartialWriteFailure:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return self.stream.__exit__(exc_type, exc, traceback)

            def write(self, data):
                self.stream.write(data[:max(1, len(data) // 2)])
                self.stream.flush()
                raise OSError('injected partial report write')

            def __getattr__(self, name):
                return getattr(self.stream, name)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'run'
            original_open = Path.open

            def open_with_partial_failure(path, mode='r', *args, **kwargs):
                stream = original_open(path, mode, *args, **kwargs)
                if path.name == '.report.json.tmp' and 'x' in mode:
                    return PartialWriteFailure(stream)
                return stream

            call = Mock(return_value={'status': 'returned', 'result': {'status': 'completed'}})
            with patch.object(Path, 'open', autospec=True, side_effect=open_with_partial_failure):
                report, retention = invoke(call, {}, root, operation='dispatch')

            call.assert_called_once()
            self.assertTrue(retention['request_persisted'])
            self.assertFalse(retention['report_persisted'])
            self.assertIn('injected partial report write', retention['persistence_error'])
            self.assertFalse((root / 'report.json').exists())
            temp = root / '.report.json.tmp'
            residue = temp.read_bytes()
            self.assertGreater(len(residue), 0)
            self.assertLess(len(residue), len(json.dumps(report, allow_nan=False).encode('utf-8')))
            first = inspect_attempt(root)
            self.assertEqual(first['status'], 'unknown_or_incomplete')
            self.assertFalse(first['replay_allowed'])
            self.assertEqual(first['temporary_files'], ['.report.json.tmp'])
            self.assertEqual(temp.read_bytes(), residue)
            self.assertEqual(inspect_attempt(root), first)
            self.assertEqual(temp.read_bytes(), residue)
            call.assert_called_once()

    def test_report_fsync_failure_is_visible_and_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'run'
            original_fsync = os.fsync
            count = 0

            def fail_report_fsync(fd):
                nonlocal count
                count += 1
                if count == 2:
                    raise OSError('injected report fsync failure')
                return original_fsync(fd)

            call = Mock(return_value={'status': 'returned', 'result': {'status': 'completed'}})
            with patch('runtime.cli_v1.attempt.os.fsync', side_effect=fail_report_fsync):
                report, retention = invoke(call, {}, root, operation='dispatch')

            call.assert_called_once()
            self.assertEqual(count, 2)
            self.assertTrue(retention['request_persisted'])
            self.assertFalse(retention['report_persisted'])
            self.assertIn('injected report fsync failure', retention['persistence_error'])
            self.assertFalse((root / 'report.json').exists())
            temp = root / '.report.json.tmp'
            residue = temp.read_bytes()
            self.assertEqual(json.loads(residue), report)
            first = inspect_attempt(root)
            self.assertEqual(first['status'], 'unknown_or_incomplete')
            self.assertFalse(first['replay_allowed'])
            self.assertEqual(first['temporary_files'], ['.report.json.tmp'])
            self.assertEqual(temp.read_bytes(), residue)
            self.assertEqual(inspect_attempt(root), first)
            self.assertEqual(temp.read_bytes(), residue)
            call.assert_called_once()

    def test_successful_report_publication_leaves_no_temp_residue(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'run'
            report = {'status': 'returned', 'result': {'status': 'completed'}}
            call = Mock(return_value=report)
            _, retention = invoke(call, {}, root, operation='dispatch')
            call.assert_called_once()
            self.assertTrue(retention['request_persisted'])
            self.assertTrue(retention['report_persisted'])
            inspected = inspect_attempt(root)
            self.assertEqual(inspected['status'], 'report_recorded')
            self.assertFalse(inspected['replay_allowed'])
            self.assertEqual(inspected['temporary_files'], [])

