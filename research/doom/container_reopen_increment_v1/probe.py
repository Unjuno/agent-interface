from __future__ import annotations
import argparse, json, os, pathlib, statistics, subprocess, sys, tempfile, time
from Xlib import X, XK, display as xdisplay
from Xlib.ext import xtest
from PIL import Image, ImageGrab

APP=r'''
import json,time,tkinter as tk
root=tk.Tk(); root.geometry("900x600+20+20"); root.title("reopen-increment-probe")
c=tk.Canvas(root,width=900,height=600,bg="white"); c.pack(fill="both",expand=True)
for y in range(0,600,20):
    for x in range(0,900,20):
        c.create_rectangle(x,y,x+20,y+20,fill=("#335577" if (x//20+y//20)%2 else "#ccaa66"),outline="")
def emit(kind,e): print(json.dumps({"event":kind,"perf_ns":time.perf_counter_ns(),"keycode":e.keycode}),flush=True)
root.bind_all("<KeyPress>",lambda e:emit("press",e)); root.bind_all("<KeyRelease>",lambda e:emit("release",e))
root.update_idletasks(); root.update(); print(json.dumps({"event":"ready","xid":root.winfo_id()}),flush=True); root.mainloop()
'''

def percentile(vals,p):
    s=sorted(vals); k=(len(s)-1)*p; lo=int(k); hi=min(lo+1,len(s)-1); f=k-lo
    return s[lo]*(1-f)+s[hi]*f

def wait_line(proc,timeout=3.0):
    import select
    r,_,_=select.select([proc.stdout],[],[],timeout)
    if not r: raise TimeoutError('app stdout timeout')
    line=proc.stdout.readline()
    if not line: raise RuntimeError('app exited')
    return json.loads(line)

def pre_release_pipeline(display, reopen):
    t0=time.perf_counter_ns(); im=ImageGrab.grab(xdisplay=display); t1=time.perf_counter_ns()
    with tempfile.TemporaryDirectory(prefix='reopen-increment-') as td:
        p=pathlib.Path(td)/'frame.png'; im.save(p,format='PNG')
        with p.open('rb') as f: os.fsync(f.fileno())
        t2=time.perf_counter_ns()
        if reopen:
            with Image.open(p) as r:
                r.load(); _=r.getpixel((10,10))
        t3=time.perf_counter_ns()
    return {'pipeline_ms':(t3-t0)/1e6,'capture_ms':(t1-t0)/1e6,'write_fsync_ms':(t2-t1)/1e6,'reopen_ms':(t3-t2)/1e6}

def run_case(display,mode,hold_ms=250):
    env={**os.environ,'DISPLAY':display,'XAUTHORITY':'/dev/null'}
    app=subprocess.Popen([sys.executable,'-u','-c',APP],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,bufsize=1)
    try:
        ready=wait_line(app); d=xdisplay.Display(display)
        try:
            w=d.create_resource_object('window',int(ready['xid'])); w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); time.sleep(.02)
            key=d.keysym_to_keycode(XK.string_to_keysym('w'))
            down=time.perf_counter_ns(); xtest.fake_input(d,X.KeyPress,key); d.sync(); press=wait_line(app)
            deadline=down+hold_ms*1_000_000; now=time.perf_counter_ns()
            if now<deadline: time.sleep((deadline-now)/1e9)
            pipe=pre_release_pipeline(display,reopen=(mode=='with_reopen'))
            up=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,key); d.sync(); release=wait_line(app)
            return {'mode':mode,'hold_target_ms':hold_ms,'app_hold_ms':(release['perf_ns']-press['perf_ns'])/1e6,'send_hold_ms':(up-down)/1e6,'deadline_to_up_ms':(up-deadline)/1e6,'send_up_to_app_release_ms':(release['perf_ns']-up)/1e6,**pipe}
        finally:d.close()
    finally:
        app.terminate()
        try:app.wait(timeout=1)
        except subprocess.TimeoutExpired:app.kill();app.wait()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pairs',type=int,required=True); ap.add_argument('--out',type=pathlib.Path,required=True); a=ap.parse_args()
    out=a.out; out.mkdir(parents=True,exist_ok=False); display=':96'; os.environ['XAUTHORITY']='/dev/null'
    xv=subprocess.Popen(['Xvfb',display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=(out/'xvfb.stderr').open('w'))
    wm=subprocess.Popen(['openbox'],env={**os.environ,'DISPLAY':display},stdout=subprocess.DEVNULL,stderr=(out/'openbox.stderr').open('w'))
    try:
        time.sleep(.4); rows=[]
        for i in range(a.pairs):
            order=('write_only','with_reopen') if i%2==0 else ('with_reopen','write_only')
            for mode in order:
                row=run_case(display,mode); row['pair']=i+1; rows.append(row)
                with (out/'rows.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
        by={m:[r for r in rows if r['mode']==m] for m in ('write_only','with_reopen')}; summary={}
        for m,rs in by.items():
            summary[m]={'n':len(rs),'app_hold_median_ms':statistics.median(r['app_hold_ms'] for r in rs),'app_hold_p95_ms':percentile([r['app_hold_ms'] for r in rs],.95),'pipeline_median_ms':statistics.median(r['pipeline_ms'] for r in rs),'capture_median_ms':statistics.median(r['capture_ms'] for r in rs),'write_fsync_median_ms':statistics.median(r['write_fsync_ms'] for r in rs),'reopen_median_ms':statistics.median(r['reopen_ms'] for r in rs),'deadline_to_up_median_ms':statistics.median(r['deadline_to_up_ms'] for r in rs)}
        diffs=[]; reopen_times=[]
        for i in range(1,a.pairs+1):
            wo=next(r for r in rows if r['pair']==i and r['mode']=='write_only'); wr=next(r for r in rows if r['pair']==i and r['mode']=='with_reopen')
            diffs.append(wr['app_hold_ms']-wo['app_hold_ms']); reopen_times.append(wr['reopen_ms'])
        res={'schema':'reopen-increment-development-v1','pairs':a.pairs,'summary':summary,'paired_with_reopen_minus_write_only_app_hold_ms':{'median':statistics.median(diffs),'p95':percentile(diffs,.95),'min':min(diffs),'max':max(diffs)},'with_reopen_reopen_ms':{'median':statistics.median(reopen_times),'p95':percentile(reopen_times,.95)},'claim_boundary':'Rendered Xvfb/Tk/XTEST development fixture only.'}
        (out/'result.json').write_text(json.dumps(res,indent=2)+'\n'); print(json.dumps(res,indent=2))
    finally:
        wm.terminate(); xv.terminate()
        for p in (wm,xv):
            try:p.wait(timeout=1)
            except subprocess.TimeoutExpired:p.kill();p.wait()
if __name__=='__main__':main()
