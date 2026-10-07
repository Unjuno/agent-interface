import copy
import json
from pathlib import Path
import queue
import tarfile
import threading
from types import SimpleNamespace
import unittest
from gate import fault_gate
from runner import InjectionStream, factory


class FaultGateTests(unittest.TestCase):
    def fixture(self, case='candidate_fault'):
        return {'case': case, 'right_code': 114, 'wait_outcome': '_SessionReaderFailure',
                'cause': 'JSONDecodeError', 'reader_alive_at_cancel': False,
                'after_notification': {'keys': [114], 'buttons': []},
                'before_cancel': {'keys': [114], 'buttons': []},
                'injection_state': {'keys': [114], 'buttons': []},
                'held_ns': 10, 'fault_requested_ns': 11, 'injected_ns': 13,
                'wait_start_ns': 12, 'wait_end_ns': 14, 'notification_sample_ns': 15,
                'before_cancel_ns': 16, 'cancel_send': {'start_ns': 17}, 'unhandled': []}

    def test_rejects_not_held_notification_and_wrong_fault(self):
        self.assertTrue(fault_gate(self.fixture()))
        for field, value in [('cause', 'UnicodeDecodeError'), ('reader_alive_at_cancel', 0),
                             ('injected_ns', None), ('injection_state', {'keys': [], 'buttons': []}),
                             ('after_notification', {'keys': [], 'buttons': []}),
                             ('before_cancel', {'keys': [114], 'buttons': [1]}),
                             ('unhandled', [{'thread': 'native-evidence-drain', 'type': 'ValueError'}])]:
            with self.subTest(field=field):
                row = self.fixture(); row[field] = value
                self.assertFalse(fault_gate(row))

    def test_healthy_requires_live_reader_and_no_injection(self):
        row = self.fixture('candidate_healthy')
        row.update(wait_outcome='TimeoutError', cause=None, reader_alive_at_cancel=True,
                   injected_ns=None, injection_state=None)
        self.assertTrue(fault_gate(row))
        row['injected_ns'] = 13
        self.assertFalse(fault_gate(row))

    def test_original_requires_exact_unhandled_reader_error_only(self):
        row = self.fixture('original_fault')
        row.update(wait_outcome='TimeoutError', cause=None,
                   unhandled=[{'thread': 'selected-v39-reader', 'type': 'JSONDecodeError'}])
        self.assertTrue(fault_gate(row))
        row['unhandled'].append({'thread': 'native-evidence-drain', 'type': 'ValueError'})
        self.assertFalse(fault_gate(row))


class ExactReceiverTests(unittest.TestCase):
    def snapshot(self, name):
        with tarfile.open(Path(__file__).parent / 'source-closure.tar.gz', 'r:gz') as archive:
            return archive.extractfile('research/doom/v39_reader_signal_59_e02_20261004_3cbf/source/' + name).read()

    def test_exact_candidate_surfaces_parser_cause_from_injected_stream(self):
        wire = queue.Queue(); trigger = threading.Event(); trigger.set()
        stream = InjectionStream(wire, trigger)
        stream.observe = lambda: {'keys': [114], 'buttons': []}
        reader, wait, events = factory(self.snapshot('v39-candidate.py.txt'))(
            SimpleNamespace(stdout=stream, poll=lambda: None), queue.Queue())
        thread = threading.Thread(target=reader); thread.start(); thread.join(1)
        self.assertFalse(thread.is_alive())
        with self.assertRaises(RuntimeError) as caught:
            wait(lambda row: False, timeout=.02)
        self.assertEqual(type(caught.exception).__name__, '_SessionReaderFailure')
        self.assertIsInstance(caught.exception.__cause__, json.JSONDecodeError)
        self.assertEqual(caught.exception.__cause__.doc, 'not-json\n')
        self.assertEqual(events, [])

    def test_both_exact_readers_deliver_real_ready_without_injection(self):
        for name in ('v39-original.py.txt', 'v39-candidate.py.txt'):
            with self.subTest(name=name):
                wire = queue.Queue(); wire.put('{"event":"ready"}\n'); wire.put(None)
                stream = InjectionStream(wire, threading.Event())
                reader, wait, events = factory(self.snapshot(name))(
                    SimpleNamespace(stdout=stream, poll=lambda: None), queue.Queue())
                thread = threading.Thread(target=reader); thread.start(); thread.join(1)
                self.assertEqual(wait(lambda row: row['event'] == 'ready', timeout=.02), {'event': 'ready'})
                self.assertEqual(events, [{'event': 'ready'}]); self.assertIsNone(stream.injected_ns)


if __name__ == '__main__':
    unittest.main()
