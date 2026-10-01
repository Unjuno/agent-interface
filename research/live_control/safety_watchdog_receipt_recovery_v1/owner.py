import json, os, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest
life_fd=int(sys.argv[1]); ready_fd=int(sys.argv[2]); start_fd=int(sys.argv[3])
d=display.Display(); kc=d.keysym_to_keycode(XK.string_to_keysym('F8'))
if os.read(start_fd,1)!=b'G': raise RuntimeError('owner start barrier closed')
xtest.fake_input(d,X.KeyPress,kc); d.sync(); press_ns=time.monotonic_ns()
os.write(ready_fd,(json.dumps({'event':'PRESS_CONFIRMED','press_ns':press_ns,'keycode':kc})+'\n').encode())
while True: time.sleep(10)
