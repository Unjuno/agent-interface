from __future__ import annotations
import argparse,hashlib,json,math,os,platform,subprocess,time
from pathlib import Path
from Xlib import X,display

W=320;H=240;PERIOD_NS=50_000_000;TTL_NS=200_000_000
CAPTURE_OFFSETS_MS=(-100,-50,0,50,100,150,200)
GUARD_PROJECTION_FIELDS=['capture_finished_ns','red_centroid_x']

def wait_file(p,timeout=4):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if p.exists(): return
        time.sleep(.005)
    raise RuntimeError(f'timeout {p}')

def normalize(raw):
    if isinstance(raw,bytes): data=raw
    elif isinstance(raw,(bytearray,memoryview)): data=bytes(raw)
    elif isinstance(raw,str): data=raw.encode('latin-1')
    else: raise TypeError(type(raw).__name__)
    if len(data)!=W*H*4: raise ValueError(f'payload len {len(data)}')
    return data

def red_centroid(data):
    candidates=[]
    for ri,gi,bi,name in ((2,1,0,'BGRX'),(0,1,2,'RGBX')):
        xs=[]
        for i in range(W*H):
            p=i*4
            if data[p+ri]>=200 and data[p+gi]<=80 and data[p+bi]<=80:
                xs.append(i%W)
        candidates.append((len(xs),None if not xs else sum(xs)/len(xs),name))
    count,cx,fmt=max(candidates,key=lambda t:t[0])
    if count<500 or cx is None: raise RuntimeError(f'red pixels insufficient {candidates}')
    return count,cx,fmt

def sgn(v,eps=.25):
    return 1 if v>eps else -1 if v<-eps else 0

def pct(xs,p):
    if not xs:return None
    ys=sorted(xs); k=(len(ys)-1)*p; lo=math.floor(k); hi=math.ceil(k)
    return ys[lo] if lo==hi else ys[lo]*(hi-k)+ys[hi]*(k-lo)

