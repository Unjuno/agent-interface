"""Exercise deadline refusal through the real execution and recovery wrapper."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.guarded_x11_v1.bridge import _GuardedBackend


class MotionDeadlineSessionTests(unittest.TestCase):
    def test_expiry_runs_cleanup_and_blocks_suffix(self):
        for verified in (True, False):
            with self.subTest(verified=verified):
                backend = object.__new__(_GuardedBackend)
                backend.owner = SimpleNamespace(
                    active=('target', [0, 0]), deadline=100,
                    check=Mock(return_value={'point': [20, 30]}),
                    _check_cancelled=Mock())
                backend.emissions = 0
                backend.preflight = Mock(return_value=None)
                backend.manifest = Mock(return_value={})
                backend.focus = Mock()
                backend.release_all = Mock(return_value={
                    'verified': verified, 'keys_down': [], 'buttons_down': []})
                session = X11RuntimeSession(backend)
                program = {'ops': [
                    {'op': 'focus', 'target': 'target'},
                    {'op': 'pointer_move', 'frame': 'screen_physical_px', 'x': 20, 'y': 30},
                    {'op': 'pointer_button', 'button': 'left', 'down': True},
                    {'op': 'release_all'}]}
                accepted = SimpleNamespace(accepted=True, required_capabilities=[])
                with patch('runtime.backends.x11_v1.session.admit_program', return_value=accepted), \
                     patch('runtime.guarded_x11_v1.bridge.time.monotonic_ns', return_value=100), \
                     patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit:
                    result = session.dispatch(program, current_observation_seq=1,
                                              current_binding_revision=1, now_ns=99)
                self.assertEqual(result['status'], 'execution_failed')
                self.assertEqual(result['execution']['failed_op'], 1)
                self.assertEqual(result['execution']['completed_ops'], [0])
                self.assertEqual(result['execution']['program_emissions'], 0)
                self.assertEqual(result['recovery_required'], not verified)
                backend.release_all.assert_called_once()
                emit.assert_not_called()
                if not verified:
                    refused = session.dispatch(program, current_observation_seq=1,
                                               current_binding_revision=1, now_ns=99)
                    self.assertEqual(refused['error'], 'INPUT_RECOVERY_REQUIRED')
                    backend.release_all.return_value['verified'] = True
                    recovery = session.recover_input()
                    self.assertEqual(recovery['status'], 'input_recovered')
                    self.assertFalse(recovery['replay_allowed'])
                    self.assertFalse(session.recovery_required)
                    self.assertEqual(backend.release_all.call_count, 2)
                    backend.focus.assert_called_once()


if __name__ == '__main__':
    unittest.main()
