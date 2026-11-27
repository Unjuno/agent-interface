import json
from pathlib import Path
import tempfile
import unittest
from record_launch import record_launch

class RecorderTests(unittest.TestCase):
    def test_start_is_durable_before_preparation_failure_and_exception_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'attempt'; error=FileNotFoundError('conditions')
            def launch():
                self.assertTrue((p/'attempt-start.json').exists())
                raise error
            with self.assertRaises(FileNotFoundError) as caught:
                record_launch(p,launch,planned_stages=['prepare','model','task','cleanup'])
            self.assertIs(caught.exception,error)
            row=json.loads((p/'attempt-terminal.json').read_text())
            self.assertEqual(row['status'],'launcher_raised')
            self.assertIsNone(row['usage'])
            self.assertIsNone(row['task_success'])

    def test_existing_attempt_refuses_before_invocation(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileExistsError):
                record_launch(td,lambda:self.fail('replayed'),planned_stages=[])

    def test_return_and_exit_are_not_promoted_to_task_success(self):
        for code in (None,0,1):
            with self.subTest(code=code),tempfile.TemporaryDirectory() as td:
                p=Path(td)/'a'; value=object()
                def launch():
                    if code is not None: raise SystemExit(code)
                    return value
                if code is None:
                    self.assertIs(record_launch(p,launch,planned_stages=[]),value)
                else:
                    with self.assertRaises(SystemExit): record_launch(p,launch,planned_stages=[])
                self.assertIsNone(json.loads((p/'attempt-terminal.json').read_text())['task_success'])
