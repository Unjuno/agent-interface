"""Offline tests for parent-held two-save G10 artifact custody."""
import tempfile
import unittest
from pathlib import Path

from runtime.guarded_x11_v1.calc_g10_artifact_v1 import (
    CalcG10ArtifactCustody, PROFILE_ID,
)
from runtime.guarded_x11_v1.process_identity import process_generation_from_identity


CALL_ID = 'c' * 32
ATTEMPT_ID = 'g10-custody-test-01'
XID = 42
PID = 4321
START_TICKS = 98765
PROCESS_GENERATION = process_generation_from_identity(XID, PID, START_TICKS)
WINDOW_GENERATION = 'd' * 64
METHOD_FORMAT = 'compiled-gui-runtime-receipt-v1'
CLOSE = {'status': 'closed', 'verified': True,
         'owner_process_retired': True, 'release_confirmed': True}

FIXTURES = (Path(__file__).resolve().parents[2] / 'research' / 'integration'
            / 'calc_current_shared_3311_4d74_20261004'
            / 'calc-compiled-ocrlive-4d74' / 'runs' / 'compiled_ocrlive10')


class CalcG10ArtifactCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / CALL_ID
        self.root.mkdir()
        self.custody = CalcG10ArtifactCustody(
            self.root, call_id=CALL_ID, attempt_id=ATTEMPT_ID)
        self.custody.bind_target(process_generation=PROCESS_GENERATION,
            window_generation=WINDOW_GENERATION, target_xid=XID,
            target_pid=PID, target_start_ticks=START_TICKS)

    def _save(self, action, action_id, request_id, requested_ns, filename):
        self.custody.workbook_path.write_bytes((FIXTURES / filename).read_bytes())
        action_receipt = {'action': action, 'action_id': action_id,
                          'status': 'completed', 'release_verified': True}
        save_request = {
            'schema': 'agent-interface/calc-g10-save-request-v1',
            'call_id': CALL_ID, 'attempt_id': ATTEMPT_ID,
            'profile_id': PROFILE_ID, 'action': action,
            'action_id': action_id, 'process_generation': PROCESS_GENERATION,
            'window_generation': WINDOW_GENERATION,
            'save_request_id': request_id,
            'save_request_monotonic_ns': requested_ns,
        }
        return self.custody.record_saved_action(
            action, action_receipt=action_receipt, save_request=save_request)

    def _method(self, first_id='action-first', second_id='action-second'):
        return {
            'format': METHOD_FORMAT, 'outcome': 'TASK_SUCCEEDED',
            'reason': 'method_complete', 'completed_transitions': 2,
            'transitions': [
                {'action': 'first', 'action_id': first_id,
                 'release_verified': True},
                {'action': 'second', 'action_id': second_id,
                 'release_verified': True},
            ],
        }

    def _exit(self, observed_ns=30):
        return {
            'schema': 'agent-interface/calc-target-exit-receipt-v1',
            'status': 'exited', 'verified': True,
            'process_generation': PROCESS_GENERATION,
            'xid': XID, 'pid': PID, 'start_ticks': START_TICKS,
            'exit_code': 0, 'observed_monotonic_ns': observed_ns,
        }

    def _two_saves(self):
        first = self._save('first', 'action-first', '1' * 32, 10,
                           'first.fods')
        second = self._save('second', 'action-second', '2' * 32, 20,
                            'second.fods')
        return first, second

    def test_close_verification_without_target_binding_is_unknown(self):
        call_id = 'e' * 32
        root = Path(self.temp.name) / call_id
        root.mkdir()
        custody = CalcG10ArtifactCustody(
            root, call_id=call_id, attempt_id=ATTEMPT_ID)
        result = custody.verify_after_close(method_receipt=self._method(),
            close_receipt=CLOSE, target_exit_receipt=self._exit())
        self.assertEqual(result['status'], 'unknown')
        self.assertIsNone(result['task_success'])
        self.assertEqual(result['reason'], 'target_identity_unavailable')

    def test_both_archived_g10_saves_and_same_target_exit_verify(self):
        first, second = self._two_saves()
        self.assertNotEqual(first['artifact_sha256'], second['artifact_sha256'])
        result = self.custody.verify_after_close(method_receipt=self._method(),
            close_receipt=CLOSE, target_exit_receipt=self._exit())
        self.assertEqual(result['status'], 'verified')
        self.assertIs(result['task_success'], True)
        self.assertIs(result['replay_allowed'], False)
        self.assertEqual(set(result['saved_effects']), {'first', 'second'})
        self.assertEqual(
            result['saved_effects']['first']['effect']['status'], 'verified')
        self.assertEqual(
            result['saved_effects']['second']['effect']['status'], 'verified')

    def test_missing_second_save_never_promotes_success(self):
        self._save('first', 'action-first', '1' * 32, 10, 'first.fods')
        result = self.custody.verify_after_close(method_receipt=self._method(),
            close_receipt=CLOSE, target_exit_receipt=self._exit())
        self.assertEqual(result['status'], 'unknown')
        self.assertIsNone(result['task_success'])
        self.assertEqual(result['reason'], 'both_g10_save_receipts_required')

    def test_transition_mismatch_refuses_to_join_saved_effects(self):
        self._two_saves()
        method = self._method(second_id='different-action-id')
        result = self.custody.verify_after_close(method_receipt=method,
            close_receipt=CLOSE, target_exit_receipt=self._exit())
        self.assertEqual(result['status'], 'unknown')
        self.assertIsNone(result['task_success'])
        self.assertEqual(result['reason'], 'g10_transition_receipt_mismatch')

    def test_snapshot_mutation_after_receipt_is_unknown(self):
        self._two_saves()
        (self.root / 'g10-first.fods').write_bytes(b'changed')
        result = self.custody.verify_after_close(method_receipt=self._method(),
            close_receipt=CLOSE, target_exit_receipt=self._exit())
        self.assertEqual(result['status'], 'unknown')
        self.assertIsNone(result['task_success'])
        self.assertEqual(result['reason'], 'g10_snapshot_custody_mismatch')

    def test_exit_before_both_save_requests_is_unknown(self):
        self._two_saves()
        result = self.custody.verify_after_close(method_receipt=self._method(),
            close_receipt=CLOSE, target_exit_receipt=self._exit(observed_ns=20))
        self.assertEqual(result['status'], 'unknown')
        self.assertIsNone(result['task_success'])
        self.assertEqual(result['reason'], 'target_process_exit_invalid')

    def test_wrong_saved_effect_is_a_scoped_failure_after_valid_custody(self):
        self._save('first', 'action-first', '1' * 32, 10, 'second.fods')
        self._save('second', 'action-second', '2' * 32, 20, 'second.fods')
        result = self.custody.verify_after_close(method_receipt=self._method(),
            close_receipt=CLOSE, target_exit_receipt=self._exit())
        self.assertEqual(result['status'], 'failed')
        self.assertIs(result['task_success'], False)
        self.assertIs(result['replay_allowed'], False)

    def test_unreleased_action_and_reused_save_request_are_rejected(self):
        self.custody.workbook_path.write_bytes(
            (FIXTURES / 'first.fods').read_bytes())
        receipt = {'action': 'first', 'action_id': 'action-first',
                   'status': 'completed', 'release_verified': False}
        request = {'schema': 'agent-interface/calc-g10-save-request-v1',
            'call_id': CALL_ID, 'attempt_id': ATTEMPT_ID,
            'profile_id': PROFILE_ID, 'action': 'first',
            'action_id': 'action-first', 'process_generation': PROCESS_GENERATION,
            'window_generation': WINDOW_GENERATION,
            'save_request_id': '1' * 32, 'save_request_monotonic_ns': 10}
        with self.assertRaises(ValueError):
            self.custody.record_saved_action(
                'first', action_receipt=receipt, save_request=request)
        self._save('first', 'action-first', '1' * 32, 10, 'first.fods')
        with self.assertRaises(ValueError):
            self._save('second', 'action-second', '1' * 32, 20,
                       'second.fods')

    def test_changed_blank_is_refused_before_target_binding(self):
        call_id = 'e' * 32
        root = Path(self.temp.name) / call_id
        root.mkdir()
        artifact = CalcG10ArtifactCustody(
            root, call_id=call_id, attempt_id=ATTEMPT_ID)
        artifact.workbook_path.write_bytes(b'prepopulated')
        with self.assertRaisesRegex(ValueError, 'blank workbook changed'):
            artifact.bind_target(process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION, target_xid=XID,
                target_pid=PID, target_start_ticks=START_TICKS)


if __name__ == '__main__':
    unittest.main()
