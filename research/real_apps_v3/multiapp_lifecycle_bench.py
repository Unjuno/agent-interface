#!/usr/bin/env python3
import argparse, json, os, random, statistics, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'real_apps_v1'))
import real_app_suite_v1 as base
from PIL import ImageGrab
from Xlib import X
from Xlib.ext import xtest

base.MODE='sparse_reactive'
base.CHAR_GAP_MS=2.0

class Metrics:
    def __init__(self):
        self.obs_pixels=0; self.obs_count=0; self.capture_ms=[]; self.input_events=0
    def full(self):
        t=time.perf_counter(); im=ImageGrab.grab(); dt=(time.perf_counter()-t)*1000
        self.obs_pixels += im.width*im.height; self.obs_count += 1; self.capture_ms.append(dt); return im


def q(a,p):
    if not a: return None
    a=sorted(a); return a[min(len(a)-1, int((len(a)-1)*p))]

def wm_lines(s): return s.windows().splitlines()

def wid_for(s, needle):
    for line in wm_lines(s):
        if needle in line: return line.split()[0]
    return None

def title_for_id(s,wid):
    for line in wm_lines(s):
        if line.startswith(wid+' '):
            parts=line.split(None,3); return parts[3] if len(parts)>=4 else ''
    return ''

def focus_id(s,wid):
    subprocess.run(['wmctrl','-ia',wid],env=s.env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
    time.sleep(.015)

def geom(s,wid):
    out=subprocess.run(['wmctrl','-lG'],env=s.env,text=True,capture_output=True).stdout
    for line in out.splitlines():
        if line.startswith(wid+' '):
            ps=line.split(); return tuple(map(int,ps[2:6]))
    raise RuntimeError('geometry missing '+wid)

def click(s,x,y,m):
    xtest.fake_input(s.d,X.MotionNotify,x=int(x),y=int(y)); s.d.sync(); m.input_events+=1
    xtest.fake_input(s.d,X.ButtonPress,1); s.d.sync(); m.input_events+=1
    xtest.fake_input(s.d,X.ButtonRelease,1); s.d.sync(); m.input_events+=1

class Input:
    def __init__(self,s,m): self.s=s; self.m=m; self.d=base.Driver(s,0)
    def _run(self,fn,*args):
        before=self.d.input_events; fn(*args); self.m.input_events += self.d.input_events-before
    def text(self,t): self._run(self.d.text,t)
    def key(self,k): self._run(self.d.key,k)
    def chord(self,a,b): self._run(self.d.chord,a,b)

# Planner serialization proxies only. These are bytes, not model tokens.
def raw_payload(app,arg):
    if app=='xterm': return f'OBSERVE;FOCUS target;TEXT {arg};KEY ENTER;VERIFY title={arg}'
    return f'OBSERVE;FOCUS browser;CHORD CTRL L;TEXT {arg};KEY ENTER;VERIFY title={arg}'

def call_payload(app,arg):
    return f'CALL SEND_TITLE({arg})' if app=='xterm' else f'CALL NAVIGATE({arg})'


def summarize(run):
    rs=run['rows']; good=[r for r in rs if r['success']]
    vals=lambda k:[r[k] for r in good]
    return {
        'app':run['app'],'strategy':run['strategy'],'seed':run['seed'],'n':len(rs),
        'success':sum(r['success'] for r in rs),
        'wall_p50_ms':statistics.median(vals('wall_ms')) if good else None,
        'wall_p95_ms':q(vals('wall_ms'),.95),'wall_p99_ms':q(vals('wall_ms'),.99),
        'planner_bytes_mean':statistics.mean(vals('planner_bytes')) if good else None,
        'obs_mpix_mean':statistics.mean(vals('obs_pixels'))/1e6 if good else None,
        'obs_count_mean':statistics.mean(vals('obs_count')) if good else None,
        'input_events_mean':statistics.mean(vals('input_events')) if good else None,
        'defs':run['defs'],'route_failures':run['route_failures'],'route_suspensions':run['route_suspensions'],
        'fallbacks':run['fallbacks'],'reheats':run['reheats']
    }


def run_xterm(strategy,seed,episodes=24,learn_after=2,reheat_after=2,updates=(8,16)):
    s=base.XSession(); m=Metrics(); inp=Input(s,m); rows=[]
    method_defined=False; route_hot=False; clean=0; defs=0; route_failures=0; susp=0; fallbacks=0; reheats=0
    try:
        # target: each plain input line becomes the XTerm title; no shell command language required.
        cmd='while IFS= read -r line; do printf "\\033]0;%s\\007" "$line"; done'
        s.spawn(['xterm','-T','AI-XTERM','-geometry','80x24','-e','sh','-c',cmd],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        s.wait_window('AI-XTERM',5); target=wid_for(s,'AI-XTERM'); focus_id(s,target)
        # distractor consumes input harmlessly.
        s.spawn(['xterm','-T','DISTRACTOR','-geometry','50x10','-e','sh','-c','cat >/dev/null'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        s.wait_window('DISTRACTOR',5); distractor=wid_for(s,'DISTRACTOR'); focus_id(s,target)
        for ep in range(episodes):
            injected=None
            if ep in updates:
                injected='focus_loss'; focus_id(s,distractor)
            token=f'e{seed%100:02d}_{ep:02d}'
            p0=m.obs_pixels; o0=m.obs_count; i0=m.input_events; t0=time.perf_counter()
            planner=call_payload('xterm',token) if method_defined else raw_payload('xterm',token)
            success=False; used_hot=route_hot; fallback=False; failed_hot=False
            if route_hot:
                inp.text(token); inp.key('Return')
                success=base.wait_until(lambda:title_for_id(s,target)==token,.12,.002)
                if not success:
                    failed_hot=True; route_failures+=1; fallbacks+=1; fallback=True
                    route_hot=False; clean=0
                    if strategy=='invalidate': method_defined=False
                    else: susp+=1
            if not success:
                # Universal route. If semantic method is gone, reacquire from screen/context.
                if not method_defined:
                    m.full()
                focus_id(s,target); inp.text(token); inp.key('Return')
                success=base.wait_until(lambda:title_for_id(s,target)==token,.25,.002)
            if success:
                if not route_hot:
                    clean += 1
                    threshold=learn_after if not method_defined else reheat_after
                    if clean>=threshold:
                        if not method_defined: method_defined=True; defs+=1
                        else: reheats+=1
                        route_hot=True; clean=0
            else:
                route_hot=False; clean=0
            rows.append({'ep':ep,'success':success,'wall_ms':(time.perf_counter()-t0)*1000,
                'planner_bytes':len(planner.encode()),'obs_pixels':m.obs_pixels-p0,'obs_count':m.obs_count-o0,
                'input_events':m.input_events-i0,'used_hot':used_hot,'fallback':fallback,'failed_hot':failed_hot,'injected':injected})
        return {'app':'xterm','strategy':strategy,'seed':seed,'rows':rows,'defs':defs,'route_failures':route_failures,'route_suspensions':susp,'fallbacks':fallbacks,'reheats':reheats}
    finally: s.close()


def navigate_universal(s,inp,target_wid,url):
    focus_id(s,target_wid); inp.chord('Control_L','l'); time.sleep(.020); inp.text(url); time.sleep(.020); inp.key('Return')
    return base.wait_until(lambda:url in title_for_id(s,target_wid),.6,.003)

def calibrate_omnibox(s,wid,m):
    # Calibration is observable and charged as one full-frame observation. The route stores the
    # successful app-specific click location; it is deliberately absolute so geometry drift can invalidate it.
    m.full(); x,y,w,h=geom(s,wid); return (x+min(400,max(250,w//2)), y+65)

def run_chromium(strategy,seed,episodes=24,learn_after=2,reheat_after=2,updates=(8,16)):
    s=base.XSession(); m=Metrics(); inp=Input(s,m); rows=[]
    method_defined=False; route_hot=False; clean=0; defs=0; route_failures=0; susp=0; fallbacks=0; reheats=0; cached=None
    urls=['chrome://settings/','chrome://history/','chrome://downloads/','chrome://bookmarks/']
    try:
        s.spawn(['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run','--no-default-browser-check',f'--user-data-dir={s.tmp}/profile','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        s.wait_window('Chromium',10); s.focus(chromium=True); time.sleep(.55); target=wid_for(s,'Chromium')
        original=geom(s,target)
        for ep in range(episodes):
            injected=None
            if ep in updates:
                # Visible geometry drift, never exposed as an epoch/id to the controller.
                if ep==updates[0]:
                    subprocess.run(['wmctrl','-ir',target,'-b','remove,maximized_vert,maximized_horz'],env=s.env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    subprocess.run(['wmctrl','-ir',target,'-e','0,180,180,900,580'],env=s.env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    injected='window_shift_down'
                else:
                    subprocess.run(['wmctrl','-ir',target,'-e',f'0,{original[0]},{original[1]},{original[2]},{original[3]}'],env=s.env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    injected='window_shift_back'
                time.sleep(.20); focus_id(s,target)
            url=urls[(ep+seed)%len(urls)]
            p0=m.obs_pixels; o0=m.obs_count; i0=m.input_events; t0=time.perf_counter()
            planner=call_payload('chromium',url) if method_defined else raw_payload('chromium',url)
            success=False; used_hot=route_hot; fallback=False; failed_hot=False
            if route_hot and cached is not None:
                click(s,cached[0],cached[1],m); time.sleep(.015); inp.chord('Control_L','a'); inp.text(url); inp.key('Return')
                success=base.wait_until(lambda:url in title_for_id(s,target),.45,.003)
                if not success:
                    failed_hot=True; route_failures+=1; fallbacks+=1; fallback=True; route_hot=False; clean=0
                    if strategy=='invalidate': method_defined=False; cached=None
                    else: susp+=1
            if not success:
                if not method_defined: m.full()
                success=navigate_universal(s,inp,target,url)
            if success:
                if not route_hot:
                    clean += 1
                    threshold=learn_after if not method_defined else reheat_after
                    if clean>=threshold:
                        if not method_defined: method_defined=True; defs+=1
                        else: reheats+=1
                        cached=calibrate_omnibox(s,target,m); route_hot=True; clean=0
            else:
                route_hot=False; clean=0
            rows.append({'ep':ep,'success':success,'wall_ms':(time.perf_counter()-t0)*1000,
                'planner_bytes':len(planner.encode()),'obs_pixels':m.obs_pixels-p0,'obs_count':m.obs_count-o0,
                'input_events':m.input_events-i0,'used_hot':used_hot,'fallback':fallback,'failed_hot':failed_hot,'injected':injected})
        return {'app':'chromium','strategy':strategy,'seed':seed,'rows':rows,'defs':defs,'route_failures':route_failures,'route_suspensions':susp,'fallbacks':fallbacks,'reheats':reheats}
    finally: s.close()

RUNNERS={'xterm':run_xterm,'chromium':run_chromium}
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--app',choices=RUNNERS,required=True); ap.add_argument('--strategy',choices=['invalidate','route_suspend'],required=True); ap.add_argument('--seed',type=int,default=1); ap.add_argument('--episodes',type=int,default=24); ap.add_argument('--out')
    a=ap.parse_args(); r=RUNNERS[a.app](a.strategy,a.seed,a.episodes); s=summarize(r); print(json.dumps(s,sort_keys=True),flush=True)
    if a.out: Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True))
