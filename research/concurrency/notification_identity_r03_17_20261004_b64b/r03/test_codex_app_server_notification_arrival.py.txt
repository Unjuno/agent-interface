"""Public reentry repair regressions with a real Condition and inert reader."""
import json
import threading
import types
import unittest
from collections import deque

from codex_app_server_client_v2 import CodexAppServerClient


class Arrival(unittest.TestCase):
    def exercise(self, eof):
        client = CodexAppServerClient.__new__(CodexAppServerClient)
        old = {'method': 'eligible', 'params': {'tag': 'old', 'intent': '保持した豊かな意図'}}
        new = {'method': 'eligible', 'params': {'tag': 'new', 'intent': '保持した豊かな意図'}}
        marker = {'method': 'marker', 'params': {'tag': 'marker'}}
        client._notifications = deque([old])
        client._notification_consumptions = 0
        client._responses = {}
        client._closed = False
        selected = threading.Event()
        consumed = threading.Event()
        finish = threading.Event()
        endpoint = threading.Event()
        outer_done = threading.Event()
        callback = threading.local()
        waits, errors, visits, received, returns = [], [], [], [], {}

        class ObservedCondition(threading.Condition):
            def wait(self, timeout=None):
                if threading.current_thread().name == 'arrival-outer':
                    active = getattr(callback, 'active', False)
                    waits.append({'nested_callback': active,
                                  'queued': [x['params']['tag'] for x in client._notifications]})
                    if not active:
                        endpoint.set()
                return super().wait(timeout)

        client._condition = ObservedCondition()

        def stream():
            if not consumed.wait(2):
                raise AssertionError('old-consumer gate')
            yield json.dumps(new, ensure_ascii=False) + '\n'
            yield json.dumps(marker) + '\n'
            if not eof and not finish.wait(2):
                raise AssertionError('reader-cleanup gate')

        client.process = types.SimpleNamespace(stdout=stream())
        client._record = lambda direction, row: received.append((direction, row))

        def predicate(row):
            visits.append(row['params']['tag'])
            if row is old:
                selected.set()
                callback.active = True
                try:
                    returns['nested'] = client.wait_notification(
                        lambda item: item.get('method') == 'marker', timeout=2)
                finally:
                    callback.active = False
                if not consumed.is_set():
                    raise AssertionError('old not consumed before callback return')
                if [x['params']['tag'] for x in client._notifications] != ['new']:
                    raise AssertionError('fresh not queued before callback return')
            return True

        def outer():
            returns['outer'] = client.wait_notification(predicate, timeout=2)

        def consumer():
            if not selected.wait(2):
                raise AssertionError('outer-selection gate')
            returns['consumer'] = client.wait_notification(lambda row: row is old, timeout=2)
            consumed.set()

        def guarded(name, action):
            try:
                action()
            except BaseException as error:
                errors.append((name, type(error).__name__, str(error)))
            finally:
                if name == 'outer':
                    outer_done.set()
                    endpoint.set()

        threads = [threading.Thread(target=guarded, args=('reader', client._read), name='arrival-reader'),
                   threading.Thread(target=guarded, args=('consumer', consumer), name='arrival-consumer'),
                   threading.Thread(target=guarded, args=('outer', outer), name='arrival-outer')]
        for thread in threads:
            thread.start()
        reached = endpoint.wait(2)
        # Cleanup can notify after the asserted endpoint, but is never a success wake.
        finished_without_cleanup = outer_done.is_set()
        finish.set()
        with client._condition:
            client._condition.notify_all()
        for thread in threads:
            thread.join(2)
        self.assertTrue(reached, 'finite endpoint')
        self.assertTrue(finished_without_cleanup, 'completion required before cleanup notify')
        self.assertTrue(all(not thread.is_alive() for thread in threads), 'all owned threads retired')
        self.assertEqual(errors, [])
        self.assertIs(returns['consumer'], old)
        self.assertEqual(returns['nested'], marker)
        self.assertEqual(returns['outer'], new)
        self.assertIsNot(returns['consumer'], returns['outer'])
        self.assertEqual(visits, ['old', 'new'])
        self.assertTrue(waits, 'real nested Condition wait observed')
        self.assertTrue(all(row['nested_callback'] for row in waits), 'no post-predicate sleep')
        self.assertEqual(client._notification_consumptions, 3)
        self.assertEqual(list(client._notifications), [])
        self.assertEqual([row['params']['tag'] for _, row in received], ['new', 'marker'])
        self.assertEqual(returns['outer']['params']['intent'], old['params']['intent'])
        print(json.dumps({'eof_after_marker': eof, 'returns': {k: v['params']['tag'] for k, v in returns.items()},
                          'waits': waits, 'visits': visits, 'consumptions': client._notification_consumptions,
                          'all_threads_retired': True, 'completed_before_cleanup_notify': finished_without_cleanup}, sort_keys=True))

    def test_new_notification_before_wait_with_open_reader(self):
        self.exercise(False)

    def test_new_notification_before_wait_with_reader_eof(self):
        self.exercise(True)
