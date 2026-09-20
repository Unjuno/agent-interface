"""Construction check for the exact receiver-control oracle used by formal-02."""
import os, subprocess, tempfile, time, unittest
from Xlib import X, XK, display
from Xlib.ext import xtest
from runner import Lookup, drain

class ReceiverControl(unittest.TestCase):
    def test_press_and_release_lookup_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DISPLAY"] = ":219"
            log=open(os.path.join(tmp,"xvfb.log"),"wb")
            proc=subprocess.Popen(["/usr/bin/Xvfb",":219","-screen","0","800x600x24","-nolisten","tcp","+extension","XKEYBOARD","+extension","XTEST","-noreset"],stdout=log,stderr=subprocess.STDOUT)
            d=lookup=None
            try:
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    try:d=display.Display(":219");break
                    except Exception:time.sleep(.05)
                self.assertIsNotNone(d)
                w=d.screen().root.create_window(0,0,1,1,0,X.CopyFromParent,X.InputOnly,X.CopyFromParent,event_mask=X.KeyPressMask|X.KeyReleaseMask)
                w.map();w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
                self.assertEqual(d.get_input_focus().focus.id,w.id)
                lookup=Lookup();code=d.keysym_to_keycode(XK.string_to_keysym("a"))
                xtest.fake_input(d,X.KeyPress,code);d.sync();xtest.fake_input(d,X.KeyRelease,code);d.sync()
                got=drain(d,lookup)
                self.assertEqual([(e["type"],e["keycode"],e["keysym"],e["lookup_text"]) for e in got],
                    [("KeyPress",code,97,"a"),("KeyRelease",code,97,"a")])
            finally:
                if lookup:lookup.close()
                if d:d.close()
                if proc.poll() is None:proc.terminate()
                proc.wait(timeout=4);log.close()

if __name__=="__main__":unittest.main()
