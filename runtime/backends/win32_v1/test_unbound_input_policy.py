"""Inert preflight tests for untargeted task input."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from runtime.backends.win32_v1 import backend as native

class UnboundInputPolicyTests(unittest.TestCase):
    def test_unbound_down_chord_and_text_are_refused(self):
        b=native.Win32Backend.__new__(native.Win32Backend)
        for op in ({"op":"key_state","key":"Q","down":True}, {"op":"key_chord","keys":["Q"]}, {"op":"text","text":"hello"}, {"op":"scroll","dx":0,"dy":120}, {"op":"pointer_button","button":"left","down":True}):
            with self.subTest(op=op), self.assertRaises(native.Win32BackendError):
                b.preflight({"ops":[op]})

    def test_focused_or_bound_target_is_accepted(self):
        b=native.Win32Backend.__new__(native.Win32Backend)
        b._target=lambda name: 7
        b.preflight({"ops":[{"op":"focus","target":"fixture"},{"op":"key_state","key":"Q","down":True}]})
        b.preflight({"ops":[{"op":"text","text":"hello"}]}, bound_target="fixture", guard=lambda: True)

    def test_shared_runner_selects_public_composition_only_on_windows(self):
        path = Path(__file__).resolve().parents[2] / "integration_checks" / "native.py"
        test_name = "runtime.cli_v1.test_mcp_supervised_backend_composition"
        for platform in ("win32", "linux"):
            with self.subTest(platform=platform), patch.object(sys, "platform", platform):
                spec = importlib.util.spec_from_file_location("native_runner_probe", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertEqual(test_name in module.SUITES["win32"], platform == "win32")

    def test_unbound_up_and_release_stay_available(self):
        b=native.Win32Backend.__new__(native.Win32Backend)
        b.preflight({"ops":[{"op":"key_state","key":"Q","down":False},{"op":"release_all"}]})

if __name__ == "__main__": unittest.main()
