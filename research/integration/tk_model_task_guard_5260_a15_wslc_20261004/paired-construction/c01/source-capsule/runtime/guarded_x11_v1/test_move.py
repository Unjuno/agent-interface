"""Pointer-only guarded admission and retained dispatch contracts, without X11."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from runtime.guarded_x11_v1.bridge import NativeHandleBridge


class MoveTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(NativeHandleBridge, 'move', None)),
                        'guarded pointer-only move API is missing')
        self.bridge = object.__new__(NativeHandleBridge)
        self.bridge.active = None
        self.bridge.session = SimpleNamespace(recovery_required=False)
        self.bridge.review_required = False
        self.bridge.sequence = 7
        self.bridge.binding_revision = 2
        self.bridge.scope = 'move:test'
        self.bridge.target = 'app'
        self.bridge._save = Mock()
        self.bridge.check = Mock(return_value={'point': [20, 30]})
        self.dispatcher = patch('runtime.guarded_x11_v1.bridge.dispatch_in_session')
        self.dispatch = self.dispatcher.start()
        self.addCleanup(self.dispatcher.stop)
        self.dispatch.return_value = {'status': 'returned', 'result': {
            'status': 'completed', 'execution': {'releases': [
                {'verified': True, 'keys_down': [], 'buttons_down': []}]}}}

    def test_move_emits_only_focus_motion_wait_and_release(self):
        row = self.bridge.move('save', [12, 7], tail=[{'op': 'wait_update', 'timeout_ms': 100}])
        self.assertEqual(row['status'], 'completed')
        program = self.dispatch.call_args.args[1]
        self.assertEqual(program['ops'], [
            {'op': 'focus', 'target': 'app'},
            {'op': 'pointer_move', 'frame': 'screen_physical_px', 'x': 20, 'y': 30},
            {'op': 'wait_update', 'timeout_ms': 100}, {'op': 'release_all'}])
        self.assertTrue(program['terminal']['release_all_required'])
        self.bridge.check.assert_called_once_with('before_admission')
        self.assertIsNone(self.bridge.active)
        self.assertIsNone(self.bridge.deadline)

    def test_move_rejects_input_in_tail_before_admission(self):
        for op in ({'op': 'text', 'text': 'unsafe'}, {'op': 'key_chord', 'keys': ['ENTER']},
                   {'op': 'pointer_button', 'button': 'left', 'down': True}):
            with self.subTest(op=op), self.assertRaisesRegex(ValueError, 'move'):
                self.bridge.move('save', [12, 7], tail=[op])
        self.dispatch.assert_not_called()
        self.bridge.check.assert_not_called()

    def test_changed_reference_refuses_without_dispatch(self):
        self.bridge.check.side_effect = RuntimeError('region_pixels_missing')
        row = self.bridge.move('save', [12, 7])
        self.assertEqual(row['status'], 'refused')
        self.assertFalse(row['input_dispatched'])
        self.dispatch.assert_not_called()
        self.assertIsNone(self.bridge.active)

    def test_recovery_or_window_review_blocks_motion(self):
        for recovery, review, error in [(True, False, 'INPUT_RECOVERY_REQUIRED'),
                                        (False, True, 'WINDOW_REVIEW_REQUIRED')]:
            self.bridge.session.recovery_required = recovery
            self.bridge.review_required = review
            row = self.bridge.move('save', [12, 7])
            self.assertEqual(row['error'], error)
            self.assertFalse(row['input_dispatched'])
        self.dispatch.assert_not_called()
        self.bridge.check.assert_not_called()

    def test_failed_execution_and_release_are_returned_without_replay(self):
        failure = {'status': 'execution_failed', 'recovery_required': True,
                   'execution': {'failed_op': 1, 'failed_op_effect': 'unknown',
                                 'releases': [{'verified': False}]}}
        self.dispatch.return_value = {'status': 'returned', 'result': failure}
        row = self.bridge.move('save', [12, 7])
        self.assertEqual(row['status'], 'execution_failed')
        self.assertFalse(row['execution']['releases'][0]['verified'])
        self.dispatch.assert_called_once()
        self.assertIsNone(self.bridge.active)


if __name__ == '__main__': unittest.main()
