"""A raw sibling session cannot revive the guarded owner's old aliases."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from Xlib import X

from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.bridge import NativeHandleBridge


class GuardedSharedRecoveryTests(unittest.TestCase):
    def test_sibling_recovery_cannot_revive_old_guarded_alias(self):
        fake = FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            bridge = NativeHandleBridge(':fake', {'app': 20}, 'app', Path(td) / 'owner')
            try:
                other = X11RuntimeSession(fake.backend)
                source = bridge.observe()
                offset = bridge.mint('field', source['sequence'], [8, 8], region_size=(12, 12))
                args = dict(tail=[{'op': 'key_chord', 'keys': ['CTRL', 'a']}])
                def emit(connection, kind, code):
                    fake.emit(connection, kind, code)
                    if kind == X.KeyPress:
                        raise OSError('after CTRL transport effect')
                def unreadable():
                    raise OSError('release readback unavailable')
                fake.backend.d.query_keymap = unreadable
                with patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit):
                    failed = bridge.keyboard('field', offset, **args)
                self.assertEqual(failed['status'], 'execution_failed')
                self.assertTrue(bridge.session.recovery_required)
                self.assertEqual(fake.backend.held_keycodes, {'CTRL': 1})
                self.assertEqual(fake.down, set())
                fake.backend.d.query_keymap = fake.keymap
                # Same backend and already-existing wrapper; a verified release
                # acknowledges only that wrapper's context, not old aliases.
                other.recovery_required = True
                recovered = other.recover_input()
                self.assertEqual(recovered['status'], 'input_recovered')
                before = list(fake.emissions)
                refused = bridge.keyboard('field', offset, **args)
                print(json.dumps({'case': 'sibling-recovery', 'failed': failed, 'recovery': recovered,
                    'before': before, 'after': fake.emissions, 'guarded_result': refused,
                    'guarded_recovery_required': bridge.session.recovery_required}), flush=True)
                self.assertEqual(refused['status'], 'refused')
                self.assertEqual(fake.emissions, before)
                self.assertTrue(bridge.session.recovery_required)
                own_recovery = bridge.recover_input(bridge.binding_revision)
                self.assertEqual(own_recovery['status'], 'input_recovered')
                self.assertTrue(own_recovery['review_required'])
                self.assertEqual(len(bridge.history), 0)
                self.assertFalse(other.recovery_required)
                self.assertFalse(own_recovery['replay_allowed'])
                self.assertIsNone(own_recovery['task_success'])
            finally:
                bridge.close()


if __name__ == '__main__':
    unittest.main()
