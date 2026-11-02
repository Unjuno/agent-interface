import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lifecycle_launcher import run_attempt

class FakeDriver:
    def __init__(self, *, timeout=False, cleanup='confirmed'):
        self.timeout=timeout;self.cleanup=cleanup;self.calls=[]
    def prepare_host(self,allocation):return 'host-token'
    def prepare_container(self,allocation):return 'container-token'
    def start_host(self,token,allocation):self.calls.append('host_start')
    def start_container(self,token,allocation):self.calls.append('container_start')
    def wait_container(self,token,timeout):
        self.calls.append('container_wait')
        return {'status':'timeout','exit_code':None} if self.timeout else {'status':'exited','exit_code':0}
    def stop_host(self,token,timeout):self.calls.append('host_stop');return {'status':'exited','exit_code':0}
    def cleanup_container(self,token,timeout):self.calls.append('container_cleanup');return {'status':self.cleanup}
    def audit(self,allocation):self.calls.append('audit');return {'status':'passed','release_confirmed':True}

class LauncherTests(unittest.TestCase):
    def test_success_requires_confirmed_release_and_timings(self):
        with tempfile.TemporaryDirectory() as d:
            driver=FakeDriver();path=Path(d)/'run'
            result=run_attempt(path,{'run_id':'one'},driver,timeout_s=1)
            self.assertEqual(result['status'],'completed_scoped')
            self.assertEqual(result['input_release'],'confirmed')
            self.assertEqual(result['cleanup']['status'],'confirmed')
            self.assertEqual(driver.calls,['host_start','container_start','container_wait','host_stop','container_cleanup','audit'])
            self.assertGreaterEqual(result['events']['before_result_write_ns'],result['events']['started_ns'])
            self.assertEqual(json.loads((path/'result.json').read_text()),result)
    def test_timeout_stops_owned_resources_but_never_reports_success(self):
        with tempfile.TemporaryDirectory() as d:
            driver=FakeDriver(timeout=True,cleanup='unknown');path=Path(d)/'run'
            result=run_attempt(path,{'run_id':'two'},driver,timeout_s=1)
            self.assertEqual(result['status'],'incomplete')
            self.assertEqual(result['container']['status'],'timeout')
            self.assertEqual(result['cleanup']['status'],'unknown')
            self.assertEqual(result['input_release'],'UNKNOWN')
            self.assertNotIn('audit',driver.calls)
            self.assertEqual(driver.calls[-2:],['host_stop','container_cleanup'])
            self.assertTrue((path/'result.json').is_file())
    def test_partial_start_failure_is_unknown_and_host_is_stopped(self):
        class PartialStart(FakeDriver):
            def cleanup_container(self,token,timeout):self.calls.append('container_cleanup');return {'status':'unknown'}
            def start_container(self, token, allocation):
                self.calls.append('container_start')
                raise RuntimeError('start returned no handle')
        with tempfile.TemporaryDirectory() as d:
            driver=PartialStart();path=Path(d)/'run'
            result=run_attempt(path,{'run_id':'partial'},driver,timeout_s=1)
            self.assertEqual(result['status'],'incomplete')
            self.assertEqual(result['container']['status'],'unknown')
            self.assertEqual(result['cleanup']['status'],'unknown')
            self.assertIn('host_stop',driver.calls)
            self.assertIn('container_cleanup',driver.calls)
            self.assertNotIn('audit',driver.calls)

    def test_nonfinite_timeout_does_not_create_allocation(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'run'
            for value in (float('nan'),float('inf'),True):
                with self.assertRaises(ValueError):run_attempt(path,{'run_id':'x'},FakeDriver(),timeout_s=value)
                self.assertFalse(path.exists())

    def test_task_pass_does_not_promote_unknown_release(self):
        class UnknownRelease(FakeDriver):
            def audit(self,allocation):self.calls.append('audit');return {'status':'passed','release_confirmed':None}
        with tempfile.TemporaryDirectory() as d:
            result=run_attempt(Path(d)/'run',{'run_id':'unknown-release'},UnknownRelease(),timeout_s=1)
            self.assertEqual(result['status'],'incomplete')
            self.assertEqual(result['audit']['status'],'passed')
            self.assertEqual(result['input_release'],'UNKNOWN')

    def test_clean_task_is_audited_even_if_cleanup_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            driver=FakeDriver(cleanup='unknown')
            result=run_attempt(Path(d)/'run',{'run_id':'cleanup'},driver,timeout_s=1)
            self.assertEqual(result['status'],'incomplete')
            self.assertEqual(result['audit']['status'],'passed')
            self.assertEqual(result['cleanup']['status'],'unknown')
            self.assertIn('audit',driver.calls)

    def test_interrupt_in_host_cleanup_still_runs_container_cleanup(self):
        class InterruptHost(FakeDriver):
            def stop_host(self,token,timeout):self.calls.append('host_stop');raise KeyboardInterrupt()
        with tempfile.TemporaryDirectory() as d:
            driver=InterruptHost();path=Path(d)/'run'
            with self.assertRaises(KeyboardInterrupt):run_attempt(path,{'run_id':'interrupt'},driver,timeout_s=1)
            self.assertIn('container_cleanup',driver.calls)
            self.assertEqual(json.loads((path/'result.json').read_text())['status'],'incomplete')

    def test_late_zero_exit_does_not_count_as_complete(self):
        now={'ns':0}
        class LateExit(FakeDriver):
            def wait_container(self,token,timeout):
                result=super().wait_container(token,timeout)
                now['ns']=2_000_000_000
                return result
        with tempfile.TemporaryDirectory() as d, patch('lifecycle_launcher.time.monotonic_ns',side_effect=lambda:now['ns']):
            result=run_attempt(Path(d)/'run',{'run_id':'late'},LateExit(),timeout_s=1)
            self.assertEqual(result['status'],'incomplete')
            self.assertEqual(result['error']['type'],'TimeoutError')
            self.assertEqual(result['container']['exit_code'],0)

    def test_wait_receives_remaining_execution_budget(self):
        class CaptureTimeout(FakeDriver):
            def wait_container(self,token,timeout):
                self.wait_timeout=timeout
                return super().wait_container(token,timeout)
        ticks=iter(range(0, 10_000_000_000, 100_000_000))
        with tempfile.TemporaryDirectory() as d, patch('lifecycle_launcher.time.monotonic_ns',side_effect=lambda:next(ticks)):
            driver=CaptureTimeout()
            run_attempt(Path(d)/'run',{'run_id':'budget'},driver,timeout_s=1)
            self.assertGreater(driver.wait_timeout,0)
            self.assertLess(driver.wait_timeout,1)

    def test_malformed_wait_receipt_is_unknown_and_persisted(self):
        class BadWait(FakeDriver):
            def wait_container(self,token,timeout):return None
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'run';driver=BadWait()
            result=run_attempt(path,{'run_id':'bad-wait'},driver,timeout_s=1)
            self.assertEqual(result['status'],'incomplete')
            self.assertEqual(result['container']['status'],'unknown')
            self.assertEqual(result['error']['phase'],'container_wait')
            self.assertTrue((path/'result.json').is_file())

    def test_malformed_cleanup_receipt_is_unknown_and_persisted(self):
        class BadCleanup(FakeDriver):
            def cleanup_container(self,token,timeout):return None
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'run'
            result=run_attempt(path,{'run_id':'bad-cleanup'},BadCleanup(),timeout_s=1)
            self.assertEqual(result['status'],'incomplete')
            self.assertEqual(result['cleanup']['status'],'unknown')
            self.assertTrue((path/'result.json').is_file())

    def test_late_cleanup_not_promoted_to_complete(self):
        now={'ns':0}
        class LateCleanup(FakeDriver):
            def cleanup_container(self,token,timeout):
                result=super().cleanup_container(token,timeout)
                now['ns']=2_000_000_000
                return result
        with tempfile.TemporaryDirectory() as d, patch('lifecycle_launcher.time.monotonic_ns',side_effect=lambda:now['ns']):
            result=run_attempt(Path(d)/'run',{'run_id':'late-cleanup'},LateCleanup(),timeout_s=1)
            self.assertEqual(result['status'],'incomplete')
            self.assertTrue(result['cleanup_deadline_exceeded'])
            self.assertEqual(result['cleanup']['status'],'confirmed')

    def test_wait_exception_preserves_unknown_container_status(self):
        class BrokenWait(FakeDriver):
            def wait_container(self,token,timeout):raise TimeoutError('unknown wait')
        with tempfile.TemporaryDirectory() as d:
            result=run_attempt(Path(d)/'run',{'run_id':'wait-error'},BrokenWait(),timeout_s=1)
            self.assertEqual(result['container']['status'],'unknown')
            self.assertEqual(result['status'],'incomplete')

    def test_existing_allocation_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'run';path.mkdir();(path/'sentinel').write_text('keep')
            driver=FakeDriver()
            with self.assertRaises(FileExistsError):run_attempt(path,{'run_id':'three'},driver,timeout_s=1)
            self.assertEqual(driver.calls,[])
            self.assertEqual((path/'sentinel').read_text(),'keep')
if __name__=='__main__':unittest.main()
