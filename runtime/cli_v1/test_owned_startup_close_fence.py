import tempfile
import threading
import unittest
from unittest.mock import patch
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner

class Conn:
    def close(self): pass
    def poll(self, timeout): return True
    def recv(self): return {'ok': True, 'snapshot': {'state': 'open'}}

class Process:
    pid = None
    exitcode = None
    def __init__(self, entered, resume):
        self.entered, self.resume, self.alive, self.started = entered, resume, False, False
    def start(self):
        self.started, self.alive, self.pid = True, True, 123
        self.entered.set()
        if not self.resume.wait(5): raise RuntimeError('gate timed out')
    def is_alive(self): return self.alive
    def terminate(self): self.alive, self.exitcode = False, -15
    def join(self, timeout=None): pass

class Context:
    def __init__(self, process, before_alloc=None): self.process, self.before_alloc = process, before_alloc
    def Pipe(self, duplex=True):
        if self.before_alloc:
            entered,resume=self.before_alloc; self.before_alloc=None; entered.set()
            if not resume.wait(5): raise RuntimeError('allocation gate timed out')
        return Conn(), Conn()
    def RawArray(self, kind, size): return bytearray(size)
    def Process(self, **kwargs): return self.process

class StartupCloseFenceTests(unittest.TestCase):
    def exercise(self, allocation_gate):
        entered,resume=threading.Event(),threading.Event()
        spawned,spawn_resume=threading.Event(),threading.Event()
        if allocation_gate: spawn_resume.set()
        else: entered,resume=spawned,spawn_resume
        process=Process(spawned,spawn_resume)
        context=Context(process,(entered,resume) if allocation_gate else None)
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            errors=[]
            def start():
                try: owner._ensure_started()
                except Exception as error: errors.append(error)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=context):
                t=threading.Thread(target=start); t.start()
                try:
                    self.assertTrue(entered.wait(5), 'startup gate was not reached')
                    snapshot=owner.snapshot()['owner_process']
                    self.assertIsNone(snapshot['alive'], 'unregistered child liveness is unknown')
                    self.assertIsNone(snapshot['retired'])
                    result=owner.close()
                    self.assertIsNot(result.get('verified'),True, 'startup in progress cannot be verified closed')
                    self.assertNotEqual(result.get('status'),'closed')
                    self.assertIsNone(owner.close_report, 'busy result must not become canonical close')
                finally:
                    resume.set(); spawn_resume.set(); t.join(5)
                self.assertFalse(t.is_alive())
                self.assertTrue(errors, 'late startup must not be admitted after close request')
                self.assertFalse(process.is_alive(), 'resumed owned child must be retired')
                self.assertNotEqual(owner.state, 'open')
    def test_completed_start_cannot_clear_next_start_admission(self):
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            first_released, release_first = threading.Event(), threading.Event()
            second_entered, release_second = threading.Event(), threading.Event()
            underlying = threading.Lock()
            class GateLock:
                def __enter__(self): underlying.acquire(); return self
                def __exit__(self, *args):
                    gate = threading.current_thread().name == 'first-start' and not owner._startup_in_progress
                    underlying.release()
                    if gate and not first_released.is_set():
                        first_released.set()
                        if not release_first.wait(5): raise RuntimeError('first gate timeout')
            owner._lifecycle_lock=GateLock()
            errors=[]
            def fake_start():
                if threading.current_thread().name == 'second-start':
                    second_entered.set()
                    if not release_second.wait(5): raise RuntimeError('second gate timeout')
            def invoke():
                try: owner._ensure_started()
                except Exception as error: errors.append(error)
            with patch.object(owner, '_ensure_started_impl', side_effect=fake_start):
                first=threading.Thread(target=invoke,name='first-start')
                second=threading.Thread(target=invoke,name='second-start')
                first.start()
                try:
                    self.assertTrue(first_released.wait(5))
                    second.start(); self.assertTrue(second_entered.wait(5))
                    release_first.set(); first.join(5); self.assertFalse(first.is_alive())
                    self.assertIs(owner.close()['verified'], False)
                finally:
                    release_first.set(); release_second.set(); first.join(5)
                    if second.ident is not None: second.join(5)
                self.assertFalse(second.is_alive())

    def test_retire_before_process_handle_is_available_stays_unconfirmed(self):
        entered,resume=threading.Event(),threading.Event()
        spawned,spawn_resume=threading.Event(),threading.Event();spawn_resume.set()
        child=Process(spawned,spawn_resume);errors=[]
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            def start():
                try: owner._ensure_started()
                except Exception as error: errors.append(error)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=Context(child,(entered,resume))):
                t=threading.Thread(target=start);t.start()
                try:
                    self.assertTrue(entered.wait(5))
                    report=owner.retire('shutdown while allocation is gated')
                    self.assertFalse(report['retired'])
                    self.assertIsNone(report['exitcode'])
                finally:
                    resume.set();t.join(5)
            self.assertFalse(t.is_alive())
            self.assertTrue(errors)
            self.assertFalse(child.started, 'shutdown during allocation must prevent a later spawn')
            self.assertFalse(child.is_alive())

    def test_retire_during_start_reports_unknown_when_child_probe_raises(self):
        class Unreadable:
            pid=123
            def is_alive(self): raise OSError('process query failed')
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            owner._startup_in_progress=True
            owner._starting_process=Unreadable()
            result=owner.retire('shutdown')
            self.assertFalse(result['retired'])
            self.assertIsNone(result['exitcode'])
            self.assertIs(owner._process,owner._starting_process)
            self.assertTrue(owner._close_during_startup)
            self.assertTrue(owner.review_required)
            snapshot=owner.snapshot()['owner_process']
            self.assertIsNone(snapshot['alive'])
            self.assertIsNone(snapshot['retired'])
            self.assertIsNone(snapshot['liveness_observed_monotonic_ns'])

    def test_retire_during_start_reports_unknown_when_pid_probe_raises(self):
        class Unreadable:
            @property
            def pid(self): raise RuntimeError('pid unavailable')
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            owner._startup_in_progress=True
            owner._starting_process=Unreadable()
            result=owner.retire('shutdown')
            self.assertFalse(result['retired'])
            self.assertIsNone(result['exitcode'])
            self.assertIsNone(owner._process)
            self.assertTrue(owner._close_during_startup)
            self.assertTrue(owner.review_required)

    def test_close_before_start_rejects_later_start(self):
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            self.assertTrue(owner.close()['verified'])
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context') as get_context:
                with self.assertRaises(RuntimeError): owner._ensure_started()
                get_context.assert_not_called()
    def test_start_raises_after_spawn_retains_and_retires_exact_child(self):
        class SpawnThenFail(Process):
            def start(self):
                self.started, self.alive, self.pid = True, True, 123
                raise OSError('failed after child started')
        child=SpawnThenFail(threading.Event(),threading.Event())
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=Context(child)):
                with self.assertRaises(OSError): owner._ensure_started()
            self.assertIs(owner._process,child)
            self.assertFalse(child.is_alive())
            self.assertIsNot(owner.close()['verified'],True)

    def test_late_start_retirement_failure_keeps_owner_failed(self):
        class BrokenRetire(Process):
            def terminate(self): raise RuntimeError('retirement failed')
        entered,resume=threading.Event(),threading.Event()
        child=BrokenRetire(entered,resume); errors=[]
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            def start():
                try: owner._ensure_started()
                except Exception as error: errors.append(error)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=Context(child)):
                t=threading.Thread(target=start);t.start()
                try:
                    self.assertTrue(entered.wait(5))
                    self.assertFalse(owner.close()['verified'])
                finally:
                    resume.set();t.join(5)
            self.assertFalse(t.is_alive())
            self.assertTrue(errors)
            self.assertEqual(owner.state,'failed')
            self.assertTrue(owner.review_required)
            self.assertIs(owner._process,child)

    def test_failed_retirement_preserves_original_start_error_and_child(self):
        class SpawnThenFail(Process):
            def start(self):
                self.started, self.alive, self.pid = True, True, 123
                raise OSError('original start error')
            def terminate(self): raise RuntimeError('retirement failed')
        child=SpawnThenFail(threading.Event(),threading.Event())
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=Context(child)):
                with self.assertRaisesRegex(OSError, 'original start error') as caught: owner._ensure_started()
            self.assertIs(owner._process,child)
            self.assertTrue(child.is_alive())
            self.assertIn('RuntimeError', ' '.join(getattr(caught.exception,'__notes__',[])))
            self.assertTrue(owner.review_required)

    def test_second_pipe_failure_closes_previously_allocated_handles(self):
        class Tracked:
            def __init__(self): self.closed=False
            def close(self): self.closed=True
        class FailingContext:
            def __init__(self): self.calls=0; self.first=(Tracked(),Tracked())
            def Pipe(self, duplex=True):
                self.calls+=1
                if self.calls==1:return self.first
                raise OSError('second pipe failed')
        context=FailingContext()
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=context):
                with self.assertRaisesRegex(OSError,'second pipe failed'):owner._ensure_started()
            self.assertTrue(all(handle.closed for handle in context.first))
            self.assertIsNot(owner.close()['verified'],True)

    def test_ambiguous_allocation_handle_close_is_retained_without_retry(self):
        class Tracked:
            def __init__(self, fail=False): self.calls=0; self.fail=fail
            def close(self):
                self.calls+=1
                if self.fail:raise OSError('ambiguous close')
        class FailingContext:
            def __init__(self): self.calls=0; self.first=(Tracked(True),Tracked())
            def Pipe(self, duplex=True):
                self.calls+=1
                if self.calls==1:return self.first
                raise OSError('second pipe failed')
        context=FailingContext()
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=context):
                with self.assertRaisesRegex(OSError,'second pipe failed') as caught:owner._ensure_started()
            self.assertEqual([h.calls for h in context.first],[1,1])
            self.assertIn(context.first[0],owner._unclosed_startup_handles)
            self.assertEqual(owner.snapshot()['startup_handle_cleanup'],
                             {'status':'unknown','unconfirmed_handles':1})
            self.assertIn('OSError',' '.join(getattr(caught.exception,'__notes__',[])))
            self.assertIsNot(owner.close()['verified'],True)
            self.assertEqual(context.first[0].calls,1)

    def test_start_error_survives_unreadable_process_identity(self):
        class UnreadableAfterStart:
            @property
            def pid(self): raise RuntimeError('identity unavailable')
            def start(self): raise OSError('original start error')
        child=UnreadableAfterStart()
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=Context(child)):
                with self.assertRaisesRegex(OSError,'original start error') as caught: owner._ensure_started()
            self.assertIs(owner._starting_process,child)
            self.assertIn('RuntimeError',' '.join(getattr(caught.exception,'__notes__',[])))
            self.assertIsNot(owner.close()['verified'],True)

    def test_post_spawn_child_pipe_close_error_is_not_retried(self):
        class Tracked(Conn):
            def __init__(self, fail=False): self.calls=0; self.fail=fail
            def close(self):
                self.calls+=1
                if self.fail:raise OSError('child close ambiguous')
        class PipeContext(Context):
            def __init__(self, process):
                super().__init__(process);self.first=(Tracked(),Tracked(True));self.second=(Tracked(),Tracked());self.calls=0
            def Pipe(self, duplex=True):
                self.calls+=1
                return self.first if self.calls==1 else self.second
        child=Process(threading.Event(),threading.Event()); child.resume.set()
        context=PipeContext(child)
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=context):
                with self.assertRaisesRegex(OSError,'child close ambiguous'):owner._ensure_started()
            self.assertEqual(context.first[1].calls,1)
            self.assertIn(context.first[1],owner._unclosed_startup_handles)
            self.assertEqual([context.first[0].calls,context.second[0].calls,context.second[1].calls],[1,1,1])
            self.assertFalse(child.is_alive())
            self.assertIsNot(owner.close()['verified'],True)

    def test_failed_partial_allocation_does_not_report_verified_close(self):
        class FailingContext:
            def Pipe(self, duplex=True): raise OSError('allocation failed')
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=FailingContext()):
                with self.assertRaises(OSError): owner._ensure_started()
            self.assertIsNot(owner.close().get('verified'), True)

    def test_unconfirmed_startup_handle_prevents_verified_close_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            owner = OwnedGuardedSessionOwner({'app': 20}, root)
            child = Process(threading.Event(), threading.Event())
            child.pid, child.exitcode = 123, 0
            owner._process = child
            owner._unclosed_startup_handles.append(Conn())
            receipt = {'status': 'closed', 'connection_close_attempted': True,
                       'release_attempted': False}
            with patch.object(owner, '_request_locked', return_value=receipt):
                result = owner.close()
            self.assertFalse(result['verified'])
            self.assertEqual(result['cleanup_status'], 'UNKNOWN')

    def test_close_during_child_start_is_not_verified(self): self.exercise(False)
    def test_close_during_pre_spawn_allocation_is_not_verified(self): self.exercise(True)

if __name__=='__main__': unittest.main()
