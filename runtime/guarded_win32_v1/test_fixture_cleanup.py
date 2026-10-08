import pathlib, sys, subprocess, tempfile, types, unittest
from unittest.mock import patch
from runtime.backends.win32_v1 import test_integration as fixture_module
class FixtureCleanupTests(unittest.TestCase):
    def test_setup_launch_failure_runs_registered_cleanup(self):
        class FailedLaunch(unittest.TestCase):
            setUpClass=classmethod(fixture_module.Win32IntegrationTests.setUpClass.__func__)
            _cleanup_fixture=classmethod(fixture_module.Win32IntegrationTests._cleanup_fixture.__func__)
            def test_unused(self): self.fail('setup must fail first')
        result=unittest.TestResult()
        with patch.object(fixture_module.subprocess,'Popen',side_effect=OSError('controlled launch failure')):
            unittest.defaultTestLoader.loadTestsFromTestCase(FailedLaunch).run(result)
        self.assertEqual(len(result.errors),1)
        self.assertIn('controlled launch failure',result.errors[0][1])
        self.assertFalse(pathlib.Path(FailedLaunch.tmp.name).exists())
    def test_live_owned_child_is_killed_and_reaped_after_timeout(self):
        child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],stderr=subprocess.PIPE)
        tmp=tempfile.TemporaryDirectory();root=pathlib.Path(tmp.name)
        holder=types.SimpleNamespace(proc=child,tmp=tmp)
        real_wait=child.wait;calls=[]
        def timeout_once(*args,**kwargs):
            calls.append(kwargs.get('timeout'))
            if len(calls)==1: raise subprocess.TimeoutExpired(child.args,kwargs.get('timeout'))
            return real_wait(*args,**kwargs)
        try:
            with patch.object(child,'wait',side_effect=timeout_once):
                fixture_module.Win32IntegrationTests._cleanup_fixture.__func__(holder)
            self.assertEqual(len(calls),2);self.assertIsNotNone(child.poll())
            self.assertTrue(child.stderr.closed);self.assertFalse(root.exists())
        finally:
            if child.poll() is None: child.kill()
            child.wait(timeout=3)
            if not child.stderr.closed: child.stderr.close()
            tmp.cleanup()
    def test_cleanup_before_process_creation_releases_temporary_directory(self):
        tmp=tempfile.TemporaryDirectory();root=pathlib.Path(tmp.name)
        try:
            fixture_module.Win32IntegrationTests._cleanup_fixture.__func__(types.SimpleNamespace(tmp=tmp))
            self.assertFalse(root.exists())
        finally: tmp.cleanup()
if __name__=='__main__': unittest.main()
