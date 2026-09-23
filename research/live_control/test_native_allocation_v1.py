import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from native_allocation_v1 import NativeAllocation
from native_exchange_v1 import current_owner_identity


class AllocationTests(unittest.TestCase):
    def test_explicit_text_policy_is_forwarded_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            for gap in (0,2,10):
                allocation=NativeAllocation(Path(tmp)/str(gap),'calc',text_gap_ms=gap)
                process=Mock(pid=os.getpid()); process.poll.return_value=None
                with patch('native_allocation_v1.subprocess.Popen',return_value=process) as spawn:
                    state=allocation.start(timeout=0)
                self.assertEqual(state['text_gap_ms'],gap)
                argv=spawn.call_args.args[0]
                self.assertEqual(argv[argv.index('--text-gap-ms')+1],str(gap))
            for bad in (True,1,20,'2',2.0):
                with self.assertRaises(ValueError):
                    NativeAllocation(Path(tmp)/'invalid','calc',text_gap_ms=bad)
            self.assertFalse((Path(tmp)/'invalid').exists())

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'allocation'
        self.process=Mock(pid=os.getpid())
        self.process.poll.return_value=None

    def test_start_timeout_observes_same_owner_and_never_restarts_terminal(self):
        allocation=NativeAllocation(self.path,'inkscape',python='/configured/python')
        self.assertEqual(allocation.status()['status'],'not_started')
        with patch('native_allocation_v1.subprocess.Popen',return_value=self.process) as spawn:
            self.assertEqual(allocation.start(timeout=0)['status'],'starting')
            self.assertEqual(allocation.start(timeout=0)['status'],'starting')
            allocation.run_directory.mkdir()
            (allocation.run_directory/'owner.json').write_text(json.dumps(current_owner_identity()))
            (allocation.run_directory/'source-1.json').write_text('{}')
            self.assertEqual(allocation.start(timeout=0)['status'],'ready')
            self.process.poll.return_value=1
            terminal=allocation.start(timeout=0)
            self.assertEqual(terminal['status'],'terminal')
            self.assertEqual(terminal['returncode'],1)
            self.assertIsNone(terminal['task_success'])
            self.assertFalse(terminal['cleanup_verified'])
            self.assertEqual(spawn.call_count,1)
            self.assertEqual(spawn.call_args.args[0][0],'/configured/python')
            self.assertNotIn('shell',spawn.call_args.kwargs)

    def test_existing_directory_and_failed_spawn_never_retry(self):
        self.path.mkdir()
        allocation=NativeAllocation(self.path,'calc')
        with patch('native_allocation_v1.subprocess.Popen') as spawn:
            self.assertEqual(allocation.status()['status'],'needs_review')
            self.assertEqual(allocation.start(timeout=0)['status'],'needs_review')
            self.assertEqual(allocation.start(timeout=0)['status'],'needs_review')
            spawn.assert_not_called()
        other=NativeAllocation(Path(self.temp.name)/'other','calc')
        with patch('native_allocation_v1.subprocess.Popen',side_effect=OSError('injected')) as spawn:
            self.assertEqual(other.start(timeout=0)['status'],'needs_review')
            self.assertEqual(other.start(timeout=0)['status'],'needs_review')
            self.assertEqual(spawn.call_count,1)

    def test_exit_between_poll_and_owner_read_gets_one_nonblocking_recheck(self):
        allocation = NativeAllocation(self.path, 'inkscape')
        allocation.process = self.process
        for code in (0, 7, None):
            with self.subTest(code=code):
                self.process.reset_mock()
                self.process.poll.side_effect = [None, code]
                with patch('native_allocation_v1.owner_state', return_value={
                        'state': 'terminal', 'reason': 'owner_process_terminal'}):
                    state = allocation.status()
                self.assertEqual(self.process.poll.call_count, 2)
                self.process.wait.assert_not_called()
                self.process.terminate.assert_not_called()
                self.assertFalse(state['restart_allowed'])
                if code is None:
                    self.assertEqual(state['status'], 'needs_review')
                    self.assertNotIn('returncode', state)
                else:
                    self.assertEqual((state['status'], state['returncode']), ('terminal', code))
                    self.assertIsNone(state['task_success'])
                    self.assertFalse(state['cleanup_verified'])

    def test_nonterminal_owner_does_not_trigger_extra_poll(self):
        allocation = NativeAllocation(self.path, 'inkscape')
        allocation.process = self.process
        for owner in (None, {'state': 'live'}, {'state': 'unverifiable'}):
            with self.subTest(owner=owner):
                self.process.reset_mock()
                self.process.poll.side_effect = [None]
                with patch('native_allocation_v1.owner_state', return_value=owner):
                    allocation.status()
                self.assertEqual(self.process.poll.call_count, 1)

    def test_foreign_source_is_not_ready(self):
        allocation=NativeAllocation(self.path,'inkscape')
        with patch('native_allocation_v1.subprocess.Popen',return_value=self.process):
            allocation.start(timeout=0)
        allocation.run_directory.mkdir()
        (allocation.run_directory/'source-1.json').write_text('{}')
        (allocation.run_directory/'owner.json').write_text(json.dumps(dict(current_owner_identity(),pid=99999999)))
        self.assertEqual(allocation.status()['status'],'needs_review')

    def test_invalid_start_has_no_side_effect(self):
        allocation=NativeAllocation(self.path,'calc')
        for timeout in [-1,True,float('nan'),31]:
            with self.assertRaises(ValueError):allocation.start(timeout=timeout)
        self.assertFalse(self.path.exists())


if __name__=='__main__':
    unittest.main()
