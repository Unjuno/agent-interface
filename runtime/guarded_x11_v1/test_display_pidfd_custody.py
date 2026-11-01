import os, select, tempfile, unittest, threading, time
from unittest.mock import patch
from pathlib import Path
from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner

class Custody(unittest.TestCase):
    def test_duplicate_remains_bound_and_detects_retirement(self):
        with tempfile.TemporaryDirectory() as d:
            owner=PrivateDisplayOwner(Path(d)/'display')
            fd=None
            try:
                owner.start(timeout_s=5)
                fd,pid=owner.duplicate_server_pidfd(timeout_s=1)
                fields=dict(line.split(':',1) for line in Path('/proc/self/fdinfo',str(fd)).read_text().splitlines() if ':' in line)
                self.assertEqual(int(fields['Pid']),pid)
                poll=select.poll();poll.register(fd,select.POLLIN|select.POLLHUP|select.POLLERR)
                self.assertFalse(poll.poll(0))
                self.assertEqual(owner.close(timeout_s=3)['status'],'retired')
                self.assertTrue(poll.poll(1000))
                with self.assertRaises(RuntimeError): owner.duplicate_server_pidfd(timeout_s=1)
            finally:
                if fd is not None:os.close(fd)
                owner.close(timeout_s=3)

    def test_close_waits_for_real_duplication_in_progress(self):
        with tempfile.TemporaryDirectory() as d:
            owner=PrivateDisplayOwner(Path(d)/'display');owner.start(timeout_s=5)
            entered=threading.Event();resume=threading.Event();closed=threading.Event()
            duplicate=[]; errors=[]; real_dup=os.dup
            def paused_dup(fd):
                entered.set()
                if not resume.wait(3): raise RuntimeError('fixture timeout')
                return real_dup(fd)
            def duplicator():
                try: duplicate.append(owner.duplicate_server_pidfd(timeout_s=1))
                except BaseException as e:errors.append(repr(e))
            def closer():
                try: owner.close(timeout_s=3)
                except BaseException as e:errors.append(repr(e))
                finally: closed.set()
            try:
                with patch('runtime.guarded_x11_v1.private_display_owner.os.dup',side_effect=paused_dup):
                    t=threading.Thread(target=duplicator);t.start()
                    self.assertTrue(entered.wait(3))
                    c=threading.Thread(target=closer);c.start()
                    self.assertFalse(closed.wait(.15))
                    resume.set();t.join(3);c.join(3)
                self.assertFalse(t.is_alive());self.assertFalse(c.is_alive())
                self.assertEqual(errors,[]);self.assertTrue(closed.is_set());self.assertEqual(len(duplicate),1)
                fd,pid=duplicate[0]; poll=select.poll();poll.register(fd,select.POLLIN|select.POLLHUP|select.POLLERR)
                self.assertTrue(poll.poll(1000))
            finally:
                resume.set()
                for fd,_ in duplicate:os.close(fd)
                owner.close(timeout_s=3)

    def test_each_lock_timeout_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            owner=PrivateDisplayOwner(Path(d)/'display');owner.start(timeout_s=5)
            try:
                for lock in (owner._cleanup_lock,owner._lock):
                    with self.subTest(lock=repr(lock)):
                        held=threading.Event();release=threading.Event()
                        def holder():
                            with lock:
                                held.set();release.wait(3)
                        t=threading.Thread(target=holder);t.start();self.assertTrue(held.wait(1))
                        try:
                            start=time.monotonic()
                            with self.assertRaises(TimeoutError):owner.duplicate_server_pidfd(timeout_s=.1)
                            self.assertLess(time.monotonic()-start,1.0)
                        finally:release.set();t.join(2)
                        self.assertFalse(t.is_alive())
                fd,pid=owner.duplicate_server_pidfd(timeout_s=1);os.close(fd)
            finally:owner.close(timeout_s=3)

    def test_late_duplicate_is_closed_not_returned(self):
        with tempfile.TemporaryDirectory() as d:
            owner=PrivateDisplayOwner(Path(d)/'display');owner.start(timeout_s=5)
            real_dup=os.dup;created=[]
            def delayed(fd):
                duplicate=real_dup(fd);created.append(duplicate);time.sleep(.15);return duplicate
            try:
                with patch('runtime.guarded_x11_v1.private_display_owner.os.dup',side_effect=delayed):
                    with self.assertRaises(TimeoutError):owner.duplicate_server_pidfd(timeout_s=.05)
                self.assertEqual(len(created),1)
                with self.assertRaises(OSError):os.fstat(created[0])
                fd,pid=owner.duplicate_server_pidfd(timeout_s=1);os.close(fd)
            finally:owner.close(timeout_s=3)

    def test_invalid_deadlines_rejected(self):
        owner=PrivateDisplayOwner('/unused')
        for value in (0,-1,float('nan'),float('inf'),True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):owner.duplicate_server_pidfd(timeout_s=value)

    def test_unstarted_owner_refuses(self):
        owner=PrivateDisplayOwner('/unused')
        with self.assertRaises(RuntimeError):owner.duplicate_server_pidfd(timeout_s=1)

if __name__=='__main__':unittest.main(verbosity=2)
