import os,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
import win_job_spawn
from win_job_spawn import AtomicJobProcess

@unittest.skipUnless(sys.platform=='win32','Windows only')
class JobStdioTests(unittest.TestCase):
    def test_roundtrip_standard_streams_and_close(self):
        code="import sys; s=sys.stdin.buffer.readline(); sys.stdout.buffer.write(b'out:'+s); sys.stdout.buffer.flush(); sys.stderr.buffer.write(b'err\\n'); sys.stderr.buffer.flush()"
        p=AtomicJobProcess([sys.executable,'-u','-c',code],stdio=True)
        try:
            p.start();self.assertTrue(p.in_job());p.resume()
            p.stdin.write(b'hello\n');p.stdin.close()
            self.assertEqual(p.wait(5),0)
            self.assertEqual(p.stdout.read(),b'out:hello\n')
            self.assertEqual(p.stderr.read(),b'err\n')
            self.assertTrue(p.close()['kernel_handles_closed'])
            self.assertTrue(p.close_streams()['streams_closed'])
            self.assertTrue(p.close()['handles_closed'])
        finally:
            p.close();p.close_streams()

    def test_explicit_cwd_and_unicode_environment_reach_child(self):
        with tempfile.TemporaryDirectory() as root:
            d=str(Path(root)/'試験 cwd');Path(d).mkdir()
            env=dict(os.environ);env['AI_TASK_ENV']='試験-value'
            code="import os,sys;sys.stdout.buffer.write((os.getcwd()+'\\n'+os.environ['AI_TASK_ENV']+'\\n').encode('utf-8'))"
            p=AtomicJobProcess([sys.executable,'-u','-c',code],stdio=True,cwd=d,environment=env)
            try:
                p.start();p.resume();self.assertEqual(p.wait(5),0)
                lines=p.stdout.read().decode('utf-8').splitlines()
                self.assertEqual(os.path.normcase(lines[0]),os.path.normcase(d))
                self.assertEqual(lines[1],'試験-value')
            finally:p.close();p.close_streams()

    def test_duplicate_case_environment_rejected_before_start(self):
        with self.assertRaises(ValueError):
            AtomicJobProcess([sys.executable],environment={'TEST':'a','test':'b'})

    def test_descendant_holds_stdout_until_job_is_closed(self):
        child="import time; print('grandchild',flush=True); time.sleep(30)"
        code="import subprocess,sys,time; subprocess.Popen([sys.executable,'-u','-c',%r],close_fds=False); print('worker',flush=True); time.sleep(.5)" % child
        p=AtomicJobProcess([sys.executable,'-u','-c',code],stdio=True)
        seen=[];both=threading.Event();done=threading.Event();state={'eof':False,'errors':[]}
        def reader():
            try:
                for line in p.stdout:
                    seen.append(line.strip())
                    if b'worker' in seen and b'grandchild' in seen:both.set()
                state['eof']=True
            except BaseException as exc:state['errors'].append(type(exc).__name__)
            finally:done.set()
        thread=None
        try:
            p.start();p.resume();thread=threading.Thread(target=reader,daemon=True);thread.start()
            self.assertTrue(both.wait(8),'both processes did not report ready')
            self.assertEqual(p.wait(5),0)
            self.assertFalse(done.is_set(),'grandchild should still hold stdout after worker exit')
            receipt=p.close(timeout_s=5)
            self.assertTrue(receipt['job_closed'])
            self.assertTrue(receipt['process_exited'])
            self.assertTrue(done.wait(5),'stdout reader did not end')
            thread.join(1);self.assertFalse(thread.is_alive())
            self.assertTrue(state['eof'],'reader did not observe EOF')
            self.assertEqual(state['errors'],[])
            self.assertTrue(p.close_streams()['streams_closed'])
        finally:
            p.close()
            if thread is None or not thread.is_alive():p.close_streams()

    def test_failed_raw_close_is_retained_as_unknown_without_retry(self):
        p=AtomicJobProcess([sys.executable,'-c','import time;time.sleep(30)'],stdio=True)
        original=os.close;failed=[]
        def fail_once(fd):
            if not failed:
                failed.append(fd)
                raise OSError('injected close failure before close')
            return original(fd)
        try:
            with patch.object(win_job_spawn.os,'close',side_effect=fail_once):
                with self.assertRaises(OSError):p.start()
            self.assertEqual(p._unknown_raw_fds,set(failed))
            self.assertFalse(p.close()['handles_closed'])
            self.assertFalse(p.close_streams()['streams_closed'])
        finally:
            p.close();p.close_streams()
            for fd in failed:original(fd)

    def test_known_pre_fdopen_failure_cleans_up_pipes(self):
        p=AtomicJobProcess([sys.executable,'-c','pass'],stdio=True)
        original=os.fdopen;calls=[]
        def fail_before_transfer(*args,**kwargs):
            calls.append(1)
            if len(calls)==2:raise OSError('injected before fdopen')
            return original(*args,**kwargs)
        try:
            with patch.object(win_job_spawn.os,'fdopen',side_effect=fail_before_transfer):
                with self.assertRaises(OSError):p.start()
            self.assertTrue(p.close()['handles_closed'])
            self.assertTrue(p.close_streams()['streams_closed'])
        finally:p.close();p.close_streams()

    def test_start_failure_closes_created_pipes(self):
        p=AtomicJobProcess(['C:\\path-that-does-not-exist\\never.exe'],stdio=True)
        try:
            with self.assertRaises(OSError):p.start()
            self.assertTrue(p.close_streams()['streams_closed'])
            self.assertTrue(p.close()['handles_closed'])
        finally:
            p.close();p.close_streams()

if __name__=='__main__':unittest.main()
