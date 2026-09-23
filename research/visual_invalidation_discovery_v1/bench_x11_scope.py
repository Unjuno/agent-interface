from __future__ import annotations
import json, multiprocessing as mp, os, platform, statistics, time
import numpy as np
from PIL import ImageGrab
DISPLAY=':99'; W=H=256; ROI=(104,104,152,152); COUNT_T=100; N=30
TARGET=(122,122,134,134); NUIS=(20,20,36,36)

def child(conn):
 os.environ['DISPLAY']=DISPLAY
 import tkinter as tk
 root=tk.Tk(); root.geometry(f'{W}x{H}+0+0'); root.overrideredirect(True)
 c=tk.Canvas(root,width=W,height=H,highlightthickness=0,bg='#505050'); c.pack()
 tr=c.create_rectangle(*TARGET,fill='#505050',outline=''); nr=c.create_rectangle(*NUIS,fill='#505050',outline='')
 def apply(kind,on):
  obj=tr if kind=='target' else nr; c.itemconfig(obj,fill=('#909090' if on else '#505050')); root.update_idletasks(); conn.send(('applied',kind,on,time.perf_counter()))
 def poll():
  while conn.poll():
   m=conn.recv()
   if m[0]=='set': root.after(int(m[3]),lambda k=m[1],o=m[2]:apply(k,o))
   elif m[0]=='quit': root.destroy(); return
  root.after(1,poll)
 root.update_idletasks(); conn.send(('ready',)); root.after(1,poll); root.mainloop()

def gray(im): return np.asarray(im,dtype=np.uint8)[:,:,0]
def wait(conn,k,on):
 while True:
  m=conn.recv()
  if m[:3]==('applied',k,on): return m[3]
def changed_count(a,b): return int(np.count_nonzero(np.abs(a.astype(np.int16)-b.astype(np.int16))>=12))
def grab_full(): return gray(ImageGrab.grab(bbox=(0,0,W,H),xdisplay=DISPLAY))
def grab_roi(): return gray(ImageGrab.grab(bbox=ROI,xdisplay=DISPLAY))

def run(conn,observer,event_kind):
 hits=0; lats=[]; calls=[]
 for _ in range(N):
  for k in ['target','nuisance']:
   conn.send(('set',k,False,0)); wait(conn,k,False)
  time.sleep(.003)
  ref=grab_full() if observer=='global' else grab_roi()
  conn.send(('set',event_kind,True,15)); ev=None; hit=False; deadline=time.perf_counter()+.1
  while time.perf_counter()<deadline:
   t0=time.perf_counter_ns(); cur=grab_full() if observer=='global' else grab_roi(); calls.append((time.perf_counter_ns()-t0)/1e6)
   while conn.poll():
    m=conn.recv()
    if m[:3]==('applied',event_kind,True): ev=m[3]
   if changed_count(ref,cur)>=COUNT_T:
    hit=True; td=time.perf_counter()
    if ev is None: ev=wait(conn,event_kind,True)
    lats.append((td-ev)*1000); break
  hits+=int(hit)
 return {'hit_rate':hits/N,'median_event_to_hit_ms':statistics.median(lats) if lats else None,'median_capture_ms':statistics.median(calls),'median_changed_threshold':COUNT_T}

def main():
 a,b=mp.Pipe(); p=mp.Process(target=child,args=(b,),daemon=True); p.start(); assert a.recv()[0]=='ready'; time.sleep(.03)
 out={}
 for obs in ['global','scoped_roi']:
  out[obs]={}
  for event in ['target','nuisance']:
   out[obs][event]=run(a,obs,event)
 a.send(('quit',)); p.join(2)
 print(json.dumps({'env':{'python':platform.python_version(),'platform':platform.platform(),'cpu_count':os.cpu_count()},'fixture':{'window':[W,H],'roi':ROI,'target':TARGET,'nuisance':NUIS,'changed_pixel_count_threshold':COUNT_T,'n_per_cell':N,'note':'same changed-pixel threshold; Xvfb/Tk/PIL'},'results':out},indent=2))
if __name__=='__main__': main()
