import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from native_tail_v1 import expand_tail
from native_handle_bridge_v1 import NativeHandleBridge


class NativeTailTests(unittest.TestCase):
    def test_matches_flat_order_without_implicit_wait(self):
        compact = [{'op': 'wait_update', 'timeout_ms': 50},
                   {'op': 'key_chord', 'keys': ['Right'], 'repeat': 18},
                   {'op': 'key_chord', 'keys': ['CTRL', 's']}]
        flat = [compact[0]] + [{'op': 'key_chord', 'keys': ['Right']} for _ in range(18)] + [compact[2]]
        self.assertEqual(expand_tail(compact, max_ops=123), flat)

    def test_independent_copies_preserve_caller(self):
        request = [{'op': 'key_chord', 'keys': ['Right'], 'repeat': 2}]
        output = expand_tail(request, max_ops=123)
        output[0]['keys'][0] = 'Left'
        self.assertEqual(output[1]['keys'], ['Right'])
        self.assertEqual(request[0]['keys'], ['Right'])

    def test_bad_counts_and_types(self):
        for count in (True, False, 0, -1, 1.0, '2', None, 127, 10**100):
            with self.subTest(count=count), self.assertRaises(ValueError):
                expand_tail([{'op': 'key_chord', 'keys': ['Right'], 'repeat': count}], max_ops=126)

    def test_repeat_on_other_operations_refused(self):
        for name in ('text', 'wait_update', 'repeat', 'pointer_button'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                expand_tail([{'op': name, 'repeat': 1}], max_ops=123)

    def test_capacity_includes_flat_and_expanded_ops(self):
        chord = {'op': 'key_chord', 'keys': ['Right'], 'repeat': 123}
        self.assertEqual(len(expand_tail([chord], max_ops=123)), 123)
        with self.assertRaises(ValueError):
            expand_tail([chord, {'op': 'observe'}], max_ops=123)
        self.assertEqual(len(expand_tail([dict(chord, repeat=126)], max_ops=126)), 126)

    def test_bridge_rejects_before_guard_or_dispatch(self):
        bridge = object.__new__(NativeHandleBridge)
        bridge.active = None
        bridge.check = Mock()
        bridge.session = SimpleNamespace(recovery_required=False, dispatch=Mock())
        for activate in (True, False):
            with self.subTest(activate=activate), self.assertRaises(ValueError):
                bridge._run_guarded('alias', [0, 0], tail=[
                    {'op': 'key_chord', 'keys': ['Right'], 'repeat': 127}], activate=activate)
        bridge.check.assert_not_called()
        bridge.session.dispatch.assert_not_called()
        self.assertIsNone(bridge.active)


if __name__ == '__main__':
    unittest.main()
