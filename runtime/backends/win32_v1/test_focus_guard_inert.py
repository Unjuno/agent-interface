import unittest
from unittest import mock
from runtime.backends.win32_v1.backend import Win32Backend, Win32BackendError, Win32ExecutionError, INPUT, INPUT_KEYBOARD, KEYBDINPUT, KEYEVENTF_KEYUP, _execution_target

class FakeUser:
    def __init__(self): self.foreground=1; self.calls=0
    def GetForegroundWindow(self): return self.foreground
    def GetAncestor(self, hwnd, flag): return hwnd
    def SendInput(self, *args): self.calls += 1; return 1

class Inert:
    _send = Win32Backend._send
    _handle_value = staticmethod(Win32Backend._handle_value)
    def __init__(self): self.user32=FakeUser(); self.emissions=0; self.released=0
    def _target(self, target): return 1
    def preflight(self, *args, **kwargs): pass
    def focus(self,target): self.user32.foreground=1
    def target_generation(self,target): return "stable"
    def key_state(self,key,down): self._send(INPUT(type=INPUT_KEYBOARD))
    def key_chord(self,keys):
        for key in keys: self.key_state(key, True)
    def release_all(self): self.released += 1; return {"verified":True}
    def execute(self, program): return Win32Backend.execute(self, program)

class FocusTests(unittest.TestCase):
    def test_drift_blocks_input_and_still_runs_cleanup(self):
        b=Inert()
        program={"source":{"target_generations":{"target":"stable"}},"ops":[{"op":"focus","target":"target"},{"op":"wait_update","timeout_ms":1},{"op":"key_state","key":"a","down":True}]}
        with mock.patch("runtime.backends.win32_v1.backend.time.sleep", side_effect=lambda _: setattr(b.user32,"foreground",2)):
            with self.assertRaises(Win32ExecutionError): b.execute(program)
        self.assertEqual(b.user32.calls,0)
        self.assertEqual(b.released,1)

    def test_drift_between_chord_downs_stops_second_and_clears_context(self):
        b=Inert()
        original = b.user32.SendInput
        def first_then_drift(*args):
            result=original(*args); b.user32.foreground=2; return result
        b.user32.SendInput=first_then_drift
        program={"ops":[{"op":"focus","target":"target"},{"op":"key_chord","keys":["a","b"]}]}
        with self.assertRaises(Win32ExecutionError): b.execute(program)
        self.assertEqual(b.user32.calls, 1)
        self.assertEqual(b.released, 1)
        self.assertIsNone(_execution_target.get())

    def test_key_up_remains_allowed_after_focus_drift(self):
        b=Inert(); b.user32.foreground=2
        item=INPUT(type=INPUT_KEYBOARD); item.ki=KEYBDINPUT(65, 0, KEYEVENTF_KEYUP, 0, 0)
        token=_execution_target.set("target")
        try: b._send(item)
        finally: _execution_target.reset(token)
        self.assertEqual(b.user32.calls, 1)

    def test_missing_foreground_api_fails_closed(self):
        b=Inert(); b.user32.GetForegroundWindow=lambda: 0
        token=_execution_target.set("target")
        try:
            with self.assertRaises(Win32BackendError): b._send(INPUT(type=INPUT_KEYBOARD))
        finally: _execution_target.reset(token)
        self.assertEqual(b.user32.calls, 0)

if __name__ == "__main__": unittest.main()
