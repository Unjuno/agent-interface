"""Supported Python bridge -> public dispatch -> actual X11 session/backend."""
import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from Xlib import X

from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.bridge import NativeHandleBridge


class GuardedInterruptTests(unittest.TestCase):
    def test_interrupted_press_releases_and_requires_explicit_recovery_and_review(self):
        for failed_readback in (False, True):
            with self.subTest(failed_readback=failed_readback):
                fake = FakeX(self)
                with tempfile.TemporaryDirectory() as td:
                    bridge = NativeHandleBridge(':fake', {'app': 20}, 'app', Path(td) / 'owner')
                    try:
                        source = bridge.observe()
                        offset = bridge.mint('field', source['sequence'], [8, 8], region_size=(12, 12))
                        original = KeyboardInterrupt('after fake CTRL press')
                        def emit(connection, kind, code):
                            fake.emit(connection, kind, code)
                            if kind == X.KeyPress:
                                raise original
                        if failed_readback:
                            def unreadable():
                                raise OSError('cleanup readback')
                            fake.backend.d.query_keymap = unreadable
                        with patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit):
                            with self.assertRaises(KeyboardInterrupt) as caught:
                                bridge.keyboard('field', offset, tail=[{'op': 'key_chord', 'keys': ['CTRL', 'a']}])
                        self.assertIs(caught.exception, original)
                        self.assertIsNone(bridge.active)
                        self.assertIsNone(bridge.deadline)
                        self.assertTrue(bridge.session.recovery_required)
                        evidence = fake.backend.interrupted_execution
                        self.assertEqual(evidence['completed_ops'], [0])
                        self.assertEqual(evidence['failed_op'], 1)
                        self.assertEqual(evidence['releases'][0]['verified'], not failed_readback)
                        self.assertEqual(fake.down, set())
                        self.assertEqual(fake.backend.held_keycodes, {'CTRL': 1} if failed_readback else {})
                        print(json.dumps({'case': 'guarded-interrupt', 'failed_readback': failed_readback,
                            'emissions': list(fake.emissions), 'fake_down': sorted(fake.down),
                            'held_keycodes': dict(fake.backend.held_keycodes),
                            'quarantine': bridge.session.recovery_required, 'execution': evidence}), flush=True)
                        before = list(fake.emissions)
                        refused = bridge.keyboard('field', offset, tail=[{'op': 'text', 'text': 'a'}])
                        self.assertEqual(refused['status'], 'refused')
                        self.assertEqual(fake.emissions, before)
                        fake.backend.d.query_keymap = fake.keymap
                        recovered = bridge.recover_input(bridge.binding_revision)
                        self.assertEqual(recovered['status'], 'input_recovered')
                        self.assertTrue(recovered['review_required'])
                        self.assertFalse(recovered['replay_allowed'])
                        self.assertIsNone(recovered['task_success'])
                        self.assertEqual(len(bridge.history), 0)
                        self.assertEqual([e for e in fake.emissions if e[0] == X.KeyPress], [(X.KeyPress, 1)])
                        self.assertIs(fake.backend.interrupted_execution, evidence)
                        print(json.dumps({'case': 'guarded-recovery', 'failed_readback': failed_readback,
                            'emissions': list(fake.emissions), 'report': recovered,
                            'quarantine': bridge.session.recovery_required}), flush=True)
                    finally:
                        bridge.close()


if __name__ == '__main__':
    unittest.main()
