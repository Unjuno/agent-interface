"""Direct target subscriptions with actual query reader; Fake X transport only."""
from collections import deque
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from Xlib import X
from .target_queries import X11TargetQueries


class LifecycleConnection:
    def __init__(self):
        self.events = deque()
        self.mask = 0
        self.selections = []
        self.on_attributes = lambda: None
        self.closed = False

    def create_resource_object(self, kind, xid):
        def select(**kwargs):
            self.mask = kwargs['event_mask']
            self.selections.append((xid, self.mask))
        def attributes():
            self.on_attributes()
            return SimpleNamespace(your_event_mask=self.mask)
        return SimpleNamespace(id=xid, change_attributes=select, get_attributes=attributes)

    def sync(self): pass
    def pending_events(self): return len(self.events)
    def next_event(self): return self.events.popleft()
    def close(self): self.closed = True
    def get_input_focus(self): return SimpleNamespace(focus=SimpleNamespace(id=20))

    def event(self, kind, *, xid=20, synthetic=False):
        self.events.append(SimpleNamespace(type=kind, window=SimpleNamespace(id=xid),
            event=SimpleNamespace(id=xid), send_event=synthetic))


class LifecycleReaderTests(unittest.TestCase):
    def reader(self, connection):
        with patch('runtime.guarded_x11_v1.target_queries.display.Display', return_value=connection):
            reader = X11TargetQueries(':fake-lifecycle')
        self.addCleanup(reader.close)
        return reader

    def test_direct_subscription_preserves_remap_reparent_and_repaint(self):
        connection = LifecycleConnection()
        reader = self.reader(connection)
        token = reader.read('window_incarnation', 20)
        self.assertRegex(token, r'^[0-9a-f]{64}$')
        self.assertEqual(connection.selections, [(20, X.StructureNotifyMask)])
        for kind in (X.UnmapNotify, X.ReparentNotify, X.MapNotify, X.ConfigureNotify):
            connection.event(kind)
            self.assertEqual(reader.read('window_incarnation', 20), token)
        self.assertEqual(connection.selections, [(20, X.StructureNotifyMask)])

    def test_destroy_reuse_is_sticky_even_after_event_drained(self):
        connection = LifecycleConnection()
        reader = self.reader(connection)
        reader.read('window_incarnation', 20)
        connection.event(X.DestroyNotify)
        for _ in range(2):
            with self.assertRaises(RuntimeError): reader.read('window_incarnation', 20)
        self.assertEqual(len(connection.selections), 1)

    def test_new_observer_does_not_reuse_token(self):
        first = self.reader(LifecycleConnection()).read('window_incarnation', 20)
        second = self.reader(LifecycleConnection()).read('window_incarnation', 20)
        self.assertNotEqual(first, second)

    def test_unknown_coverage_transport_events_and_overflow_retire(self):
        for fault in ('mask', 'transport', 'synthetic', 'malformed', 'overflow'):
            with self.subTest(fault=fault):
                connection = LifecycleConnection()
                reader = self.reader(connection)
                reader.read('window_incarnation', 20)
                if fault == 'mask': connection.mask = 0
                elif fault == 'transport': connection.on_attributes = lambda: (_ for _ in ()).throw(OSError('lost'))
                elif fault == 'synthetic': connection.event(X.ReparentNotify, synthetic=True)
                elif fault == 'malformed': connection.events.append(SimpleNamespace(type=X.DestroyNotify))
                else:
                    for _ in range(257): connection.event(X.ConfigureNotify)
                for _ in range(2):
                    with self.assertRaises(RuntimeError): reader.read('window_incarnation', 20)

    def test_destruction_during_initial_subscription_never_yields_source(self):
        connection = LifecycleConnection()
        connection.on_attributes = lambda: connection.event(X.DestroyNotify)
        reader = self.reader(connection)
        with self.assertRaises(RuntimeError): reader.read('window_incarnation', 20)


if __name__ == '__main__': unittest.main()
