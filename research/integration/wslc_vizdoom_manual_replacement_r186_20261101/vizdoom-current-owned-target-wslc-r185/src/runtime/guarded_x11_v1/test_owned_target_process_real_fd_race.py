"""Real-child close/signal serialization; no X server or external process."""
import signal
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess


@unittest.skipUnless(sys.platform.startswith('linux'), 'Linux pidfd required')
class RealCloseRace(unittest.TestCase):
    def test_close_waits_for_inflight_pidfd_signal_after_child_exit(self):
        owner = OwnedTargetProcess.launch(
            [sys.executable, '-c', 'import time; time.sleep(60)'], disposable=True)
        owner._bound_xid = 123
        owner._bound_identity_digest = 'test-fixture-binding'
        entered, resume, close_started, close_done = (threading.Event() for _ in range(4))
        real_signal = signal.pidfd_send_signal
        errors = []
        receipts = []

        # Observe the close thread reaching the actual shared-lock acquisition.
        # The old implementation has no lock and signals just before close.
        if hasattr(owner, '_handle_lock'):
            class ObservedLock:
                def __init__(self, lock):
                    self.lock = lock
                def acquire(self, *args, **kwargs):
                    if threading.current_thread().name == 'test-close':
                        close_started.set()
                    return self.lock.acquire(*args, **kwargs)
                def release(self):
                    return self.lock.release()
                def __enter__(self):
                    self.acquire()
                    return self
                def __exit__(self, *args):
                    self.release()
            owner._handle_lock = ObservedLock(owner._handle_lock)

        def paused_signal(fd, signum):
            entered.set()
            if not resume.wait(5):
                raise TimeoutError('signal pause expired')
            return real_signal(fd, signum)

        def retire():
            try:
                receipts.append(owner.retire_bound_target(term_timeout_s=.1, kill_timeout_s=.1))
            except BaseException as error:
                errors.append(('retire', error))

        def close():
            if not hasattr(owner, '_handle_lock'):
                close_started.set()
            try:
                owner.close()
            except BaseException as error:
                errors.append(('close', error))
            finally:
                close_done.set()

        worker = closer = None
        try:
            with patch('runtime.guarded_x11_v1.owned_target_process.signal.pidfd_send_signal', paused_signal):
                worker = threading.Thread(target=retire, daemon=True)
                worker.start()
                self.assertTrue(entered.wait(5))
                owner._process.kill()
                owner._process.wait(timeout=3)
                closer = threading.Thread(target=close, name='test-close', daemon=True)
                closer.start()
                self.assertTrue(close_started.wait(2))
                self.assertFalse(close_done.wait(.25), 'closed the descriptor while a signal was pending')
                resume.set()
                worker.join(5)
                closer.join(5)
                self.assertFalse(worker.is_alive())
                self.assertFalse(closer.is_alive())
                self.assertEqual(errors, [])
                self.assertEqual(receipts[0]['status'], 'retired')
                self.assertEqual(receipts[0]['signal_attempts'][0]['status'], 'already_exited')
        finally:
            resume.set()
            if worker is not None:
                worker.join(5)
            if closer is not None:
                closer.join(5)
            if owner._process.poll() is None:
                owner._process.kill()
                owner._process.wait(timeout=3)
            if not owner._closed and not (worker and worker.is_alive()) and not (closer and closer.is_alive()):
                owner.close()


if __name__ == '__main__':
    unittest.main()
