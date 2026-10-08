"""Construction gate: prove InputOnly focus/event selection and XTEST receipt."""
import os
import subprocess
import tempfile
import time
import unittest

from Xlib import X, XK, display
from Xlib.ext import xtest

from runner import Lookup, drain


class ReceiverConstruction(unittest.TestCase):
    def test_input_only_focus_and_control_key_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            os.environ["DISPLAY"] = ":199"
            log = open(os.path.join(temp, "xvfb.log"), "wb")
            proc = subprocess.Popen(["/usr/bin/Xvfb", ":199", "-screen", "0", "800x600x24",
                "-nolisten", "tcp", "+extension", "XKEYBOARD", "+extension", "XTEST", "-noreset"],
                stdout=log, stderr=subprocess.STDOUT)
            disp = lookup = None
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    try:
                        disp = display.Display(":199")
                        break
                    except Exception:
                        time.sleep(.05)
                self.assertIsNotNone(disp)
                win = disp.screen().root.create_window(0, 0, 1, 1, 0, X.CopyFromParent,
                    X.InputOnly, X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
                win.map(); win.set_input_focus(X.RevertToParent, X.CurrentTime); disp.sync()
                self.assertEqual(disp.get_input_focus().focus.id, win.id)
                lookup = Lookup()
                code = disp.keysym_to_keycode(XK.string_to_keysym("a"))
                xtest.fake_input(disp, X.KeyPress, code); disp.sync()
                xtest.fake_input(disp, X.KeyRelease, code); disp.sync()
                events = drain(disp, lookup)
                self.assertEqual([(e["type"], e["keycode"], e["lookup_text"]) for e in events],
                    [("KeyPress", code, "a"), ("KeyRelease", code, "a")])
            finally:
                if lookup: lookup.close()
                if disp: disp.close()
                if proc.poll() is None: proc.terminate()
                proc.wait(timeout=4)
                log.close()


if __name__ == "__main__":
    unittest.main()
