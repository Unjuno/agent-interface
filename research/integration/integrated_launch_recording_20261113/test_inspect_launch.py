import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from inspect_launch import inspect_launch
from record_launch import record_launch

class InspectionTests(unittest.TestCase):
    def test_real_hard_exit_leaves_incomplete_record_not_success(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'attempt'
            code='import os,sys; from record_launch import record_launch; record_launch(sys.argv[1],lambda:os._exit(23),planned_stages=["setup","model"])'
            run=subprocess.run([sys.executable,'-c',code,str(target)],cwd=Path(__file__).parent,timeout=10)
            self.assertEqual(run.returncode,23)
            row=inspect_launch(target)
            self.assertEqual(row['status'],'incomplete')
            self.assertEqual(row['process_state'],'unknown')
            self.assertFalse(row['replay_allowed'])
            self.assertIsNone(row['usage'])

    def test_complete_and_corrupted_or_mismatched_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'attempt'
            record_launch(target,lambda:None,planned_stages=['setup'])
            self.assertEqual(inspect_launch(target)['status'],'terminal_recorded')
            terminal=target/'attempt-terminal.json'
            row=json.loads(terminal.read_text())
            row['started_ns']+=1
            terminal.write_text(json.dumps(row))
            self.assertEqual(inspect_launch(target)['status'],'invalid_record')
            terminal.write_text('{')
            self.assertEqual(inspect_launch(target)['status'],'invalid_record')
