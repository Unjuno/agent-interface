import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from native_allocation_v1 import NativeAllocation
from native_exchange_v1 import current_owner_identity


class AllocationTests(unittest.TestCase):
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
