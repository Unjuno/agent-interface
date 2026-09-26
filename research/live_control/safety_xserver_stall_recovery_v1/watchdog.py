import json, os, sys, time
from Xlib import X, XK, display
from Xlib.ext import xtest

d=display.Display(); key=d.keysym_to_keycode(XK.string_to_keysym('F8'))
print(json.dumps({"event":"WATCHDOG_READY","pid":os.getpid(),"keycode":key,"authority":"cleanup_only","task_input_granted":False,"ts_ns":time.monotonic_ns()}),flush=True)
for line in sys.stdin:
    cmd=json.loads(line)
    if cmd.get('op')!='cleanup':
        continue
    req=time.monotonic_ns()
    xtest.fake_input(d,X.KeyRelease,key)
    d.sync()
    verified=time.monotonic_ns(); km=d.query_keymap(); up=not bool(km[key//8] & (1 << (key%8)))
    print(json.dumps({"event":"RELEASE_CONFIRMED","pid":os.getpid(),"request_ns":req,"verified_ns":verified,"keycode":key,"up":up,"authority":"cleanup_only","task_input_granted":False,"input_dispatched":False}),flush=True)
    break
