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
from unittest.mock import patch

class PrivateDisplayOwnerTests(unittest.TestCase):
    def test_invalid_timeouts_are_rejected_before_start_or_cleanup(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        for value in (0,-1,True,float('nan'),float('inf')):
            with self.subTest(value=value),tempfile.TemporaryDirectory() as directory:
                owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner')
                for method in ('start','retire','close'):
                    with self.assertRaises(ValueError):getattr(owner,method)(timeout_s=value)
                self.assertIsNone(owner._process);self.assertFalse(owner.directory.exists())

    def test_close_and_retire_report_unknown_when_locks_are_held(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        for method in ('close','retire'):
            for lock_name in ('_cleanup_lock','_lock'):
                with self.subTest(method=method,lock=lock_name), tempfile.TemporaryDirectory() as directory:
                    owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner');owner.start(timeout_s=5)
                    lock=getattr(owner,lock_name);lock.acquire();results=[];errors=[]
                    def invoke():
                        try:results.append(getattr(owner,method)(timeout_s=.1))
                        except Exception as e:errors.append(repr(e))
                    worker=threading.Thread(target=invoke);worker.start()
                    try:
                        worker.join(.8)
                        self.assertFalse(worker.is_alive(),'operation did not honor lock wait budget')
                        self.assertEqual(errors,[]);self.assertEqual(results,[{'status':'unknown'}])
                        self.assertIsNone(owner._process.poll())
                    finally:
                        lock.release();worker.join(4);owner.close()

    def test_retire_during_start_does_not_publish_dead_display(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as directory:
            owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner');entered=threading.Event();resume=threading.Event();observed={};calls=[]
            original=owner._auth_add
            def gated_auth(*args):
                calls.append(1)
                if len(calls)==2:
                    entered.set()
                    if not resume.wait(3):raise RuntimeError('fixture timeout')
                return original(*args)
            owner._auth_add=gated_auth
            def launch():
                try:observed['session']=owner.start(timeout_s=5)
                except Exception as e:observed['error']=type(e).__name__
            worker=threading.Thread(target=launch);worker.start()
            try:
                self.assertTrue(entered.wait(3));result=owner.retire(timeout_s=3)
                resume.set();worker.join(5)
                self.assertFalse(worker.is_alive());self.assertNotIn('session',observed)
                self.assertIn('error',observed);self.assertIn(result['status'],('pending','retired'))
                self.assertIsNotNone(owner._process.poll())
            finally:
                resume.set();worker.join(5);owner.close()

    def test_simultaneous_closes_do_not_double_close_pidfd(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as directory:
            owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner');owner.start(timeout_s=5)
            target_fd=owner._pidfd;first_entered=threading.Event();second_entered=threading.Event();release=threading.Event()
            original_close=os.close;counter=[];errors=[];results=[]
            def gated_close(fd):
                if fd==target_fd:
                    counter.append(1)
                    if len(counter)==1:
                        first_entered.set()
                        if not release.wait(3):raise RuntimeError('fixture timeout')
                    else:second_entered.set()
                return original_close(fd)
            def close():
                try:results.append(owner.close())
                except Exception as e:errors.append(repr(e))
            first=threading.Thread(target=close);second=threading.Thread(target=close)
            try:
                with patch('os.close',side_effect=gated_close):
                    first.start();self.assertTrue(first_entered.wait(3));second.start()
                    second_entered.wait(.3);release.set();first.join(3);second.join(3)
                self.assertFalse(first.is_alive());self.assertFalse(second.is_alive())
                self.assertFalse(second_entered.is_set(),'same pidfd closed twice')
                self.assertEqual(errors,[]);self.assertEqual(results,[{'status':'retired'},{'status':'retired'}])
            finally:
                release.set();first.join(3)
                if second.ident is not None:second.join(3)
                if owner._pidfd==target_fd and counter:owner._pidfd=None
                owner.close()

    def test_pidfd_open_failure_retains_child_for_later_reap(self):
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as directory:
            owner=PrivateDisplayOwner(pathlib.Path(directory)/'owner');original_wait=subprocess.Popen.wait
            def timeout_xvfb(process,timeout=None):
                if process.args[0]=='Xvfb':raise subprocess.TimeoutExpired('Xvfb',timeout)
                return original_wait(process,timeout=timeout)
            try:
                with patch('os.pidfd_open',side_effect=OSError('injected pidfd failure')), patch.object(subprocess.Popen,'wait',timeout_xvfb):
                    with self.assertRaisesRegex(RuntimeError,'cleanup unconfirmed'):owner.start(timeout_s=5)
                self.assertIsNotNone(owner._process);self.assertIsNone(owner._pidfd);self.assertFalse(owner._retired)
                try:result=owner.close()
                except RuntimeError as e:self.fail('owned child could not be reaped: '+str(e))
                self.assertEqual(result,{'status':'retired'})
            finally:
                if owner._process is not None and owner._process.poll() is None:
                    owner._process.kill();owner._process.wait(timeout=3)

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
