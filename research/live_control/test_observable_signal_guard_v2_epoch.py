"""Current-caller health-only early delivery and epoch refusal checks."""
import copy
import queue
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'research/doom'), str(ROOT / 'research/live_control')]
from research.live_control.test_observable_signal_guard_v2 import (
    Extractor, ObservableSignalGuard, ObservableSignalPolicyMonitor,
    signal, spec, typed_observation)
import map01_overlap_controller_v39 as controller


class HealthTypedEpochTests(unittest.TestCase):
    def monitor(self):
        extractor = Extractor()
        return ObservableSignalPolicyMonitor(
            ObservableSignalGuard(spec(), signal(), signal()['binding']), extractor), extractor

    def test_new_sequence_cannot_move_capture_time_backward_or_repeat_it(self):
        for capture in (1_050_000_000, 1_100_000_000):
            with self.subTest(capture=capture):
                monitor, extractor = self.monitor()
                self.assertIsNone(monitor.observe(typed_observation(signal(87))))
                result = monitor.observe(typed_observation(
                    signal(86), sequence=39, capture_ns=capture))
                self.assertIsNotNone(result)
                self.assertEqual(result['outcome']['status'], 'UNKNOWN')
                self.assertTrue(result['outcome']['requires_new_decision'])
                self.assertEqual(monitor.soft_event_count, 1)
                self.assertEqual(extractor.calls, 0)

    def test_typed_signals_obey_shared_doom_domains(self):
        for name, value in (('health', 201), ('health', 0), ('health', -1), ('ammo', -1), ('ammo', 1000)):
            with self.subTest(name=name, value=value):
                monitor, extractor = self.monitor()
                typed = typed_observation(signal(87))
                typed['signals'][name]['value'] = value
                result = monitor.observe(typed)
                self.assertIsNotNone(result)
                self.assertEqual(result['outcome']['status'], 'UNKNOWN')
                self.assertFalse(result['outcome']['keep_existing_policy'])
                self.assertEqual(extractor.calls, 0)

    def test_each_epoch_accepts_each_transport_kind_only_once(self):
        typed = typed_observation(signal(87))
        full = {'event': 'observation', 'sequence': 38,
                'frame_rgb_sha256': typed['frame_rgb_sha256'],
                'signal': copy.deepcopy(typed['signals']['health'])}
        for first, second in ((typed, full), (full, typed)):
            with self.subTest(first=first['event']):
                monitor, _ = self.monitor()
                self.assertIsNone(monitor.observe(first))
                self.assertIsNone(monitor.observe(second))
                result = monitor.observe(first)
                self.assertIsNotNone(result)
                self.assertEqual(result['outcome']['status'], 'UNKNOWN')
                self.assertTrue(result['outcome']['requires_new_decision'])
                self.assertEqual(monitor.soft_event_count, 1)

    def test_current_controller_drains_early_hard_health_without_artifact(self):
        class Reader:
            calls = 0
            def read(self, _observation):
                self.calls += 1
                if self.calls == 1:
                    return signal()
                raise AssertionError('early health must not read an artifact')
        reader = Reader()
        source = signal()
        validity = {'signal_id': 'health', 'critical_health_minimum': 80,
                    'maximum_health_loss': 20, 'max_source_age_ms': 30000}
        monitor, admission = controller.build_cover_monitor(reader, {'sequence': 37}, validity, 0)
        self.assertEqual(admission['status'], 'admitted')
        incoming = queue.Queue()
        incoming.put(typed_observation(signal(79)))
        result = controller.drain_pending_observation_events(incoming, monitor, 'cover-0')
        self.assertEqual(result['invalidation']['outcome']['status'], 'HARD_INVALIDATED')
        self.assertFalse(result['invalidation']['outcome']['grants_input_authority'])
        self.assertFalse(result['invalidation']['outcome']['task_success_verified'])
        self.assertEqual(reader.calls, 1)


if __name__ == '__main__':
    unittest.main()
