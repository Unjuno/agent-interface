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
    pid = 123
    exitcode = None
    def __init__(self, entered, resume): self.entered, self.resume, self.alive = entered, resume, True
    def start(self):
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

    def test_close_before_start_rejects_later_start(self):
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            self.assertTrue(owner.close()['verified'])
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context') as get_context:
                with self.assertRaises(RuntimeError): owner._ensure_started()
                get_context.assert_not_called()
    def test_start_raises_after_spawn_retains_and_retires_exact_child(self):
        class SpawnThenFail(Process):
            def start(self): raise OSError('failed after child started')
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
            def start(self): raise OSError('original start error')
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

    def test_failed_partial_allocation_does_not_report_verified_close(self):
        class FailingContext:
            def Pipe(self, duplex=True): raise OSError('allocation failed')
        with tempfile.TemporaryDirectory() as root:
            owner=OwnedGuardedSessionOwner({'app':20},root)
            with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context',return_value=FailingContext()):
                with self.assertRaises(OSError): owner._ensure_started()
            self.assertIsNot(owner.close().get('verified'), True)
    def test_close_during_child_start_is_not_verified(self): self.exercise(False)
    def test_close_during_pre_spawn_allocation_is_not_verified(self): self.exercise(True)

if __name__=='__main__': unittest.main()
