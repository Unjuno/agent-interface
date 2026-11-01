"""Inert SendInput tests; no native input or windows are created."""
import unittest
from unittest.mock import patch
from runtime.backends.win32_v1 import backend as native
from runtime.backends.win32_v1.test_explicit_up_ledger import InputState

class FocusDriftCurrentTests(unittest.TestCase):
    def test_held_key_is_released_when_focus_drifts_before_next_down(self):
        b=native.Win32Backend.__new__(native.Win32Backend)
        b.held_keys={}; b.held_buttons=set(); b.pending_unicode_ups=set(); b.emissions=0
        b.user32=InputState(); b.user32.foreground=1
        b.user32.GetForegroundWindow=lambda: b.user32.foreground
        b.user32.GetAncestor=lambda hwnd, flags: hwnd
        b.targets={"fixture":1}; b.focused_target=None
        b.preflight=lambda program: None
        b.focus=lambda target: setattr(b,"focused_target",target)
        program={"ops":[{"op":"focus","target":"fixture"},{"op":"key_state","key":"Q","down":True},{"op":"wait_update","timeout_ms":1},{"op":"key_state","key":"R","down":True}]}
        with patch.object(native.time,"sleep", side_effect=lambda _: setattr(b.user32,"foreground",2)):
            with self.assertRaises(native.Win32ExecutionError) as caught: b.execute(program)
        sends=[row for row in b.user32.events if "send" in row]
        self.assertEqual(sends,[{"send":81,"down":True},{"send":81,"down":False}])
        self.assertEqual(b.user32.down,set())
        self.assertTrue(caught.exception.release_receipt["verified"])
        self.assertIsNone(native._execution_target.get())

if __name__ == "__main__": unittest.main()
