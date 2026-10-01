"""Deterministic construction controls for the frozen call-boundary audit."""
from __future__ import annotations

import ast
import json
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "SOURCE_FREEZE.json").read_text(encoding="utf-8"))


def read_source(path: str) -> str:
    return subprocess.check_output(
        ["git", "cat-file", "blob", f"{FREEZE['main_sha']}:{path}"], cwd=ROOT, text=True
    )


class CallerBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner = ast.parse(read_source("research/live_control/input_owner_v10.py"))
        cls.wrapper = ast.parse(read_source("research/live_control/input_transition_owner_v3.py"))

    def method(self, tree, class_name, method_name):
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
        return next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == method_name)

    def test_client_owner_call_is_queue_wait_boundary(self):
        fn = self.method(self.owner, "InputOwner", "call")
        rendered = ast.unparse(fn)
        self.assertIn("self.requests.put", rendered)
        self.assertIn("done.wait", rendered)

    def test_client_call_has_no_local_release_invocation(self):
        fn = self.method(self.owner, "InputOwner", "call")
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "release" for n in ast.walk(fn)))

    def test_owner_loop_expires_cancelled_or_invalidated_lease(self):
        fn = self.method(self.owner, "InputOwner", "_run")
        text = ast.unparse(fn)
        self.assertIn("expired or active.cancel.is_set() or changed", text)
        self.assertIn("release('expired' if expired", text)

    def test_stop_and_thread_exit_paths_release_without_client_call(self):
        fn = self.method(self.owner, "InputOwner", "_run")
        release_args = [ast.unparse(n.args[0]) for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "release"]
        self.assertIn("'stop_requested'", release_args)
        self.assertIn("'thread_exit'", release_args)

    def test_v3_wrapper_stamps_only_client_operation_paths(self):
        fn = self.method(self.wrapper, "InputOwner", "call")
        text = ast.unparse(fn)
        self.assertIn("operation not in ('up', 'button_up')", text)
        self.assertIn("operation in ('release', 'close')", text)
        self.assertNotIn("_run", text)

    def test_registered_universal_nesting_rule_fails_for_autonomous_site(self):
        fn = self.method(self.owner, "InputOwner", "_run")
        wrapper_fn = self.method(self.wrapper, "InputOwner", "call")
        releases = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "release"]
        auto = [n for n in releases if ast.unparse(n.args[0]) != "op"]
        wrapper_text = ast.unparse(wrapper_fn)
        self.assertTrue(auto)
        self.assertNotIn("release(reason)", wrapper_text)
        self.assertNotIn("_run", wrapper_text)


if __name__ == "__main__":
    unittest.main()
