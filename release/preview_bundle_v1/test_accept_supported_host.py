from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
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

    @mock.patch.object(mod, 'run_step')
    def test_setup_reuses_existing_venv_without_installing(self, run_step):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); out = root / 'out'; out.mkdir()
            venv = root / 'runtime' / '.venv'; venv.mkdir(parents=True)
            row = mod.setup_step(root, out, 2, install_dependencies=True)
            self.assertEqual(row['status'], 'skipped_existing_venv')
            self.assertEqual(row['venv_path'], str(venv))
            run_step.assert_not_called()

    @mock.patch.object(mod, 'run_step')
    def test_setup_requires_explicit_install_opt_in_for_missing_venv(self, run_step):
        run_step.return_value = {'name': 'setup', 'returncode': 2}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); out = root / 'out'; out.mkdir()
            mod.setup_step(root, out, 2, install_dependencies=False)
            self.assertEqual(run_step.call_args.args[3], 'setup')
            self.assertEqual(run_step.call_args.args[4], ['./runtime/setup-golden-demo-v3.sh'])

    @mock.patch.object(mod, 'run_step')
    def test_setup_passes_install_opt_in_when_authorized(self, run_step):
        run_step.return_value = {'name': 'setup', 'returncode': 0}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); out = root / 'out'; out.mkdir()
            mod.setup_step(root, out, 2, install_dependencies=True)
            self.assertEqual(run_step.call_args.args[4], [
                './runtime/setup-golden-demo-v3.sh', '--install-dependencies'])


    def test_partial_native_accounting_is_audited_but_holds_acceptance(self):
        live_schema = "agent_interface_golden_desktop_live_v2"
        audit_schema = "agent_interface_golden_live_audit_v1"
        partial = {"passed": False, "functional_passed": True, "usage_status": "partial",
                   "accounting_policy": "native-cache-write-optional-v1"}
        for audit_valid in (False, True):
            with self.subTest(audit_valid=audit_valid), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                out = root / "out"
                (root / "runtime" / ".venv").mkdir(parents=True)

                def step(_root, _out, _index, name, _command):
                    if name == "run":
                        return {"name": name, "returncode": 1,
                                "parsed_json": {**partial, "schema": live_schema}}
                    if name == "audit-live":
                        if audit_valid:
                            return {"name": name, "returncode": 1,
                                    "parsed_json": {**partial, "schema": audit_schema}}
                        return {"name": name, "returncode": 0,
                                "parsed_json": {"schema": audit_schema, "passed": True}}
                    return {"name": name, "returncode": 0, "parsed_json": {"passed": True}}

                with mock.patch.object(mod, "run_step", side_effect=step) as runner, \
                     mock.patch.object(sys, "argv", ["accept", "--root", str(root),
                                                     "--out", str(out), "--live"]), \
                     mock.patch("builtins.print"):
                    self.assertEqual(mod.main(), 1)
                self.assertEqual([call.args[3] for call in runner.call_args_list][-2:],
                                 ["run", "audit-live"])
                result = json.loads((out / "acceptance.json").read_bytes())
                self.assertFalse(result["passed"])
                self.assertFalse(result["release_ready"])
                self.assertEqual(result["status"], "HOLD_SUPPORTED_HOST_ACCOUNTING" if audit_valid
                                 else "FAIL_SUPPORTED_HOST_ACCEPTANCE")


if __name__=='__main__': unittest.main()
