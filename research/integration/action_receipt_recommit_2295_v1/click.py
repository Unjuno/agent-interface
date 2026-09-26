from __future__ import annotations
import argparse, json, os, time
from Xlib import X, display
from Xlib.ext import xtest
ap=argparse.ArgumentParser(); ap.add_argument('x',type=int); ap.add_argument('y',type=int); a=ap.parse_args()
d=display.Display()
xtest.fake_input(d,X.MotionNotify,x=a.x,y=a.y); d.sync()
xtest.fake_input(d,X.ButtonPress,1); d.sync(); time.sleep(0.01)
xtest.fake_input(d,X.ButtonRelease,1); d.sync(); time.sleep(0.01)
q=d.screen().root.query_pointer(); mask=int(q.mask)
print(json.dumps({'clicked':True,'x':a.x,'y':a.y,'pointer_mask':mask,'buttons_neutral':(mask & (X.Button1Mask|X.Button2Mask|X.Button3Mask|X.Button4Mask|X.Button5Mask))==0},sort_keys=True))
d.close()
