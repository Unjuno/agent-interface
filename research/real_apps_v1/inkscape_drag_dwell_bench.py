#!/usr/bin/env python3
import importlib.util, subprocess, time, json, statistics
from pathlib import Path
from Xlib import X, XK
from Xlib.ext import xtest

spec=importlib.util.spec_from_file_location('suite',str(Path(__file__).with_name('real_app_suite_v1.py')))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s=m.XSession(); path=s.tmp/'shape.svg';path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect id="r" x="50" y="50" width="40" height="30" fill="red"/></svg>')
D=s.d

def kc(n):return D.keysym_to_keycode(XK.string_to_keysym(n))
def raw(n,down):xtest.fake_input(D,X.KeyPress if down else X.KeyRelease,kc(n));D.sync()
def chord(a,b):raw(a,1);raw(b,1);raw(b,0);raw(a,0)
def capture_bbox():return m.largest_red_bbox(m.ImageGrab.grab())
def center(b):return ((b[0]+b[2])/2,(b[1]+b[3])/2)
def drag(x0,y0,dx,press_ms):
 xtest.fake_input(D,X.MotionNotify,x=round(x0),y=round(y0));D.sync()
 xtest.fake_input(D,X.ButtonPress,1);D.sync()
 if press_ms:time.sleep(press_ms/1000)
 steps=8
 for i in range(1,steps+1):
  xtest.fake_input(D,X.MotionNotify,x=round(x0+dx*i/steps),y=round(y0));D.sync();time.sleep(.004)
 xtest.fake_input(D,X.ButtonRelease,1);D.sync()

try:
 s.spawn(['inkscape',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 s.wait_window('shape.svg',10);s.focus('shape.svg');time.sleep(1)
 out=[]
 for dwell in [0,2,5,10,20,40]:
  succ=0; shifts=[]; lats=[]
  for j in range(20):
   chord('Control_L','a');time.sleep(.10)
   b0=capture_bbox();x0,y0=center(b0)
   t=time.perf_counter();drag(x0,y0,30,dwell);time.sleep(.10);b1=capture_bbox();lat=(time.perf_counter()-t)*1000
   x1,_=center(b1);shift=x1-x0;ok=shift>5
   succ+=ok;shifts.append(shift);lats.append(lat)
   if ok:
    chord('Control_L','z');time.sleep(.10)
  r={'press_dwell_ms':dwell,'success':succ,'n':20,'rate':succ/20,'shift_median_px':statistics.median(shifts),'latency_p50_ms':statistics.median(lats),'latency_max_ms':max(lats)}
  out.append(r);print(json.dumps(r),flush=True)
 res=Path(__file__).with_name('results'); res.mkdir(exist_ok=True); (res/'inkscape_dwell.json').write_text(json.dumps(out,indent=2))
finally:s.close()
