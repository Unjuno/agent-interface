import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from PIL import Image

from native_visual_watch_v1 import NativeVisualWatch


class WatchTests(unittest.TestCase):
    def bridge(self, frames, *, binding=None):
        source = {'sequence': 1, 'binding_revision': 0, 'capture_ns': 10,
                  'pointer_binding': {'focus': 2, 'surface': 2, 'geometry': [0, 0, 10, 10]}}
        bridge = SimpleNamespace(active=None, history={1: (source, Image.new('RGB', (10, 10)))},
                                 _focus_within_target=Mock(return_value=True))
        iterator = iter(frames)
        def observe():
            image = next(iterator)
            observation = dict(source, sequence=len(bridge.history)+1, capture_ns=20)
            if binding is not None:
                observation['pointer_binding'] = binding
            bridge.history[observation['sequence']] = (observation, image)
            return observation
        bridge.observe = Mock(side_effect=observe)
        return bridge

    def regions(self):
        return [{'id': 'left', 'box': [0, 0, 5, 10], 'min_changed_pixels': 1},
                {'id': 'right', 'box': [5, 0, 10, 10], 'min_changed_pixels': 2}]

    def test_two_lanes_share_exact_capture_and_keep_truth_separate(self):
        frame = Image.new('RGB', (10, 10))
        frame.putpixel((1, 1), (255, 0, 0))
        frame.putpixel((6, 1), (255, 0, 0))
        bridge = self.bridge([frame])
        watch = NativeVisualWatch(bridge, 1, self.regions())
        row = watch.run(bridge)
        self.assertEqual(row['status'], 'changed')
        self.assertEqual([(s['changed_pixels'], s['condition']) for s in row['latest']], [(1, True), (1, False)])
        self.assertEqual(bridge.observe.call_count, 1)
        self.assertIsNone(row['task_success'])
        self.assertFalse(row['authority_granted'])
        self.assertEqual({e['observation_sequence'] for e in row['events']}, {2})
        with self.assertRaises(RuntimeError):
            watch.run(bridge)

    def test_timeout_is_observed_false_not_unavailable(self):
        bridge = self.bridge([Image.new('RGB', (10, 10))])
        row = NativeVisualWatch(bridge, 1, self.regions(), timeout_ms=0).run(bridge)
        self.assertEqual(row['status'], 'timeout')
        self.assertEqual([s['condition'] for s in row['latest']], [False, False])

    def test_unavailable_never_becomes_false(self):
        for kind in ('focus', 'binding', 'capture'):
            with self.subTest(kind=kind):
                bridge = self.bridge([Image.new('RGB', (10, 10))], binding={} if kind == 'binding' else None)
                if kind == 'focus':
                    bridge._focus_within_target.return_value = False
                if kind == 'capture':
                    bridge.observe.side_effect = OSError('capture failed')
                row = NativeVisualWatch(bridge, 1, self.regions()).run(bridge)
                self.assertEqual(row['status'], 'unavailable')
                self.assertEqual([s['condition'] for s in row['latest']], [None, None])

    def test_invalid_registration_does_not_capture(self):
        bridge = self.bridge([])
        for regions in ([], self.regions()*2, [{'id': 'bad', 'box': [-1, 0, 5, 5], 'min_changed_pixels': 1}],
                        [{'id': 'bad', 'box': [0, 0, 5, 5], 'min_changed_pixels': True}]):
            with self.subTest(regions=regions), self.assertRaises(ValueError):
                NativeVisualWatch(bridge, 1, regions)
        bridge.observe.assert_not_called()

    def test_transitions_preserve_false_then_true(self):
        bridge = self.bridge([Image.new('RGB', (10, 10)), Image.new('RGB', (10, 10), 'white')])
        row = NativeVisualWatch(bridge, 1, self.regions()).run(bridge)
        self.assertEqual([e['condition'] for e in row['events']], [False, False, True, True])
        self.assertEqual([s['observation']['sequence'] for s in row['samples']], [2, 3])


if __name__ == '__main__':
    unittest.main()
