"""Integration contract for private display ownership; Linux and Xvfb required."""
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

class PrivateDisplayOwnerTests(unittest.TestCase):
    def test_start_failure_unconfirmed_reap_is_not_reported_retired(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as directory:
            owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner');entered=threading.Event();resume=threading.Event();observed={};calls=[]
            original_auth=owner._auth_add
            def blocked_auth(*args):
                calls.append(1)
                if len(calls)==2:
                    entered.set()
                    if not resume.wait(3):raise RuntimeError('fixture timeout')
                return original_auth(*args)
            owner._auth_add=blocked_auth
            def launch():
                try:owner.start(timeout_s=5)
                except Exception as e:observed['error']=str(e)
            worker=threading.Thread(target=launch);worker.start();original_wait=None;timeouts=[]
            try:
                self.assertTrue(entered.wait(3));original_wait=owner._process.wait
                def timeout_wait(timeout=None):
                    timeouts.append(timeout)
                    if timeout is None:raise AssertionError('unbounded wait')
                    raise subprocess.TimeoutExpired('Xvfb',timeout)
                owner._process.wait=timeout_wait
                self.assertEqual(owner.close(),{'status':'pending'});resume.set();worker.join(5)
                self.assertFalse(worker.is_alive());self.assertTrue(timeouts);self.assertIsNotNone(timeouts[0])
                self.assertIn('cleanup unconfirmed',observed.get('error',''))
                self.assertFalse(owner._retired)
            finally:
                resume.set();worker.join(5)
                if original_wait is not None:owner._process.wait=original_wait
                owner.close()

    def test_expired_startup_does_not_publish_display(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as directory:
            owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner');original=owner._auth_add;calls=[]
            def slow_auth(*args):
                calls.append(1)
                if len(calls)==2:time.sleep(.6)
                return original(*args)
            owner._auth_add=slow_auth
            try:
                with self.assertRaises(TimeoutError):owner.start(timeout_s=.5)
                self.assertIsNone(owner._session)
                self.assertIsNotNone(owner._process.poll())
            finally:owner.close()

    def test_close_during_start_prevents_later_server_launch(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as directory:
            owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner')
            entered=threading.Event();resume=threading.Event();observed={}
            original=owner._auth_add
            def blocked_auth(*args):
                entered.set()
                if not resume.wait(3):raise RuntimeError('fixture timeout')
                return original(*args)
            owner._auth_add=blocked_auth
            def launch():
                try:observed['session']=owner.start(timeout_s=5)
                except Exception as e:observed['error']=type(e).__name__
            worker=threading.Thread(target=launch);worker.start()
            try:
                self.assertTrue(entered.wait(2));self.assertEqual(owner.close(),{'status':'pending'});resume.set();worker.join(5)
                self.assertFalse(worker.is_alive())
                self.assertNotIn('session',observed)
                self.assertIn('error',observed)
                self.assertTrue(owner._process is None or owner._process.poll() is not None)
            finally:
                resume.set();worker.join(5);owner.close()

    def test_close_after_spawn_prevents_publishing_and_reaps_server(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as directory:
            owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner')
            entered=threading.Event();resume=threading.Event();observed={};calls=[]
            original=owner._auth_add
            def blocked_auth(*args):
                calls.append(1)
                if len(calls)==2:
                    entered.set()
                    if not resume.wait(3):raise RuntimeError('fixture timeout')
                return original(*args)
            owner._auth_add=blocked_auth
            def launch():
                try:observed['session']=owner.start(timeout_s=5)
                except Exception as e:observed['error']=type(e).__name__
            worker=threading.Thread(target=launch);worker.start()
            try:
                self.assertTrue(entered.wait(3));self.assertIsNotNone(owner._process)
                self.assertEqual(owner.close(),{'status':'pending'});resume.set();worker.join(5)
                self.assertFalse(worker.is_alive());self.assertNotIn('session',observed)
                self.assertIn('error',observed);self.assertIsNotNone(owner._process.poll())
                self.assertEqual(owner.close(),{'status':'retired'})
            finally:
                resume.set();worker.join(5);owner.close()

    def test_launched_display_requires_cookie_and_retirement_closes_it(self):
        try:
            from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        except ImportError as e:
            self.fail('private display ownership is not implemented: '+str(e))
        with tempfile.TemporaryDirectory() as directory:
            owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner')
            try:
                session=owner.start(timeout_s=5)
                self.assertTrue(session.display.startswith(':'))
                self.assertEqual(os.stat(session.authority).st_mode & 0o777,0o600)
                script='from Xlib import display; d=display.Display(); d.sync(); d.close()'
                env=dict(os.environ,DISPLAY=session.display,XAUTHORITY=str(session.authority))
                accepted=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,timeout=3)
                self.assertEqual(accepted.returncode,0,accepted.stderr.decode(errors='replace'))
                env['XAUTHORITY']=str(pathlib.Path(directory)/'absent')
                refused=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,timeout=3)
                self.assertNotEqual(refused.returncode,0)
                result=owner.retire(timeout_s=3)
                self.assertEqual(result['status'],'retired')
                env['XAUTHORITY']=str(session.authority)
                after=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,timeout=3)
                self.assertNotEqual(after.returncode,0)
                self.assertEqual(owner.retire(timeout_s=3)['status'],'retired')
            finally: owner.close()

    def test_retiring_stopped_owned_display_leaves_other_display_running(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as directory:
            first=PrivateDisplayOwner(pathlib.Path(directory)/'first')
            second=PrivateDisplayOwner(pathlib.Path(directory)/'second')
            try:
                a=first.start(timeout_s=5); b=second.start(timeout_s=5)
                self.assertNotEqual(a.display,b.display)
                signal.pidfd_send_signal(first._pidfd,signal.SIGSTOP)
                self.assertEqual(first.retire(timeout_s=3)['status'],'retired')
                env=dict(os.environ,DISPLAY=b.display,XAUTHORITY=str(b.authority))
                result=subprocess.run([sys.executable,'-c','from Xlib import display; d=display.Display(); d.sync(); d.close()'],env=env,capture_output=True,timeout=3)
                self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
            finally:
                first.close();second.close()

if __name__=='__main__':unittest.main()
