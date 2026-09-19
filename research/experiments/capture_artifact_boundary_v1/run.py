from __future__ import annotations
import argparse, io, json, os, pathlib, statistics, subprocess, sys, tempfile, time
from Xlib import X, XK, display as xdisplay
from Xlib.ext import xtest
from PIL import Image, ImageGrab

APP=r'''\nimport json,time,tkinter as tk\nr=tk.Tk(); r.geometry("900x600+20+20"); c=tk.Canvas(r,width=900,height=600); c.pack(fill="both",expand=True)\nfor y in range(0,600,20):\n for x in range(0,900,20): c.create_rectangle(x,y,x+20,y+20,fill=("#335577" if (x//20+y//20)%2 else "#ccaa66"),outline="")\ndef e(k,v): print(json.dumps({"event":k,"perf_ns":time.perf_counter_ns(),"keycode":v.keycode}),flush=True)\nr.bind_all("<KeyPress>",lambda v:e("press",v)); r.bind_all("<KeyRelease>",lambda v:e("release",v)); r.update(); print(json.dumps({"event":"ready","xid":r.winfo_id()}),flush=True); r.mainloop()\n'''

def pct(v,p):
 s=sorted(v); k=(len(s)-1)*p; a=int(k); b=min(a+1,len(s)-1); f=k-a; return s[a]*(1-f)+s[b]*f

def line(p): return json.loads(p.stdout.readline())

def pipeline(display,tmp):
 t0=time.perf_counter_ns(); im=ImageGrab.grab(xdisplay=display); p=tmp/'frame.png'; im.save(p,format='PNG'); im2=Image.open(p); im2.load(); _=im2.getpixel((10,10)); t1=time.perf_counter_ns(); return (t1-t0)/1e6

def case(display,mode,tmp):
 env={**os.environ,'DISPLAY':display,'XAUTHORITY':'/dev/null'}; p=subprocess.Popen([sys.executable,'-u','-c',APP],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
 try:
  ready=line(p); d=xdisplay.Display(display); w=d.create_resource_object('window',ready['xid']); w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); time.sleep(.02)
  kc=d.keysym_to_keycode(XK.string_to_keysym('w')); down=time.perf_counter_ns(); xtest.fake_input(d,X.KeyPress,kc); d.sync(); press=line(p); deadline=down+250_000_000
  n=time.perf_counter_ns();
  if n<deadline: time.sleep((deadline-n)/1e9)
  if mode=='release_first': up=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,kc); d.sync(); pipe=pipeline(display,tmp)
  else: pipe=pipeline(display,tmp); up=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,kc); d.sync()
  rel=line(p); d.close(); return {'mode':mode,'app_hold_ms':(rel['perf_ns']-press['perf_ns'])/1e6,'deadline_to_up_ms':(up-deadline)/1e6,'pipeline_ms':pipe}
 finally:
  p.terminate(); p.wait(timeout=2)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--pairs',type=int,default=12); ap.add_argument('--out',type=pathlib.Path,required=True); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False); display=':98'; os.environ['XAUTHORITY']='/dev/null'
 xv=subprocess.Popen(['Xvfb',display,'-screen','0','1024x768x24','-nolisten','tcp','-ac']); wm=subprocess.Popen(['openbox'],env={**os.environ,'DISPLAY':display})
 try:
  time.sleep(.5); rows=[]
  with tempfile.TemporaryDirectory() as td:
   tmp=pathlib.Path(td)
   for i in range(a.pairs):
    order=('release_first','pipeline_first') if i%2==0 else ('pipeline_first','release_first')
    for m in order: r=case(display,m,tmp); r['pair']=i+1; rows.append(r)
  ds=[]
  for i in range(1,a.pairs+1):
   z={r['mode']:r for r in rows if r['pair']==i}; ds.append(z['pipeline_first']['app_hold_ms']-z['release_first']['app_hold_ms'])
  out={'pairs':a.pairs,'paired_delta_ms':{'median':statistics.median(ds),'p95':pct(ds,.95),'min':min(ds),'max':max(ds)},'pipeline_first_pipeline_median_ms':statistics.median(r['pipeline_ms'] for r in rows if r['mode']=='pipeline_first'),'rows':rows}
  (a.out/'result.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out['paired_delta_ms'],indent=2))
 finally:
  wm.terminate(); xv.terminate(); wm.wait(); xv.wait()
if __name__=='__main__': main()
