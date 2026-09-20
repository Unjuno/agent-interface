import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from runtime.cli_v1.attempt import invoke, _write_json
from runtime.cli_v1.__main__ import main
from runtime.cli_v1.__main__ import _present_result


class RetainedAttemptTests(unittest.TestCase):
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
            with (patch.object(sys, 'argv', args),
                  patch('runtime.cli_v1.__main__.dispatch', side_effect=backend) as call,
                  patch('runtime.cli_v1.__main__._emit', side_effect=BrokenPipeError)):
                with self.assertRaises(BrokenPipeError):
                    main()
            call.assert_called_once()
            self.assertEqual(json.loads((run / 'report.json').read_text()), report)

    def test_short_stdout_write_keeps_exact_report_and_never_reinvokes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'program.json').write_text('{}')
            (root / 'targets.json').write_text('{"fixture":123}')
            run = root / 'attempt'
            report = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                      'status': 'returned', 'result': {'status': 'completed'}}

            class ShortWriter:
                def __init__(self):
                    self.accepted = ''
                    self.attempted = 0
                def write(self, text):
                    self.attempted = len(text)
                    self.accepted += text[:max(1, len(text) // 2)]
                    return len(self.accepted)

            output = ShortWriter()
            args = ['agent-interface', 'dispatch', '--program', str(root / 'program.json'),
                    '--targets', str(root / 'targets.json'), '--current-observation-seq', '1',
                    '--current-binding-revision', '0', '--run-directory', str(run)]
            with (patch.object(sys, 'argv', args),
                  patch('runtime.cli_v1.__main__.dispatch', return_value=report) as call,
                  patch('runtime.cli_v1.__main__.sys.stdout', output)):
                with self.assertRaisesRegex(BrokenPipeError, 'SHORT_STDOUT_WRITE'):
                    main()

            call.assert_called_once()
            self.assertTrue(output.accepted)
            self.assertLess(len(output.accepted), output.attempted)
            self.assertEqual(json.loads((run / 'report.json').read_bytes()), report)
            self.assertTrue((run / 'request.json').is_file())

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
