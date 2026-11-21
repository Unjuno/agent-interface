import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from recovery import reconcile_owned

CID='a'*64
RUN='b'*32

class RecoveryTests(unittest.TestCase):
    def test_stop_failure_still_independently_attempts_remove(self):
        cleanup=Mock(side_effect=[OSError('lost stop response'), {'status':'observed_absent','observed_exit_code':137}])
        with tempfile.TemporaryDirectory() as d:
            result=reconcile_owned(CID,RUN,Path(d),cleanup=cleanup)
        self.assertEqual(result['stop']['status'],'UNKNOWN')
        self.assertEqual(result['stop']['error_type'],'OSError')
        self.assertEqual(result['remove']['status'],'observed_absent')
        self.assertEqual(result['task_status'],'UNKNOWN')
        self.assertEqual(cleanup.call_count,2)
        self.assertTrue(cleanup.call_args_list[1].kwargs['remove_exited'])

    def test_timeout_is_not_task_success_even_if_removed(self):
        cleanup=Mock(side_effect=[{'status':'UNKNOWN','stop_command_succeeded':True}, {'status':'observed_absent','observed_exit_code':137}])
        with tempfile.TemporaryDirectory() as d:
            result=reconcile_owned(CID,RUN,Path(d),cleanup=cleanup)
        self.assertEqual(result['task_status'],'UNKNOWN')
        self.assertEqual(result['stop']['stop_command_succeeded'],True)
        self.assertEqual(result['remove']['observed_exit_code'],137)

    def test_malformed_receipts_and_both_errors_remain_unknown(self):
        for responses in ([None, {'status':'observed_absent'}], [OSError('a'), OSError('b')]):
            cleanup=Mock(side_effect=responses)
            with tempfile.TemporaryDirectory() as d:
                result=reconcile_owned(CID,RUN,Path(d),cleanup=cleanup)
            self.assertEqual(result['task_status'],'UNKNOWN')
            self.assertEqual(result['stop']['status'],'UNKNOWN')
            self.assertEqual(cleanup.call_count,2)

    def test_interrupt_is_reraised_only_after_removal_attempt(self):
        cleanup=Mock(side_effect=[KeyboardInterrupt(), {'status':'UNKNOWN'}])
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(KeyboardInterrupt):
                reconcile_owned(CID,RUN,Path(d),cleanup=cleanup)
        self.assertEqual(cleanup.call_count,2)

    def test_late_stop_receipt_is_marked_and_removal_not_started(self):
        now = {'t':0}
        def late(*args, **kwargs):
            now['t'] = 2
            return {'status':'observed_stopped'}
        cleanup=Mock(side_effect=late)
        with tempfile.TemporaryDirectory() as d, patch('recovery.time.monotonic',side_effect=lambda:now['t']):
            result=reconcile_owned(CID,RUN,Path(d),timeout_s=1,cleanup=cleanup)
        self.assertTrue(result['stop_returned_late'])
        self.assertEqual(result['remove']['error_type'],'DeadlineExceeded')
        self.assertEqual(cleanup.call_count,1)
        self.assertEqual(result['task_status'],'UNKNOWN')

    def test_distinct_journal_paths(self):
        cleanup=Mock(side_effect=[{'status':'observed_stopped'}, {'status':'observed_absent'}])
        with tempfile.TemporaryDirectory() as d:
            reconcile_owned(CID,RUN,Path(d),cleanup=cleanup)
            stop=cleanup.call_args_list[0].kwargs['journal_path']
            remove=cleanup.call_args_list[1].kwargs['journal_path']
            self.assertNotEqual(stop,remove)
            self.assertEqual(stop.parent,Path(d))
            self.assertEqual(remove.parent,Path(d))

if __name__=='__main__':unittest.main()
