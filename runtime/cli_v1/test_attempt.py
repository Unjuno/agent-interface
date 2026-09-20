import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from runtime.cli_v1.attempt import invoke, _write_json
from runtime.cli_v1.__main__ import main
from runtime.cli_v1.__main__ import _present_result


class RetainedAttemptTests(unittest.TestCase):
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
