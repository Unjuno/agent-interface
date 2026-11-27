"""Explicit close fences waiters even if receive-side journal retirement stalls."""
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from research.live_control.codex_app_server_client_v2 import AppServerError, CodexAppServerClient
from research.live_control.persistent_planner_adapter_v2 import PersistentPlannerAdapter
from research.live_control.test_codex_app_server_send_deadline_v1 import owned_client


class CloseWaiterTests(unittest.TestCase):
    def test_close_fence_cannot_become_visible_during_cached_publication(self):
        with owned_client() as (client, read_fd):
            predicate_entered, resume, close_lock_attempted = (threading.Event() for _ in range(3))
            class PublicationCondition(threading.Condition):
                def __init__(self):
                    super().__init__()
                    acquire = self.acquire
                    def observed_acquire(*args, **kwargs):
                        if threading.current_thread().name == 'fixture-closer':
                            close_lock_attempted.set()
                        return acquire(*args, **kwargs)
                    self.acquire = observed_acquire
            client._condition = PublicationCondition()
            row = {'method': 'fixture/queued'}
            with client._condition: client._notifications.append(row)
            results = {}
            def predicate(value):
                predicate_entered.set()
                if not resume.wait(2): raise TimeoutError('publication test gate not resumed')
                return True
            def wait():
                try: results['row'] = client.wait_notification(predicate, timeout=1)
                except BaseException as error: results['wait_error'] = error
            def close():
                try: client.close(timeout=1)
                except BaseException as error: results['close_error'] = error
            waiter = threading.Thread(target=wait)
            closer = threading.Thread(target=close, name='fixture-closer')
            waiter.start()
            try:
                self.assertTrue(predicate_entered.wait(1))
                closer.start()
                self.assertTrue(close_lock_attempted.wait(1))
                self.assertFalse(client._closing, 'close flag escaped the publication lock')
            finally:
                resume.set()
                waiter.join(1)
                if closer.ident is not None: closer.join(1)
            self.assertFalse(waiter.is_alive())
            self.assertFalse(closer.is_alive())
            self.assertEqual(results, {'row': row})
            self.assertTrue(client._closing)

    def test_reentrant_close_in_predicate_cannot_consume_notification(self):
        with owned_client() as (client, read_fd):
            row = {'method': 'fixture/reentrant-close'}
            with client._condition: client._notifications.append(row)
            def predicate(value):
                # Reader EOF cannot acquire this same condition until predicate
                # returns. A close timeout must not resume cached publication.
                with self.assertRaises(TimeoutError): client.close(timeout=.01)
                return True
            with self.assertRaises(AppServerError):
                client.wait_notification(predicate, timeout=1)
            self.assertEqual(list(client._notifications), [row])

    def test_request_and_notification_wait_stop_before_blocked_reader_retires(self):
        for mode in ('request', 'notification'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as root, owned_client(
                    journal_path=Path(root)/'journal.jsonl') as (client, read_fd):
                waiting, recording = threading.Event(), threading.Event()
                errors = []
                original_wait = client._condition.wait
                original_record = client._record
                def condition_wait(timeout=None):
                    waiting.set()
                    return original_wait(timeout)
                def record(direction, message):
                    if direction == 'received': recording.set()
                    return original_record(direction, message)
                client._condition.wait = condition_wait
                client._record = record
                def wait():
                    try:
                        if mode == 'request': client.request('fixture/pending', timeout=90)
                        else: client.wait_notification(lambda row: False, timeout=90)
                    except BaseException as error: errors.append(error)
                worker = threading.Thread(target=wait)
                worker.start()
                held = False
                try:
                    self.assertTrue(waiting.wait(1))
                    client._journal_lock.acquire()
                    held = True
                    client.process.stdout.rows.put('{"method":"fixture/pulse"}\n')
                    self.assertTrue(recording.wait(1))
                    with self.assertRaisesRegex(TimeoutError, 'reader close timed out'):
                        client.close(timeout=.03)
                    worker.join(.2)
                    snapshot = {'case': mode, 'closing': client._closing,
                        'closed': client._closed, 'waiter_alive': worker.is_alive(),
                        'reader_alive': client._reader.is_alive(), 'journal_held': held,
                        'errors': [type(error).__name__ for error in errors]}
                    print(json.dumps(snapshot), flush=True)
                    self.assertFalse(worker.is_alive(), snapshot)
                    self.assertEqual(len(errors), 1)
                    self.assertIsInstance(errors[0], AppServerError)
                    self.assertFalse(client._closed)
                    self.assertTrue(client._reader.is_alive())
                finally:
                    if held: client._journal_lock.release()
                    worker.join(1)

    def test_planner_can_retry_close_after_condition_fence_timeout(self):
        with owned_client() as (client, read_fd):
            waiting, held, release = (threading.Event() for _ in range(3))
            errors = []
            planner = PersistentPlannerAdapter(client, model="mock", effort="low", cwd=".", base_instructions="")
            original_wait = client._condition.wait
            original_close = client.close
            def observe_wait(timeout=None):
                waiting.set()
                return original_wait(timeout)
            def short_close(timeout=5):
                return original_close(timeout=.05)
            with patch.object(client, "start_thread", return_value={"thread":{"id":"fixture-thread"}}), \
                 patch.object(client, "start_turn", return_value={"turn":{"id":"fixture-turn"}}), \
                 patch.object(client, "close", side_effect=short_close):
                planner.start_session()
                handle = planner.begin_turn("observe", output_schema={"type":"object"})
                client._condition.wait = observe_wait
                def waiter():
                    try: planner.await_turn(handle, timeout=2)
                    except BaseException as error: errors.append(error)
                worker = threading.Thread(target=waiter)
                def holder():
                    with client._condition:
                        held.set()
                        release.wait(2)
                blocker = threading.Thread(target=holder)
                worker.start()
                try:
                    self.assertTrue(waiting.wait(1))
                    blocker.start()
                    self.assertTrue(held.wait(1))
                    with self.assertRaisesRegex(TimeoutError, "condition fence timed out"):
                        planner.abort_pending_turn()
                    self.assertFalse(client._closing)
                    self.assertTrue(worker.is_alive())
                    release.set()
                    blocker.join(1)
                    self.assertEqual(planner.abort_pending_turn()["outcome"], "aborted")
                    worker.join(1)
                    self.assertFalse(worker.is_alive())
                    self.assertEqual(len(errors), 1)
                    self.assertIsInstance(errors[0], AppServerError)
                    self.assertTrue(planner._cancellation_requested)
                finally:
                    release.set()
                    if blocker.ident is not None: blocker.join(1)
                    worker.join(1)
                    client._condition.wait = original_wait

    def test_explicit_close_refuses_retained_notification_without_consuming_it(self):
        with owned_client() as (client, read_fd):
            row = {'method': 'turn/completed', 'params': {'threadId': 'old'}}
            with client._condition: client._notifications.append(row)
            client.close(timeout=1)
            with self.assertRaises(AppServerError):
                client.wait_notification(lambda value: True, timeout=1)
            self.assertEqual(list(client._notifications), [row])

    def test_real_pipe_planner_wait_stops_while_receive_journal_is_held(self):
        # A finite local Python JSONL peer, not installed Codex or a model.
        peer = '''import json,sys,time
from pathlib import Path
for line in sys.stdin:
 row=json.loads(line)
 method=row.get("method")
 if method=="thread/start": result={"thread":{"id":"mock-thread"}}
 elif method=="turn/start": result={"turn":{"id":"mock-turn"}}
 else: result={}
 if "id" in row: print(json.dumps({"id":row["id"],"result":result}),flush=True)
 if method=="turn/start":
  end=time.monotonic()+5
  while not Path(sys.argv[1]).exists() and time.monotonic()<end: time.sleep(.005)
  print(json.dumps({"method":"fixture/pulse"}),flush=True)
'''
        with tempfile.TemporaryDirectory() as root:
            gate = Path(root)/'release-peer'
            client = CodexAppServerClient([sys.executable, '-u', '-c', peer, str(gate)],
                                         journal_path=Path(root)/'journal.jsonl')
            planner = PersistentPlannerAdapter(client, model='mock', effort='low', cwd='.', base_instructions='')
            waiting, recording = threading.Event(), threading.Event()
            original_wait, original_record = client._condition.wait, client._record
            errors = []
            worker = None
            held = False
            try:
                planner.start_session()
                handle = planner.begin_turn('mock observation', output_schema={'type': 'object'})
                def condition_wait(timeout=None):
                    waiting.set()
                    return original_wait(timeout)
                def record(direction, message):
                    if direction == 'received': recording.set()
                    return original_record(direction, message)
                client._condition.wait, client._record = condition_wait, record
                def wait():
                    try: planner.await_turn(handle, timeout=90)
                    except BaseException as error: errors.append(error)
                worker = threading.Thread(target=wait)
                worker.start()
                self.assertTrue(waiting.wait(1))
                planner.invalidate_turn(handle)
                client._journal_lock.acquire()
                held = True
                gate.write_text('allow one pulse')
                self.assertTrue(recording.wait(1))
                with self.assertRaisesRegex(TimeoutError, 'reader close timed out'):
                    client.close(timeout=.03)
                worker.join(.2)
                snapshot = {'case': 'owned-python-peer-planner', 'peer_exited': client.process.poll() is not None,
                    'closing': client._closing, 'closed': client._closed,
                    'reader_alive': client._reader.is_alive(), 'waiter_alive': worker.is_alive(),
                    'journal_held': held, 'errors': [type(error).__name__ for error in errors],
                    'answer_invalidated': planner._cancellation_requested}
                print(json.dumps(snapshot), flush=True)
                self.assertFalse(worker.is_alive(), snapshot)
                self.assertEqual(len(errors), 1)
                self.assertIsInstance(errors[0], AppServerError)
                self.assertIsNotNone(client.process.poll())
                self.assertTrue(client._reader.is_alive())
                self.assertFalse(client._closed)
            finally:
                if held: client._journal_lock.release()
                client.close(timeout=1)
                if worker is not None: worker.join(1)
                print(json.dumps({'case': 'owned-python-peer-final-retirement',
                    'peer_returncode': client.process.poll(), 'reader_alive': client._reader.is_alive(),
                    'waiter_alive': worker.is_alive() if worker is not None else False,
                    'streams_closed': {name: getattr(client.process, name).closed
                                       for name in ('stdin', 'stdout', 'stderr')},
                    'journal_base64': base64.b64encode((Path(root)/'journal.jsonl').read_bytes()).decode('ascii')}),
                    flush=True)


if __name__ == '__main__': unittest.main()
