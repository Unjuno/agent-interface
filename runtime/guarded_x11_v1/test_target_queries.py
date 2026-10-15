import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from .target_queries import QueryUnavailable, TargetQueryWorker, X11TargetQueries


class QueryWorkerTests(unittest.TestCase):
    def test_readonly_protocol_client_and_close_share_worker_thread(self):
        ids, closed = [], threading.Event()
        connection = SimpleNamespace(
            get_input_focus=lambda:ids.append(threading.get_ident()) or SimpleNamespace(focus=SimpleNamespace(id=20)),
            close=lambda:ids.append(threading.get_ident()) or closed.set())
        with patch('runtime.guarded_x11_v1.target_queries.display.Display',return_value=connection) as opened, \
                patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity',return_value='a'*64) as identity:
            worker = TargetQueryWorker(lambda:X11TargetQueries(':frozen-name'))
            try:
                self.assertIs(worker.read('focus',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False),True)
                self.assertEqual(worker.read('process_identity',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False),'a'*64)
            finally: worker.close()
            self.assertTrue(closed.wait(2))
            opened.assert_called_once_with(':frozen-name')
            identity.assert_called_once_with(connection,20)
            self.assertEqual(len(set(ids)),1)
            self.assertNotIn(threading.get_ident(),ids)

    def test_close_before_start_and_expired_request_create_no_thread(self):
        for close_first in (False,True):
            factory = Mock()
            worker = TargetQueryWorker(factory)
            if close_first: worker.close()
            with self.assertRaises(QueryUnavailable):
                worker.read('focus',20,deadline_ns=0,cancelled=lambda:False)
            factory.assert_not_called()
            self.assertFalse(worker.snapshot()['thread_alive'])

    def test_cancelled_pending_request_discards_late_value_and_never_reopens(self):
        entered,resume,closed,cancel = [threading.Event() for _ in range(4)]
        results = []
        class Reader:
            def read(self,operation,xid):
                entered.set();resume.wait(3);return 'late'
            def close(self): closed.set()
        factory = Mock(return_value=Reader())
        worker = TargetQueryWorker(factory)
        def invoke():
            try: results.append(worker.read('focus',20,deadline_ns=time.monotonic_ns()+2_000_000_000,cancelled=cancel.is_set))
            except QueryUnavailable: results.append('refused')
        caller = threading.Thread(target=invoke)
        caller.start()
        try:
            self.assertTrue(entered.wait(1));cancel.set();caller.join(1)
            self.assertFalse(caller.is_alive());self.assertEqual(results,['refused'])
            self.assertTrue(worker.snapshot()['retired']);self.assertTrue(worker.snapshot()['pending'])
            resume.set();self.assertTrue(closed.wait(1))
            with self.assertRaises(QueryUnavailable):
                worker.read('focus',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False)
            factory.assert_called_once()
        finally:
            cancel.set();resume.set();worker.close();caller.join(2)

    def test_query_failure_remains_a_failure_and_closes_client(self):
        closed = threading.Event()
        reader = SimpleNamespace(read=Mock(side_effect=OSError('query unavailable')),close=closed.set)
        worker = TargetQueryWorker(lambda:reader)
        with self.assertRaises(QueryUnavailable):
            worker.read('process_identity',20,deadline_ns=time.monotonic_ns()+1_000_000_000,cancelled=lambda:False)
        self.assertTrue(closed.wait(2));self.assertTrue(worker.snapshot()['retired'])
