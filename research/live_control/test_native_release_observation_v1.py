import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from Xlib import X

from native_release_observation_v1 import observe_release_failure
from runtime.backends.x11_v1.session import X11RuntimeSession


class ReleaseObservationTests(unittest.TestCase):
    def backend(self):
        keymap = [0]*32
        keymap[5] = 2  # Keycode 41, deliberately absent from local tracking.
        return SimpleNamespace(emissions=7, held_keycodes={}, held_buttons=set(),
            d=SimpleNamespace(query_keymap=Mock(return_value=keymap)),
            root=SimpleNamespace(query_pointer=Mock(side_effect=[
                SimpleNamespace(mask=X.Button1Mask), SimpleNamespace(mask=0), SimpleNamespace(mask=0)])))

    def test_records_state_changes_without_emission_or_recovery_claim(self):
        backend = self.backend()
        session = X11RuntimeSession(backend)
        session.recovery_required = True
        row = observe_release_failure(backend)
        self.assertEqual([s['core_buttons_down'] for s in row['samples']], [[1], [], []])
        self.assertEqual([s['keycodes_down'] for s in row['samples']], [[41]]*3)
        self.assertFalse(row['input_dispatched'])
        self.assertFalse(row['clears_recovery_required'])
        self.assertEqual(backend.emissions, 7)
        self.assertEqual(backend.held_keycodes, {})
        self.assertTrue(session.recovery_required)
        self.assertEqual(session.dispatch({}, current_observation_seq=1,
                         current_binding_revision=0)['error'], 'INPUT_RECOVERY_REQUIRED')

    def test_query_failure_is_unknown_not_neutral(self):
        backend = self.backend()
        backend.root.query_pointer.side_effect = OSError('disconnected')
        row = observe_release_failure(backend)
        self.assertEqual(len(row['samples']), 1)
        self.assertEqual(row['samples'][0]['status'], 'unavailable')
        self.assertNotIn('core_buttons_down', row['samples'][0])

    def test_malformed_bitmap_stops_before_pointer_query(self):
        backend = self.backend()
        backend.d.query_keymap.return_value = []
        row = observe_release_failure(backend)
        self.assertEqual(row['samples'][0]['status'], 'unavailable')
        backend.root.query_pointer.assert_not_called()


if __name__ == '__main__':
    unittest.main()
