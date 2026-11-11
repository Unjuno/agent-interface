import sys,unittest
from unittest.mock import patch
import win_job_spawn
from win_job_spawn import AtomicJobProcess

@unittest.skipUnless(sys.platform=='win32','Windows only')
class AtomicJobTests(unittest.TestCase):
    def test_suspended_child_is_in_job_before_resume_and_can_exit(self):
        p=AtomicJobProcess([sys.executable,'-c','import sys;sys.exit(7)'])
        try:
            p.start()
            self.assertTrue(p.in_job())
            self.assertTrue(p.suspended)
            p.resume()
            self.assertEqual(p.wait(5),7)
        finally:p.close()

    def test_close_terminates_only_owned_running_child(self):
        p=AtomicJobProcess([sys.executable,'-c','import time;time.sleep(30)'])
        try:
            p.start()
            p.resume()
            result=p.close(timeout_s=5)
            self.assertTrue(result['process_exited'])
            self.assertTrue(result['job_closed'])
            self.assertTrue(result['handles_closed'])
            self.assertEqual(result['errors'],[])
        finally:p.close()

    def test_close_error_preserves_job_and_child_for_retry(self):
        p=AtomicJobProcess([sys.executable,'-c','import time;time.sleep(30)'])
        try:
            p.start();job=p.job;child=p.process;original=win_job_spawn.k.CloseHandle
            def fail_job(handle):
                return False if handle==job else original(handle)
            with patch.object(win_job_spawn.k,'CloseHandle',side_effect=fail_job):
                first=p.close(timeout_s=2)
            self.assertFalse(first['job_closed'])
            self.assertEqual(p.job,job)
            self.assertEqual(p.process,child)
            second=p.close(timeout_s=5)
            self.assertTrue(second['job_closed'])
            self.assertTrue(second['process_exited'])
            self.assertTrue(second['handles_closed'])
            self.assertEqual(second['errors'],[])
        finally:p.close()

    def test_start_error_with_cleanup_failure_keeps_owner_reachable(self):
        p=AtomicJobProcess([sys.executable,'-c','import time;time.sleep(30)'])
        original=win_job_spawn.k.CloseHandle
        def fail_job(handle):
            return False if handle==p.job else original(handle)
        try:
            with patch.object(p,'in_job',return_value=False), patch.object(win_job_spawn.k,'CloseHandle',side_effect=fail_job), patch.object(win_job_spawn.k,'TerminateProcess',wraps=win_job_spawn.k.TerminateProcess) as terminate:
                with self.assertRaises(RuntimeError):p.start()
                self.assertEqual(terminate.call_count,1)
            self.assertIsNotNone(p.job)
            self.assertIsNotNone(p.process)
            result=p.close(timeout_s=5)
            self.assertTrue(result['job_closed'])
            self.assertTrue(result['process_exited'])
            self.assertTrue(result['handles_closed'])
        finally:p.close()

    def test_unexpected_resume_result_disables_retry(self):
        p=AtomicJobProcess([sys.executable,'-c','import time;time.sleep(30)'])
        try:
            p.start()
            with patch.object(win_job_spawn.k,'ResumeThread',return_value=0):
                with self.assertRaises(RuntimeError):p.resume()
            self.assertIsNone(p.suspended)
            with self.assertRaises(RuntimeError):p.resume()
            result=p.close(timeout_s=5)
            self.assertTrue(result['handles_closed'])
        finally:p.close()

    def test_failed_start_with_thread_handle_retained_cannot_resume(self):
        p=AtomicJobProcess([sys.executable,'-c','import time;time.sleep(30)'])
        original=win_job_spawn.k.CloseHandle
        def fail_thread(handle):
            return False if handle==p.thread else original(handle)
        try:
            with patch.object(p,'in_job',return_value=False), patch.object(win_job_spawn.k,'CloseHandle',side_effect=fail_thread):
                with self.assertRaises(RuntimeError):p.start()
            self.assertIsNotNone(p.thread)
            with self.assertRaises(RuntimeError):p.resume()
            self.assertTrue(p.close(timeout_s=5)['handles_closed'])
        finally:p.close()

    def test_interrupted_resume_is_not_retried(self):
        p=AtomicJobProcess([sys.executable,'-c','import time;time.sleep(30)'])
        try:
            p.start()
            with patch.object(win_job_spawn.k,'ResumeThread',side_effect=KeyboardInterrupt()):
                with self.assertRaises(KeyboardInterrupt):p.resume()
            self.assertIsNone(p.suspended)
            with self.assertRaises(RuntimeError):p.resume()
        finally:p.close()

    def test_bad_executable_does_not_create_a_child(self):
        p=AtomicJobProcess(['C:\\path-that-does-not-exist\\never.exe'])
        try:
            with self.assertRaises((OSError,ValueError)):p.start()
            self.assertIsNone(p.job)
            self.assertIsNone(p.process)
            self.assertIsNone(p.thread)
        finally:p.close()

if __name__=='__main__':unittest.main()
