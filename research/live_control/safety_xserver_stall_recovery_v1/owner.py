import json, os, time
from Xlib import X, XK, display
from Xlib.ext import xtest

d=display.Display(); key=d.keysym_to_keycode(XK.string_to_keysym('F8'))
xtest.fake_input(d,X.KeyPress,key); d.sync()
pressed=time.monotonic_ns(); km=d.query_keymap(); down=bool(km[key//8] & (1 << (key%8)))
print(json.dumps({"event":"PRESS_CONFIRMED","pid":os.getpid(),"keycode":key,"pressed_ns":pressed,"down":down}),flush=True)
while True: time.sleep(1)
