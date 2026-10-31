"""Integration contract for private display ownership; Linux and Xvfb required."""
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import unittest

class PrivateDisplayOwnerTests(unittest.TestCase):
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