def one_session(root,case_id,display_num,initial_dir,reversal_offset_ms,construction=False):
    ddir=root/f"{'construction' if construction else 'formal'}_{case_id:02d}"; ddir.mkdir(parents=True,exist_ok=True)
    ready=ddir/'ready.json'; flog=ddir/'fixture.jsonl'; control=ddir/'control.json'
    env=os.environ.copy(); env['DISPLAY']=f':{display_num}'; env['XAUTHORITY']=str(ddir/'xauth'); (ddir/'xauth').touch()
    xv=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    fix=None; d=None
    try:
        wait_file(Path(f'/tmp/.X11-unix/X{display_num}'))
        fix=subprocess.Popen(['python',str(root/'fixture.py'),'--ready',str(ready),'--log',str(flog),'--control',str(control)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        wait_file(ready)
        score_start=time.perf_counter_ns()+300_000_000
        control.write_text(json.dumps({'score_start_ns':score_start,'initial_dir':initial_dir,'reversal_offset_ms':reversal_offset_ms}))
        oldD=os.environ.get('DISPLAY');oldA=os.environ.get('XAUTHORITY');os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY']
        d=display.Display(env['DISPLAY']);r=d.screen().root
        captures=[];exceptions=[]
        for off_ms in CAPTURE_OFFSETS_MS:
            scheduled=score_start+off_ms*1_000_000
            now=time.perf_counter_ns()
            if now<scheduled: time.sleep((scheduled-now)/1e9)
            b=time.perf_counter_ns()
            try:
                data=normalize(r.get_image(0,0,W,H,X.ZPixmap,0xffffffff).data)
                count,cx,fmt=red_centroid(data)
                a=time.perf_counter_ns()
                captures.append({'offset_ms':off_ms,'scheduled_ns':scheduled,'capture_started_ns':b,'capture_finished_ns':a,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'red_pixel_count':count,'red_centroid_x':cx,'pixel_format_interpretation':fmt})
            except Exception as e:
                exceptions.append(repr(e));break
        d.sync();d.close();d=None
        if oldD is None:os.environ.pop('DISPLAY',None)
        else:os.environ['DISPLAY']=oldD
        if oldA is None:os.environ.pop('XAUTHORITY',None)
        else:os.environ['XAUTHORITY']=oldA
        fix.wait(timeout=2)
        log=[json.loads(x) for x in flog.read_text().splitlines() if x.strip()]
        rev=[x for x in log if x.get('kind')=='reversal_applied']
        reversal_applied_ns=rev[0]['t_ns'] if rev else None
        by_off={c['offset_ms']:c for c in captures}
        if -50 not in by_off or 0 not in by_off: raise RuntimeError('missing pre/current capture')
        initial_observed_dir=sgn(by_off[0]['red_centroid_x']-by_off[-50]['red_centroid_x'])
        guard_yield_ns=None; guard_trigger_pair=None
        prev=by_off[0]
        for off in (50,100,150):
            cur=by_off.get(off)
            if cur is None: break
            obs=sgn(cur['red_centroid_x']-prev['red_centroid_x'])
            if obs!=0 and initial_observed_dir!=0 and obs!=initial_observed_dir:
                guard_yield_ns=cur['capture_finished_ns'];guard_trigger_pair=[prev['offset_ms'],cur['offset_ms']];break
            prev=cur
        ttl_ns=score_start+TTL_NS
        false_invalidation=(reversal_offset_ms is None and guard_yield_ns is not None and guard_yield_ns<ttl_ns)
        detected_before_ttl=(reversal_offset_ms is not None and guard_yield_ns is not None and guard_yield_ns<ttl_ns)
        baseline_stale_ms=None;guard_stale_ms=None;reduction_ms=None;latency_ms=None
        if reversal_applied_ns is not None:
            baseline_stale_ms=max(0,(ttl_ns-reversal_applied_ns)/1e6)
            effective=min(ttl_ns,guard_yield_ns) if guard_yield_ns is not None else ttl_ns
            guard_stale_ms=max(0,(effective-reversal_applied_ns)/1e6)
            reduction_ms=baseline_stale_ms-guard_stale_ms
            latency_ms=None if guard_yield_ns is None else (guard_yield_ns-reversal_applied_ns)/1e6
        return {'case_id':case_id,'display':display_num,'initial_dir':initial_dir,'reversal_offset_ms':reversal_offset_ms,'score_start_ns':score_start,'ttl_ns':ttl_ns,'guard_projection_fields':GUARD_PROJECTION_FIELDS,'captures':captures,'capture_exceptions':exceptions,'initial_observed_dir':initial_observed_dir,'guard_yield_ns':guard_yield_ns,'guard_trigger_pair':guard_trigger_pair,'false_invalidation':false_invalidation,'detected_before_ttl':detected_before_ttl,'reversal_applied_ns':reversal_applied_ns,'reversal_latency_ms':latency_ms,'ttl_only_stale_exposure_ms':baseline_stale_ms,'guard_stale_exposure_ms':guard_stale_ms,'stale_exposure_reduction_ms':reduction_ms,'fixture_event_count':len(log)}
    finally:
        if d is not None:
            try:d.close()
            except Exception:pass
        if fix is not None and fix.poll() is None:
            fix.kill();fix.wait()
        if xv.poll() is None:
            xv.terminate()
            try:xv.wait(timeout=.3)
            except Exception:xv.kill();xv.wait()

def build_cases(construction):
    if construction:return [(1,1,25),(2,-1,None)]
    cases=[];cid=1
    for rep in range(2):
        for d in (1,-1):
            for off in (5,15,25,35,45):
                cases.append((cid,d,off));cid+=1
    for i in range(10):
        cases.append((cid,1 if i%2==0 else -1,None));cid+=1
    return cases

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--construction',action='store_true');a=ap.parse_args();out=Path(a.out);root=Path(__file__).parent
    if out.exists():raise SystemExit('result exists')
    cases=build_cases(a.construction);rows=[];base_display=1030 if a.construction else 1040
    for idx,(cid,d,off) in enumerate(cases):rows.append(one_session(root,cid,base_display+idx,d,off,a.construction))
    rev=[x for x in rows if x['reversal_offset_ms'] is not None];cont=[x for x in rows if x['reversal_offset_ms'] is None]
    lats=[x['reversal_latency_ms'] for x in rev if x['reversal_latency_ms'] is not None]
    reds=[x['stale_exposure_reduction_ms'] for x in rev if x['stale_exposure_reduction_ms'] is not None]
    result={'task':'TEMPORAL-SPECULATION-X11-REVERSAL-INVALIDATION-A2-20260918-002','construction':a.construction,'formal':not a.construction,'formal_invocations':0 if a.construction else 1,'reruns':0,'authority_grants':0,'input_actions':0,'platform':platform.platform(),'python':platform.python_version(),'rows':rows,'summary':{'reversal_cases':len(rev),'continue_cases':len(cont),'detected_before_ttl':sum(bool(x['detected_before_ttl']) for x in rev),'false_invalidations':sum(bool(x['false_invalidation']) for x in cont),'capture_exceptions':sum(len(x['capture_exceptions']) for x in rows),'reversal_latency_ms':{'p50':pct(lats,.5),'p95':pct(lats,.95),'max':max(lats) if lats else None},'stale_exposure_reduction_ms':{'median':pct(reds,.5),'min':min(reds) if reds else None}}}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
