from __future__ import annotations

import json
import io
import hashlib
import base64
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cli_v1.api import dispatch, doctor


class FakeSession:
    def __init__(self):
        self.calls = []
    def dispatch(self, program, *, current_observation_seq, current_binding_revision):
        self.calls.append((program, current_observation_seq, current_binding_revision))
        return {"status": "completed", "echo_program": program}


class ApiTests(unittest.TestCase):

    def test_explicit_text_gap_compiles_before_backend_and_maps_character_failure(self):
        from runtime.cli_v1.review import outcome_summary
        session = FakeSession()
        source = {'ops': [{'op':'text','text':'300','gap_ms':20},
                          {'op':'key_chord','keys':['Left'],'repeat':2}, {'op':'release_all'}]}
        with mock.patch('runtime.cli_v1.api.open_session', return_value=session):
            row = dispatch(source, {'app':1}, current_observation_seq=1, current_binding_revision=0)
        ops = session.calls[0][0]['ops']
        self.assertEqual(ops[:5], [{'op':'text','text':'3'}, {'op':'wait_update','timeout_ms':20},
            {'op':'text','text':'0'}, {'op':'wait_update','timeout_ms':20}, {'op':'text','text':'0'}])
        self.assertEqual(len(ops), 8)
        self.assertEqual(source['ops'][0]['text'], '300')
        row['result'] = {'status':'execution_failed','execution':{'failed_op':4}}
        self.assertEqual(outcome_summary(row)['failed_source_operation'],
            {'source_operation_index':0,'character_index':2,'phase':'text'})
        row['result']['execution']['failed_op'] = 3
        self.assertEqual(outcome_summary(row)['failed_source_operation']['phase'], 'gap_before_character')
        row['compilation']['operation_sources'][0]['source_operation_index'] = False
        self.assertIsNone(outcome_summary(row)['failed_source_operation'])

    def test_text_gap_invalid_or_oversized_never_opens_backend(self):
        for op in ({'op':'text','text':'abc','gap_ms':True},
                   {'op':'text','text':'abc','gap_ms':-1},
                   {'op':'text','text':'abc','gap_ms':1001},
                   {'op':'text','text':'x'*65,'gap_ms':20},
                   {'op':'key_chord','keys':['Left'],'gap_ms':20},
                   {'op':'text','text':'abc','gap_ms':20,'repeat':2}):
            with self.subTest(op=op), mock.patch('runtime.cli_v1.api.open_session') as opened:
                result = dispatch({'ops':[op]}, {'app':1}, current_observation_seq=1, current_binding_revision=0)
                self.assertEqual(result['error'], 'INVALID_TEXT_GAP')
                opened.assert_not_called()

    def test_text_gap_zero_empty_and_capacity_are_bounded(self):
        from runtime.core_v1.sequence import expand_text_gaps
        for text in ('', 'abc'):
            ops, _ = expand_text_gaps([{'op':'text','text':text,'gap_ms':0}])
            self.assertEqual(ops, [{'op':'text','text':text}])
        ops, _ = expand_text_gaps([{'op':'text','text':'x'*64,'gap_ms':20},{'op':'release_all'}])
        self.assertEqual(len(ops),128)
        with self.assertRaises(ValueError):
            expand_text_gaps([{'op':'focus','target':'app'},{'op':'text','text':'x'*64,'gap_ms':20},{'op':'release_all'}])


    def test_dependency_inventory_distinguishes_missing_unknown_and_metadata(self):
        from importlib.metadata import PackageNotFoundError
        with mock.patch('importlib.util.find_spec', side_effect=[None, object(), ValueError('finder failed')]), mock.patch(
                'importlib.metadata.version', side_effect=[PackageNotFoundError('python-xlib'), '10.2.0', OSError('metadata failed')]), mock.patch(
                'runtime.cli_v1.api.open_session') as opened:
            row = doctor(platform='linux', environ={'DISPLAY': ':99'}, check_dependencies=True)
        opened.assert_not_called()
        inventory = row['dependency_inventory']
        self.assertEqual(inventory['scope'], 'current_python_environment')
        xlib, pillow, mcp = inventory['modules']
        self.assertIs(xlib['discoverable'], False)
        self.assertIsNone(xlib['installed_version'])
        self.assertIs(pillow['discoverable'], True)
        self.assertEqual(pillow['installed_version'], '10.2.0')
        self.assertIsNone(mcp['discoverable'])
        self.assertIn('finder failed', mcp['discovery_error'])
        self.assertIn('metadata failed', mcp['version_error'])
        self.assertTrue(row['runtime_available'])  # Existing field is selection, not readiness.
        self.assertFalse(row['side_effect_authority'])

    def test_default_doctor_does_not_inspect_optional_dependencies(self):
        with mock.patch('importlib.util.find_spec') as discover:
            row = doctor(platform='win32', environ={})
        discover.assert_not_called()
        self.assertNotIn('dependency_inventory', row)

    def test_initialization_error_returns_receipt_and_preserves_repeat_source(self):
        request = {'ops': [{'op': 'key_chord', 'keys': ['Left'], 'repeat': 3}]}
        for error in (OSError('connection refused'), OverflowError('invalid display'), RuntimeError('setup')):
            with self.subTest(error=error), mock.patch(
                    'runtime.cli_v1.api.open_session', side_effect=error) as opened:
                row = dispatch(request, {'fixture': 123},
                               current_observation_seq=1, current_binding_revision=0)
                opened.assert_called_once()
                self.assertEqual(row['status'], 'runtime_failed')
                self.assertEqual(row['failure_phase'], 'backend_initialization')
                self.assertEqual(row['error'], repr(error))
                self.assertEqual(row['compilation']['source_program'], request)
                self.assertEqual(row['compilation']['operation_sources'], [0, 0, 0])
                self.assertNotIn('result', row)
                self.assertNotIn('cleanup_verified', row)

    def test_key_repeat_expands_once_and_retains_source_mapping_on_failure(self):
        from copy import deepcopy
        from runtime.core_v1.test_contract import program as fixture_program
        from runtime.core_v1.contract import validate_program
        request = fixture_program()
        request['ops'] = [{'op': 'focus', 'target': 'fixture'},
                          {'op': 'key_chord', 'keys': ['Right'], 'repeat': 3},
                          {'op': 'wait_update', 'timeout_ms': 0}, {'op': 'release_all'}]
        original = deepcopy(request)
        session = mock.Mock()
        session.dispatch.return_value = {'status': 'execution_failed', 'execution': {'failed_op': 2}}
        with mock.patch('runtime.cli_v1.api.open_session', return_value=session):
            row = dispatch(request, {'fixture': 1}, current_observation_seq=7, current_binding_revision=3)
        session.dispatch.assert_called_once()
        expanded = session.dispatch.call_args.args[0]
        validate_program(expanded)
        self.assertEqual(expanded['ops'], [request['ops'][0]] +
                         [{'op': 'key_chord', 'keys': ['Right']} for _ in range(3)] + request['ops'][2:])
        self.assertEqual(expanded['source'], request['source'])
        self.assertEqual(expanded['authority'], request['authority'])
        self.assertEqual(row['compilation']['source_program'], original)
        self.assertEqual(row['compilation']['operation_sources'], [0, 1, 1, 1, 2, 3])
        self.assertEqual(row['result']['execution']['failed_op'], 2)
        expanded['ops'][1]['keys'][0] = 'Left'
        self.assertEqual(expanded['ops'][2]['keys'], ['Right'])
        self.assertEqual(request, original)
        session.backend.close.assert_called_once()

    def test_invalid_repeat_and_expanded_capacity_refuse_before_backend(self):
        bad = [[{'op': 'key_chord', 'keys': ['Right'], 'repeat': value}]
               for value in (True, False, 0, -1, 1.5, '3', None, 127, 10**100)]
        bad += [[{'op': kind, 'repeat': 2}] for kind in ('text', 'wait_update', 'pointer_button', 'release_all')]
        full = [{'op': 'focus', 'target': 'fixture'},
                {'op': 'key_chord', 'keys': ['Right'], 'repeat': 126}, {'op': 'release_all'}]
        bad.append(full[:-1] + [{'op': 'wait_update', 'timeout_ms': 0}] + full[-1:])
        with mock.patch('runtime.cli_v1.api.open_session') as open_backend:
            for ops in bad:
                row = dispatch({'ops': ops}, {'fixture': 1}, current_observation_seq=7, current_binding_revision=3)
                self.assertEqual(row['error'], 'INVALID_KEY_REPEAT')
            open_backend.assert_not_called()
        session = FakeSession()
        with mock.patch('runtime.cli_v1.api.open_session', return_value=session):
            dispatch({'ops': full}, {'fixture': 1}, current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(len(session.calls[0][0]['ops']), 128)

    def test_capture_configuration_failure_closes_without_dispatch(self):
        session = mock.Mock()
        session.backend.configure_capture_artifacts.side_effect = OSError("not writable")
        with mock.patch("runtime.cli_v1.api.open_session", return_value=session):
            row = dispatch({}, {"fixture": 1}, current_observation_seq=1,
                           current_binding_revision=1, capture_directory="artifacts")
        session.dispatch.assert_not_called()
        session.backend.close.assert_called_once_with()
        self.assertEqual(row["status"], "runtime_failed")

    def test_owned_backend_closed_on_completion_refusal_and_exception(self):
        for outcome in ({"status": "completed"}, {"status": "refused"}, RuntimeError("dispatch failed")):
            session = mock.Mock()
            if isinstance(outcome, Exception):
                session.dispatch.side_effect = outcome
            else:
                session.dispatch.return_value = outcome
            with self.subTest(outcome=outcome), mock.patch("runtime.cli_v1.api.open_session", return_value=session):
                row = dispatch({}, {"fixture": 1}, current_observation_seq=0, current_binding_revision=0)
                session.backend.close.assert_called_once_with()
                self.assertEqual(row["status"], "runtime_failed" if isinstance(outcome, Exception) else "returned")

    def test_close_failure_retains_completed_result_without_reporting_success(self):
        session = mock.Mock()
        session.dispatch.return_value = {"status": "completed", "execution": {"emissions": 2}}
        session.backend.close.side_effect = RuntimeError("close failed")
        with mock.patch("runtime.cli_v1.api.open_session", return_value=session):
            row = dispatch({}, {"fixture": 1}, current_observation_seq=0, current_binding_revision=0)
        self.assertEqual(row["status"], "runtime_failed")
        self.assertEqual(row["error"], "BACKEND_CLOSE_FAILED")
        self.assertEqual(row["result"], session.dispatch.return_value)
        self.assertIn("close failed", row["cleanup_error"])

    def test_close_failure_preserves_original_execution_error(self):
        session = mock.Mock()
        session.dispatch.side_effect = RuntimeError("dispatch failed")
        session.backend.close.side_effect = RuntimeError("close failed")
        with mock.patch("runtime.cli_v1.api.open_session", return_value=session):
            row = dispatch({}, {"fixture": 1}, current_observation_seq=0, current_binding_revision=0)
        self.assertIn("dispatch failed", row["error"])
        self.assertIn("close failed", row["cleanup_error"])

    def test_doctor_is_side_effect_free(self):
        row = doctor(platform="win32", environ={})
        self.assertEqual(row["selection"]["backend_id"], "win32-v1")
        self.assertFalse(row["side_effect_authority"])

    def test_dispatch_preserves_program_and_freshness_inputs(self):
        session = FakeSession()
        program = {"schema": "agent-interface/program-v1", "source": {"observation_seq": 7, "binding_revision": 3}}
        with mock.patch("runtime.cli_v1.api.open_session", return_value=session):
            row = dispatch(program, {"fixture": 1}, current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "returned")
        self.assertIs(session.calls[0][0], program)
        self.assertEqual(session.calls[0][1:], (7, 3))

    def test_invalid_targets_fail_before_backend_construction(self):
        row = dispatch({}, {}, current_observation_seq=0, current_binding_revision=0)
        self.assertEqual(row["status"], "backend_unavailable")

    def test_invalid_sequence_and_revision_fail_closed(self):
        row = dispatch({}, {"x": 1}, current_observation_seq=-1, current_binding_revision=0)
        self.assertEqual(row["error"], "INVALID_OBSERVATION_SEQ")
        row = dispatch({}, {"x": 1}, current_observation_seq=0, current_binding_revision=-1)
        self.assertEqual(row["error"], "INVALID_BINDING_REVISION")


class CliTests(unittest.TestCase):
    def test_inline_review_preserves_refusal_exit_and_dispatches_once(self):
        from runtime.cli_v1.__main__ import main
        with tempfile.TemporaryDirectory() as td:
            args = ['agent-interface', 'dispatch', '--program', 'program.json', '--targets', 'targets.json',
                    '--current-observation-seq', '0', '--current-binding-revision', '0',
                    '--capture-directory', td, '--review']
            raw = {'schema': 'agent-interface/runtime-dispatch-result-v1', 'status': 'returned',
                   'result': {'status': 'refused', 'error': 'BACKEND_CONSTRAINT', 'detail': 'unmapped key RIGHT'}}
            with mock.patch.object(sys, 'argv', args), mock.patch('runtime.cli_v1.__main__._read_json', return_value={}), \
                 mock.patch('runtime.cli_v1.__main__.dispatch', return_value=raw) as dispatch_call, \
                 mock.patch.object(sys, 'stdout', new_callable=io.StringIO) as output:
                code = main()
            self.assertEqual(code, 3)
            dispatch_call.assert_called_once()
            row = json.loads(output.getvalue())
            self.assertEqual(row['outcome_summary']['execution_status'], 'refused')
            self.assertEqual(row['receipt']['source']['raw_report'], raw)
            self.assertEqual(list(Path(td).iterdir()), [])

    def test_inline_presentation_failure_never_replays_or_loses_raw_result(self):
        from runtime.cli_v1.__main__ import _present_result
        raw = {'status': 'returned', 'result': {'status': 'completed'}}
        with mock.patch('runtime.cli_v1.review.review_bytes', side_effect=ValueError('bad image')), \
             mock.patch.object(sys, 'stdout', new_callable=io.StringIO) as output:
            self.assertEqual(_present_result(raw, with_review=True, capture_directory='.', exit_code=0), 2)
        row = json.loads(output.getvalue())
        self.assertEqual(row['raw_result'], raw)
        self.assertEqual(row['image_status'], 'needs_review')

    def test_inline_observe_returns_exact_captured_image(self):
        from runtime.cli_v1.__main__ import main
        with tempfile.TemporaryDirectory() as td:
            png = Path(td) / 'image.png'
            pixels = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII=')
            png.write_bytes(pixels)
            raw = {'schema': 'agent-interface/runtime-observation-v1', 'status': 'returned',
                   'observation_id': 'one', 'observation': {'sha256': 'raw', 'capture_started_ns': 12,
                   'artifact': {'path': str(png), 'mime_type': 'image/png',
                                'source_raw_sha256': 'raw', 'sha256': hashlib.sha256(pixels).hexdigest()}}}
            args = ['agent-interface', 'observe', '--targets', 'targets.json', '--target', 'fixture',
                    '--frame', 'window_client', '--region', '0', '0', '1', '1', '--capture-directory', td, '--review']
            with mock.patch.object(sys, 'argv', args), mock.patch('runtime.cli_v1.__main__._read_json', return_value={}), \
                 mock.patch('runtime.cli_v1.__main__.observe', return_value=raw) as observed, \
                 mock.patch.object(sys, 'stdout', new_callable=io.StringIO) as output:
                self.assertEqual(main(), 0)
            observed.assert_called_once()
            row = json.loads(output.getvalue())
            self.assertEqual(base64.b64decode(row['image']['data']), pixels)
            self.assertEqual(row['receipt']['source']['raw_report'], raw)

    def test_inline_review_requires_capture_directory_before_read_or_input(self):
        from runtime.cli_v1.__main__ import main
        args = ['agent-interface', 'observe', '--targets', 'missing', '--target', 'fixture',
                '--frame', 'window_client', '--region', '0', '0', '100', '100', '--review']
        with mock.patch.object(sys, 'argv', args), mock.patch('runtime.cli_v1.__main__.observe') as observed, \
             mock.patch.object(sys, 'stderr', new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as stopped:
                main()
            self.assertEqual(stopped.exception.code, 2)
            observed.assert_not_called()

    def test_doctor_outputs_one_json_record(self):
        proc = subprocess.run([sys.executable, "-m", "runtime.cli_v1", "doctor"], capture_output=True, text=True, check=True)
        rows = proc.stdout.strip().splitlines()
        self.assertEqual(len(rows), 1)
        data = json.loads(rows[0])
        self.assertEqual(data["schema"], "agent-interface/runtime-doctor-v1")
        self.assertFalse(data["side_effect_authority"])

    def test_malformed_json_is_nonzero_and_json_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bad = root / "bad.json"; bad.write_text("{bad", encoding="utf-8")
            targets = root / "targets.json"; targets.write_text('{"fixture":1}', encoding="utf-8")
            proc = subprocess.run([
                sys.executable, "-m", "runtime.cli_v1", "dispatch",
                "--program", str(bad), "--targets", str(targets),
                "--current-observation-seq", "0", "--current-binding-revision", "0",
            ], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(len(proc.stdout.strip().splitlines()), 1)
            self.assertEqual(json.loads(proc.stdout)["status"], "invalid_request")


if __name__ == "__main__":
    unittest.main()
