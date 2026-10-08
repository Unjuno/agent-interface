from __future__ import annotations
import argparse, json, os, pathlib, statistics, subprocess, sys, tempfile, time
from Xlib import X, XK, display as xdisplay
from Xlib.ext import xtest
from PIL import ImageGrab

APP = r'''
import json, sys, time, tkinter as tk
root=tk.Tk(); root.geometry("900x600+20+20"); root.title("capture-hold-probe")
# make capture nontrivial but deterministic
c=tk.Canvas(root,width=900,height=600,bg="white"); c.pack(fill="both",expand=True)
for y in range(0,600,20):
    for x in range(0,900,20):
        shade=(x//20+y//20)%2
        c.create_rectangle(x,y,x+20,y+20,fill=("#335577" if shade else "#ccaa66"),outline="")
log=[]
def emit(kind, ev):
    row={"event":kind,"perf_ns":time.perf_counter_ns(),"keysym":ev.keysym,"keycode":ev.keycode}
    print(json.dumps(row), flush=True)
root.bind_all("<KeyPress>", lambda e: emit("press",e))
root.bind_all("<KeyRelease>", lambda e: emit("release",e))
root.update_idletasks(); root.update()
print(json.dumps({"event":"ready","xid":root.winfo_id(),"perf_ns":time.perf_counter_ns()}), flush=True)
root.mainloop()
'''

def percentile(vals, p):
    s=sorted(vals)
    if not s: return None
    k=(len(s)-1)*p
    lo=int(k); hi=min(lo+1,len(s)-1); f=k-lo
    return s[lo]*(1-f)+s[hi]*f

def wait_line(proc, timeout=3.0):
    import select
    r,_,_=select.select([proc.stdout],[],[],timeout)
    if not r: raise TimeoutError("app stdout timeout")
    line=proc.stdout.readline()
    if not line: raise RuntimeError("app exited")
    return json.loads(line)

def run_case(dpy_name, mode, hold_ms=250, capture_every_ms=50):
    env=dict(os.environ, DISPLAY=dpy_name, XAUTHORITY='/dev/null')
    app=subprocess.Popen([sys.executable,"-u","-c",APP],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,bufsize=1)
    try:
        ready=wait_line(app)
        if ready.get("event")!="ready": raise RuntimeError(ready)
        d=xdisplay.Display(dpy_name)
        try:
            win=d.create_resource_object('window', int(ready['xid']))
            win.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync(); time.sleep(0.02)
            keycode=d.keysym_to_keycode(XK.string_to_keysym('w'))
            send_down_ns=time.perf_counter_ns(); xtest.fake_input(d,X.KeyPress,keycode); d.sync()
            press=wait_line(app)
            if press.get('event')!='press': raise RuntimeError(("expected press",press))
            deadline=send_down_ns+hold_ms*1_000_000
            captures=[]
            next_cap=send_down_ns+capture_every_ms*1_000_000
            if mode=='capture':
                while True:
                    now=time.perf_counter_ns()
                    if now>=deadline: break
                    if now<next_cap:
                        time.sleep((min(next_cap,deadline)-now)/1e9)
                        continue
                    c0=time.perf_counter_ns(); im=ImageGrab.grab(xdisplay=dpy_name); _=im.getpixel((10,10)); c1=time.perf_counter_ns()
                    captures.append(c1-c0); next_cap += capture_every_ms*1_000_000
            else:
                now=time.perf_counter_ns()
                if now<deadline: time.sleep((deadline-now)/1e9)
            send_up_ns=time.perf_counter_ns(); xtest.fake_input(d,X.KeyRelease,keycode); d.sync()
            release=wait_line(app)
            if release.get('event')!='release': raise RuntimeError(("expected release",release))
            return {
                'mode':mode,'hold_target_ms':hold_ms,
                'send_hold_ms':(send_up_ns-send_down_ns)/1e6,
                'app_hold_ms':(release['perf_ns']-press['perf_ns'])/1e6,
                'send_up_to_app_release_ms':(release['perf_ns']-send_up_ns)/1e6,
                'press_delivery_ms':(press['perf_ns']-send_down_ns)/1e6,
                'captures':len(captures),
                'capture_total_ms':sum(captures)/1e6,
                'capture_max_ms':max(captures,default=0)/1e6,
            }
        finally:
            d.close()
    finally:
        app.terminate()
        try: app.wait(timeout=1)
        except subprocess.TimeoutExpired: app.kill(); app.wait()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pairs',type=int,default=20); ap.add_argument('--out',type=pathlib.Path,required=True); args=ap.parse_args()
    out=args.out; out.mkdir(parents=True,exist_ok=False)
    display=':99'
    os.environ['XAUTHORITY']='/dev/null'
    xvfb=subprocess.Popen(['Xvfb',display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=(out/'xvfb.stderr').open('w'))
    env=dict(os.environ,DISPLAY=display)
    wm=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=(out/'openbox.stderr').open('w'))
    try:
        time.sleep(.4)
        rows=[]
        # balanced alternating order by pair
        for i in range(args.pairs):
            order=('none','capture') if i%2==0 else ('capture','none')
            for mode in order:
                row=run_case(display,mode); row['pair']=i+1; rows.append(row)
                with (out/'rows.jsonl').open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps(row,sort_keys=True)+'\n')
                    stream.flush()
                    os.fsync(stream.fileno())
        (out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
        by={m:[r for r in rows if r['mode']==m] for m in ('none','capture')}
        summary={}
        for m,rs in by.items():
            vals=[r['app_hold_ms'] for r in rs]
            summary[m]={
                'n':len(vals),'app_hold_median_ms':statistics.median(vals),
                'app_hold_p95_ms':percentile(vals,.95),'app_hold_min_ms':min(vals),'app_hold_max_ms':max(vals),
                'send_hold_median_ms':statistics.median(r['send_hold_ms'] for r in rs),
                'send_up_to_app_release_median_ms':statistics.median(r['send_up_to_app_release_ms'] for r in rs),
                'capture_total_median_ms':statistics.median(r['capture_total_ms'] for r in rs),
                'captures_median':statistics.median(r['captures'] for r in rs),
            }
        diffs=[]
        for i in range(1,args.pairs+1):
            a=next(r for r in rows if r['pair']==i and r['mode']=='none')
            b=next(r for r in rows if r['pair']==i and r['mode']=='capture')
            diffs.append(b['app_hold_ms']-a['app_hold_ms'])
        result={'schema':'capture-hold-cost-development-v1','pairs':args.pairs,'summary':summary,
                'paired_capture_minus_none_ms':{'median':statistics.median(diffs),'min':min(diffs),'max':max(diffs),'p95':percentile(diffs,.95)},
                'claim_boundary':'Rendered Xvfb/Tk/XTEST development fixture only; no ViZDoom/gameplay/model claim.'}
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
    finally:
        wm.terminate(); xvfb.terminate();
        for p in (wm,xvfb):
            try:p.wait(timeout=1)
            except: p.kill(); p.wait()
if __name__=='__main__': main()
