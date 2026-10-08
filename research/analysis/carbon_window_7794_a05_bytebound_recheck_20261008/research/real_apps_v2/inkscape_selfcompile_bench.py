#!/usr/bin/env python3
import argparse, json, os, sys, time, random, statistics, subprocess, xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'real_apps_v1'))
import real_app_suite_v1 as base
from PIL import ImageGrab
import numpy as np

base.MODE='sparse_reactive'
base.PRESS_DWELL_MS=5.0
W,H=1280,800


def red_bbox(im, offset=(0,0), reject_edge=False):
    a=np.asarray(im.convert('RGB'))
    m=(a[:,:,0]>175)&(a[:,:,1]<120)&(a[:,:,2]<120)
    ys,xs=np.nonzero(m)
    if xs.size < 320:
        return None
    x0=int(xs.min());x1=int(xs.max());y0=int(ys.min());y1=int(ys.max())
    if reject_edge and (x0<=2 or y0<=2 or x1>=a.shape[1]-3 or y1>=a.shape[0]-3):
        return None
    ox,oy=offset
    return (x0+ox,y0+oy,x1+ox,y1+oy)


def center(b): return ((b[0]+b[2])//2,(b[1]+b[3])//2)

def shift_bbox(b,dx,dy=0): return (b[0]+dx,b[1]+dy,b[2]+dx,b[3]+dy)

def expand_bbox(b, margin=36):
    return (max(0,b[0]-margin),max(0,b[1]-margin),min(W,b[2]+margin),min(H,b[3]+margin))

class Obs:
    def __init__(self):
        self.count=0;self.pixels=0;self.ms=[]
    def full(self):
        t=time.perf_counter();im=ImageGrab.grab();dt=(time.perf_counter()-t)*1000
        self.count+=1;self.pixels+=im.width*im.height;self.ms.append(dt);return im
    def roi(self,b):
        x0,y0,x1,y1=map(int,b)
        t=time.perf_counter();im=ImageGrab.grab(bbox=(x0,y0,x1,y1));dt=(time.perf_counter()-t)*1000
        self.count+=1;self.pixels+=im.width*im.height;self.ms.append(dt);return im,(x0,y0)


def xpos(path):
    try:
        rt=ET.parse(path).getroot();q=rt.find('{http://www.w3.org/2000/svg}rect')
        return float(q.attrib.get('x','nan'))
    except Exception:return None


def full_acquire(obs):
    im=obs.full(); crop=im.crop((180,180,820,700)); return red_bbox(crop,(180,180))


def roi_acquire(obs, cached, margin=38):
    rb=expand_bbox(cached,margin)
    im,off=obs.roi(rb)
    return red_bbox(im,off,reject_edge=True)


def wait_effect(obs, old_bbox, dx, prefer_roi=True, timeout=.30):
    # Effect verification must not assume exact motor gain. Observe the swept
    # region containing both the pre-drag target and the nominal endpoint.
    pred=shift_bbox(old_bbox,dx)
    union=(min(old_bbox[0],pred[0]),min(old_bbox[1],pred[1]),
           max(old_bbox[2],pred[2]),max(old_bbox[3],pred[3]))
    watch=expand_bbox(union,52)
    end=time.perf_counter()+timeout
    while time.perf_counter()<end:
        b=None
        if prefer_roi:
            im,off=obs.roi(watch)
            b=red_bbox(im,off,reject_edge=True)
        if b is None:
            b=full_acquire(obs)
        if b is not None:
            oc=center(old_bbox); nc=center(b)
            delta=nc[0]-oc[0]
            if (dx>0 and delta >= 2) or (dx<0 and delta <= -2):
                return b
        time.sleep(.002)
    return None


def raw_payload(dx, bbox):
    x,y=center(bbox)
    return f'OBSERVE;ACQUIRE red;CHORD CTRL A;DRAG {x} {y} {x+dx} {y};WAIT_UPDATE;CHORD CTRL S;VERIFY'

def method_payload(dx, workflow=True):
    return f'CALL MOVE_SAVE({dx})' if workflow else f'CALL MOVE({dx});CALL SAVE()'


def run(strategy='universal', seed=1, episodes=36, learn_after=2, reheat_after=2, updates=(10,20)):
    rng=random.Random(seed)
    s=base.XSession(); p=s.tmp/'shape.svg'
    p.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect id="r" x="50" y="50" width="40" height="30" fill="red"/></svg>')
    obs=Obs(); rows=[]
    method_active=False; method_defined=False; clean_raw=0; cached=None; invalidations=0; reanchors=0; fallbacks=0; defs=0
    update_keys=['plus','minus']; update_i=0
    try:
        s.spawn(['inkscape',str(p)],stdout=open(os.devnull,'w'),stderr=open(os.devnull,'w'))
        s.wait_window('shape.svg',10);s.focus('shape.svg');time.sleep(1.0)
        d=base.Driver(s,0)
        for ep in range(episodes):
            # Exogenous visible UI change; controller does not get epoch/update id.
            injected=None
            if ep in updates:
                injected=update_keys[update_i%len(update_keys)]; update_i+=1
                d.key(injected); time.sleep(.12)
            dx=30 if ep%2==0 else -30
            ep_obs0=obs.pixels; ep_n0=obs.count; ep_input0=d.input_events
            t0=time.perf_counter(); used_method=method_active; fallback=False; invalidated=False; reanchored=False

            # Acquisition / method resolution.
            b=None
            if method_active and cached is not None:
                b=roi_acquire(obs,cached)
                if b is None:
                    fallbacks+=1; fallback=True
                    b=full_acquire(obs)
                    if strategy in ('invalidate','route_suspend'):
                        method_active=False; clean_raw=0; invalidations+=1; invalidated=True
                        if strategy=='invalidate': method_defined=False
                    elif strategy=='reanchor' and b is not None:
                        cached=b;reanchors+=1;reanchored=True
            if b is None:
                b=full_acquire(obs)
            if b is None:
                rows.append({'ep':ep,'success':False,'reason':'acquire','injected':injected});continue

            planner_method = (strategy=='route_suspend' and method_defined) or (used_method and not invalidated)
            planner = method_payload(dx,workflow=True) if planner_method else raw_payload(dx,b)
            planner_bytes=len(planner.encode())

            old_x=xpos(p)
            # Selection is an execution precondition, not a cacheable fact unless
            # it has an explicit observable guard. Ctrl+A is idempotent and cheap, so
            # every method invocation re-establishes it before the dependent drag.
            d.chord('Control_L','a'); time.sleep(.10)
            x0,y0=center(b)
            d.drag(x0,y0,x0+dx,y0)
            nb=wait_effect(obs,b,dx,prefer_roi=True)
            if nb is None:
                # semantic/effect failure: invalidate then one universal retry
                if method_active:
                    invalidations+=1;invalidated=True;method_active=False;clean_raw=0
                    if strategy=='invalidate': method_defined=False
                fb=full_acquire(obs);fallback=True;fallbacks+=1
                if fb is not None:
                    d.chord('Control_L','a');time.sleep(.10);x1,y1=center(fb);d.drag(x1,y1,x1+dx,y1);nb=wait_effect(obs,fb,dx,True)
            d.chord('Control_L','s')
            ok_file=base.wait_until(lambda: (xpos(p) is not None and old_x is not None and ((dx>0 and xpos(p)>old_x+.05) or (dx<0 and xpos(p)<old_x-.05))),1.0,.005)
            success=bool(nb is not None and ok_file)
            wall=(time.perf_counter()-t0)*1000

            if success:
                cached=nb
                if not method_active:
                    clean_raw+=1
                    threshold = learn_after if not method_defined else reheat_after
                    if strategy!='universal' and clean_raw>=threshold:
                        method_active=True
                        if not method_defined:
                            method_defined=True; defs+=1
                # method stays active after local reanchor; only effect failures kill it.
            else:
                method_active=False;clean_raw=0

            rows.append({
                'ep':ep,'success':success,'wall_ms':wall,'planner_bytes':planner_bytes,
                'obs_pixels':obs.pixels-ep_obs0,'observations':obs.count-ep_n0,
                'input_events':d.input_events-ep_input0,'used_method':used_method,
                'method_active_after':method_active,'fallback':fallback,'invalidated':invalidated,
                'reanchored':reanchored,'injected':injected,'dx':dx,'x':xpos(p),
            })
        return {'strategy':strategy,'seed':seed,'episodes':episodes,'rows':rows,
                'invalidations':invalidations,'reanchors':reanchors,'fallbacks':fallbacks,'defs':defs}
    finally:s.close()


def summarize(run):
    rs=run['rows']; good=[r for r in rs if r.get('success')]
    vals=lambda k:[r[k] for r in good if k in r]
    q=lambda a,p: sorted(a)[min(len(a)-1,int((len(a)-1)*p))] if a else float('nan')
    return {
        'strategy':run['strategy'],'seed':run['seed'],'n':len(rs),'success':sum(bool(r.get('success')) for r in rs),
        'wall_p50_ms':statistics.median(vals('wall_ms')) if good else None,
        'wall_p95_ms':q(vals('wall_ms'),.95),'wall_p99_ms':q(vals('wall_ms'),.99),
        'obs_mpix_mean':statistics.mean(vals('obs_pixels'))/1e6 if good else None,
        'obs_count_mean':statistics.mean(vals('observations')) if good else None,
        'planner_bytes_mean':statistics.mean(vals('planner_bytes')) if good else None,
        'input_events_mean':statistics.mean(vals('input_events')) if good else None,
        'fallbacks':run['fallbacks'],'invalidations':run['invalidations'],'reanchors':run['reanchors'],'defs':run['defs'],
    }

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--strategy',choices=['universal','invalidate','reanchor','route_suspend'],required=True)
    ap.add_argument('--seed',type=int,default=1);ap.add_argument('--episodes',type=int,default=36);ap.add_argument('--out')
    a=ap.parse_args();r=run(a.strategy,a.seed,a.episodes);s=summarize(r);print(json.dumps(s,sort_keys=True),flush=True)
    if a.out:Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True))
