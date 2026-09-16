from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("accept_supported_host", HERE / "accept_supported_host.py")
mod = importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(mod)

class FakeCompleted:
    def __init__(self, returncode=0, stdout='{}\n', stderr=''):
        self.returncode=returncode; self.stdout=stdout; self.stderr=stderr

class AcceptanceHelpers(unittest.TestCase):
    @mock.patch.object(mod.subprocess, 'run')
    def test_run_step_retains_stdout_stderr_and_json(self, run):
        run.return_value=FakeCompleted(stdout='{"passed": true}\n', stderr='note\n')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=root/'out'; out.mkdir()
            row=mod.run_step(root,out,1,'doctor',['doctor'])
            self.assertEqual(row['returncode'],0)
            self.assertTrue(row['parsed_json']['passed'])
            self.assertEqual((out/'01-doctor.stderr.txt').read_text(),'note\n')
            retained=json.loads((out/'01-doctor.json').read_text())
            self.assertEqual(retained['name'],'doctor')

    def test_git_revision_none_without_git(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(mod.git_revision(Path(td)))

if __name__=='__main__': unittest.main()
