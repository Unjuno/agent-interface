"""Actual V12 owner with isolated read-only identity client; Fake X only."""
from contextlib import contextmanager
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
from test_input_owner_v12_explicit_up_cancel import FakeDisplay
from input_owner_v12 import InputOwner
from lease_release_v1 import Lease
from executor_v3 import DecisionRequired, Cancelled
import target_process_identity_v1 as identity


class Reader:
    def __init__(self):
        self.value = 'a' * 64
        self.block = False
        self.entered, self.resume, self.closed = threading.Event(), threading.Event(), threading.Event()
    def read(self, operation, xid):
        self.entered.set()
        if self.block and not self.resume.wait(3):
            raise RuntimeError('test reader not resumed')
        return self.value
    def close(self):
        self.closed.set()


@contextmanager
def fixture():
    import input_owner_v12 as native
    display, reader = FakeDisplay(), Reader()
    events = []
    def emit(connection, event, code):
        events.append((event, code))
        if event == native.X.KeyPress:
            display.down.add(code)
        elif event == native.X.KeyRelease:
            display.down.discard(code)
    with patch.object(native.display, 'Display', return_value=display), patch.object(
            native.xtest, 'fake_input', side_effect=emit), patch.object(
            identity, 'X11TargetQueries', return_value=reader):
        owner = InputOwner(':fake', process_identity=True)
        lease = Lease(time.perf_counter_ns() + 1_000_000_000)
        lease.expected_focus = 41
        lease.expected_surface = 41
        lease.target_process_identity = (1, 41, 'a' * 64, lease.deadline)
        try:
            yield owner, lease, display, reader, events
        finally:
            reader.resume.set()
            owner.close()
            owner.identity_reader.worker.thread.join(1) if owner.identity_reader.worker.thread else None


class OwnerIdentityTests(unittest.TestCase):
    def test_final_focus_read_cannot_change_cancel_or_source_before_press(self):
        for mode in ('cancel', 'source', 'deadline'):
            with self.subTest(mode=mode), fixture() as (owner, lease, display, reader, events):
                calls = 0
                def focus():
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        if mode == 'cancel': lease.set()
                        elif mode == 'source': lease.target_process_identity = (1, 41, 'b' * 64, lease.deadline)
                        else: lease.deadline += 1_000_000
                    return SimpleNamespace(focus=41)
                display.get_input_focus = focus
                with self.assertRaises((DecisionRequired, Cancelled)):
                    owner.call('down', lease, 'W')
                self.assertEqual(events, [])

    def test_fresh_source_admits_and_release_does_not_query_identity(self):
        with fixture() as (owner, lease, display, reader, events):
            owner.call('down', lease, 'W')
            reader.value = 'b' * 64
            release = owner.call('release', lease)
            self.assertTrue(release['verified'])
            self.assertEqual(display.down, set())
            self.assertEqual(events, [(2, 38), (3, 38)])

    def test_changed_unbound_or_deadline_relabelled_source_refuses(self):
        for mode in ('changed', 'missing', 'deadline', 'surface'):
            with self.subTest(mode=mode), fixture() as (owner, lease, display, reader, events):
                if mode == 'changed': reader.value = 'b' * 64
                elif mode == 'missing': lease.target_process_identity = None
                elif mode == 'deadline': lease.deadline += 1_000_000
                else: lease.target_process_identity = (1, 99, 'a' * 64, lease.deadline)
                with self.assertRaises(DecisionRequired): owner.call('down', lease, 'W')
                self.assertEqual(events, [])

    def test_held_generation_change_wakes_lease_and_releases_prefix(self):
        with fixture() as (owner, lease, display, reader, events):
            owner.call('down', lease, 'W')
            reader.value = 'b' * 64
            self.assertIsNotNone(lease.wait_interruption(1))
            self.assertEqual(lease.interruption_snapshot()['record']['reason'], 'target_generation_invalidated')
            self.assertEqual(display.down, set())
            with self.assertRaises(DecisionRequired): owner.call('down', lease, 'A')
            self.assertEqual([code for event, code in events if event == 2], [38])

    def test_blocked_held_identity_does_not_prevent_cancel_cleanup(self):
        with fixture() as (owner, lease, display, reader, events):
            owner.call('down', lease, 'W')
            reader.entered.clear(); reader.block = True
            self.assertTrue(reader.entered.wait(1))
            lease.set()
            self.assertIsNotNone(lease.wait_interruption(1))
            self.assertEqual(display.down, set())
            self.assertTrue(owner.identity_reader.worker.snapshot()['retired'])
            record = lease.interruption_snapshot()['record']
            self.assertTrue(record['target_process_identity_reader']['retired'])
            self.assertTrue(record['target_process_identity_reader']['pending'])
            self.assertEqual(record['target_process_identity'], list(lease.target_process_identity))
            self.assertFalse(reader.closed.is_set())
            reader.resume.set()
            self.assertTrue(reader.closed.wait(1))
            self.assertEqual([code for event, code in events if event == 2], [38])

    def test_blocked_identity_original_expiry_releases_before_reader_resumes(self):
        with fixture() as (owner, lease, display, reader, events):
            lease.deadline = time.perf_counter_ns() + 100_000_000
            lease.target_process_identity = (1, 41, 'a' * 64, lease.deadline)
            owner.call('down', lease, 'W')
            reader.entered.clear(); reader.block = True
            self.assertTrue(reader.entered.wait(1))
            self.assertIsNotNone(lease.wait_interruption(1))
            self.assertEqual(lease.interruption_snapshot()['record']['reason'], 'expired')
            self.assertEqual(display.down, set())
            self.assertFalse(reader.closed.is_set())

    def test_close_while_identity_is_blocked_stops_input_owner(self):
        with fixture() as (owner, lease, display, reader, events):
            owner.call('down', lease, 'W')
            reader.entered.clear(); reader.block = True
            self.assertTrue(reader.entered.wait(1))
            owner.close()
            self.assertTrue(owner.stopped.is_set())
            self.assertFalse(owner.thread.is_alive())
            self.assertEqual(display.down, set())
            self.assertFalse(reader.closed.is_set())
