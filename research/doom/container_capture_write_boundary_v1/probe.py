from __future__ import annotations
import argparse, json, os, pathlib, statistics, subprocess, sys, tempfile, time
from Xlib import X, XK, display as xdisplay
from Xlib.ext import xtest
from PIL import ImageGrab

APP = r'''
import json, time, tkinter as tk
root=tk.Tk(); root.geometry("900x600+20+20"); root.title("capture-write-boundary-probe")
c=tk.Canvas(root,width=900,height=600,bg="white"); c.pack(fill="both",expand=True)
for y in range(0,600,20):
    for x in range(0,900,20):
        shade=(x//20+y//20)%2
        c.create_rectangle(x,y,x+20,y+20,fill=("#335577" if shade else "#ccaa66"),outline="")
def emit(kind, ev):
    print(json.dumps({"event":kind,"perf_ns":time.perf_counter_ns(),"keycode":ev.keycode}), flush=True)
root.bind_all("<KeyPress>", lambda e: emit("press",e))
root.bind_all("<KeyRelease>", lambda e: emit("release",e))
root.update_idletasks(); root.update()
print(json.dumps({"event":"ready","xid":root.winfo_id(),"perf_ns":time.perf_counter_ns()}), flush=True)
root.mainloop()
'''

def percentile(vals,p):
    s=sorted(vals); k=(len(s)-1)*p; lo=int(k); hi=min(lo+1,len(s)-1); f=k-lo
    return s[lo]*(1-f)+s[hi]*f

def wait_line(proc, timeout=3.0):
    import select
    r,_,_=select.select([proc.stdout],[],[],timeout)
    if not r: raise TimeoutError("app stdout timeout")
    line=proc.stdout.readline()
    if not line: raise RuntimeError("app exited")
    return json.loads(line)

def retained_pipeline(display):
    t0=time.perf_counter_ns()
    im=ImageGrab.grab(xdisplay=display)
    t_capture=time.perf_counter_ns()
    with tempfile.TemporaryDirectory(prefix='capture-artifact-') as td:
        path=pathlib.Path(td)/'frame.png'
        im.save(path, format='PNG')
        with path.open('rb') as f:
            os.fsync(f.fileno())
        t_write=time.perf_counter_ns()
        t_reopen=t_write
    return {
        'pipeline_total_ms':(t_reopen-t0)/1e6,
        'capture_ms':(t_capture-t0)/1e6,
        'png_write_fsync_ms':(t_write-t_capture)/1e6,
        'reopen_load_ms':0.0,
    }

def run_case(display, mode, hold_ms=250):
    env=dict(os.environ, DISPLAY=display, XAUTHORITY='/dev/null')
    app=subprocess.Popen([sys.executable,'-u','-c',APP],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,bufsize=1)
    try:
        ready=wait_line(app)
        d=xdisplay.Display(display)
        try:
            win=d.create_resource_object('window',int(ready['xid']))
            win.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); time.sleep(.02)
            keycode=d.keysym_to_keycode(XK.string_to_keysym('w'))
            down=time.perf_counter_ns(); xtest.fake_input(d,X.KeyPress,keycode); d.sync()
            press=wait_line(app)
            deadline=down+hold_ms*1_000_000
            now=time.perf_counter_ns()
            if now<deadline: time.sleep((deadline-now)/1e9)
            if mode=='release_first':
                up=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,keycode); d.sync()
                pipe=retained_pipeline(display)
            elif mode=='pipeline_first':
                pipe=retained_pipeline(display)
                up=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,keycode); d.sync()
            else:
                raise ValueError(mode)
            release=wait_line(app)
            return {
                'mode':mode,'hold_target_ms':hold_ms,
                'app_hold_ms':(release['perf_ns']-press['perf_ns'])/1e6,
                'send_hold_ms':(up-down)/1e6,
                'deadline_to_up_ms':(up-deadline)/1e6,
                'send_up_to_app_release_ms':(release['perf_ns']-up)/1e6,
                **pipe,
            }
        finally:
            d.close()
    finally:
        app.terminate()
        try: app.wait(timeout=1)
        except subprocess.TimeoutExpired: app.kill(); app.wait()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pairs',type=int,required=True); ap.add_argument('--out',type=pathlib.Path,required=True); args=ap.parse_args()
    out=args.out; out.mkdir(parents=True,exist_ok=False)
    display=':97'; os.environ['XAUTHORITY']='/dev/null'
    xvfb=subprocess.Popen(['Xvfb',display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=(out/'xvfb.stderr').open('w'))
    wm=subprocess.Popen(['openbox'],env={**os.environ,'DISPLAY':display},stdout=subprocess.DEVNULL,stderr=(out/'openbox.stderr').open('w'))
    try:
        time.sleep(.4); rows=[]
        for i in range(args.pairs):
            order=('release_first','pipeline_first') if i%2==0 else ('pipeline_first','release_first')
            for mode in order:
                row=run_case(display,mode); row['pair']=i+1; rows.append(row)
                with (out/'rows.jsonl').open('a',encoding='utf-8') as f:
                    f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
        by={m:[r for r in rows if r['mode']==m] for m in ('release_first','pipeline_first')}
        summary={}
        for m,rs in by.items():
            summary[m]={
                'n':len(rs),
                'app_hold_median_ms':statistics.median(r['app_hold_ms'] for r in rs),
                'app_hold_p95_ms':percentile([r['app_hold_ms'] for r in rs],.95),
                'send_hold_median_ms':statistics.median(r['send_hold_ms'] for r in rs),
                'deadline_to_up_median_ms':statistics.median(r['deadline_to_up_ms'] for r in rs),
                'pipeline_total_median_ms':statistics.median(r['pipeline_total_ms'] for r in rs),
                'capture_median_ms':statistics.median(r['capture_ms'] for r in rs),
                'png_write_fsync_median_ms':statistics.median(r['png_write_fsync_ms'] for r in rs),
                'reopen_load_median_ms':statistics.median(r['reopen_load_ms'] for r in rs),
                'send_up_to_app_release_median_ms':statistics.median(r['send_up_to_app_release_ms'] for r in rs),
            }
        diffs=[]; pipes=[]
        for i in range(1,args.pairs+1):
            rf=next(r for r in rows if r['pair']==i and r['mode']=='release_first')
            pf=next(r for r in rows if r['pair']==i and r['mode']=='pipeline_first')
            diffs.append(pf['app_hold_ms']-rf['app_hold_ms']); pipes.append(pf['pipeline_total_ms'])
        result={
            'schema':'capture-write-boundary-development-v1','pairs':args.pairs,'summary':summary,
            'paired_pipeline_first_minus_release_first_app_hold_ms':{
                'median':statistics.median(diffs),'p95':percentile(diffs,.95),'min':min(diffs),'max':max(diffs)},
            'pipeline_first_total_ms':{'median':statistics.median(pipes),'p95':percentile(pipes,.95)},
            'claim_boundary':'Rendered Xvfb/Tk/XTEST development fixture only; no ViZDoom/gameplay/model claim.'
        }
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,indent=2))
    finally:
        wm.terminate(); xvfb.terminate()
        for p in (wm,xvfb):
            try:p.wait(timeout=1)
            except subprocess.TimeoutExpired:p.kill();p.wait()
if __name__=='__main__': main()
