#!/usr/bin/env python3
import argparse, base64, ctypes, hashlib, importlib.util, importlib.util as iu, json, os, random, statistics, sys, threading, time, traceback, lzma
from pathlib import Path
HERE=Path(__file__).resolve().parent
UPSTREAM=HERE.parent/'quiet_watch_poll_period_v1'/'run_quiet_watch_poll_period_v1.py'
UPSTREAM_SHA256='d50233d9584876f119e78251728ccbf682a4b46b5485197ae60229970d9d520d'
SEED=28320260916
PAIR_COUNT=12
OFFSETS=(150,152,154,156,158,160)
PERIOD_MS=2

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_upstream():
    if digest(UPSTREAM)!=UPSTREAM_SHA256: raise RuntimeError('upstream source mismatch')
    spec=importlib.util.spec_from_file_location('q231',UPSTREAM); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def load_acquire():
    lib=ctypes.CDLL(str(HERE/'native_acquire.so')); lib.q_init.restype=ctypes.c_int; lib.q_open.argtypes=[ctypes.c_char_p]; lib.q_open.restype=ctypes.c_void_p; lib.q_close.argtypes=[ctypes.c_void_p]; lib.q_read.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t]; lib.q_read.restype=ctypes.c_int
    if not lib.q_init(): raise RuntimeError('XInitThreads failed')
    return lib

def load_predicate():
    cs=sorted(HERE.glob('native_predicate*.so'))
    if len(cs)!=1: raise RuntimeError(f'expected one native predicate extension, found {len(cs)}')
    spec=iu.spec_from_file_location('native_predicate',cs[0]); m=iu.module_from_spec(spec); spec.loader.exec_module(m); return m,cs[0]

def schedule():
    pairs=[]
    for i in range(PAIR_COUNT): pairs.append({'pair_id':f'nuisance-r{i:02d}','offset_ms':OFFSETS[i%len(OFFSETS)]})
    rng=random.Random(SEED); rng.shuffle(pairs)
    out=[]
    for k,p in enumerate(pairs):
        arms=('python_count','native_count') if k%2==0 else ('native_count','python_count')
        for arm in arms:
            out.append({'case_id':f"{p['pair_id']}-{arm}",'pair_id':p['pair_id'],'kind':'nuisance','offset_ms':p['offset_ms'],'period_ms':PERIOD_MS,'count_backend':arm,'order':len(out)})
    return out

class Reader:
    def __init__(self,old,lib,pred,display_name,arm):
        self.old=old; self.lib=lib; self.pred=pred; self.arm=arm; self.handle=lib.q_open(display_name.encode()); self.buf=ctypes.create_string_buffer(4096); self.samples=[]
        if not self.handle: raise RuntimeError('native display unavailable')
    def __call__(self,dpy,root):
        del dpy,root
        cpu0=time.thread_time_ns(); s=time.perf_counter_ns(); st=self.lib.q_read(self.handle,self.buf,4096); ae=time.perf_counter_ns(); cpu1=time.thread_time_ns()
        if st: raise RuntimeError(f'native capture failure {st}')
        raw=self.buf.raw; cs=time.perf_counter_ns(); count=self.old.roi_match_count(raw) if self.arm=='python_count' else self.pred.count_target(raw); ce=time.perf_counter_ns(); cpu2=time.thread_time_ns()
        self.samples.append({'start_ns':s,'acquire_end_ns':ae,'count_start_ns':cs,'count_end_ns':ce,'acquire_thread_cpu_ns':cpu1-cpu0,'count_thread_cpu_ns':cpu2-cpu1,'total_thread_cpu_ns':cpu2-cpu0})
        return s,ae,raw,count
    def close(self):
        if self.handle: self.lib.q_close(self.handle); self.handle=None

def run_one(old,lib,pred,display_name,case):
    rd=Reader(old,lib,pred,display_name,case['count_backend']); orig=old.acquire_roi; errs=[]; oldhook=threading.excepthook
    threading.excepthook=lambda x: errs.append(str(x.exc_value)); old.acquire_roi=rd
    try:
        r=old.run_case(case,display_name); r['observation_metrics']=rd.samples[:-1]; r['final_observation_metrics']=rd.samples[-1]; r['thread_errors']=errs; return r
    finally:
        old.acquire_roi=orig; threading.excepthook=oldhook
        try:
            d=old.display.Display(display_name); kc=d.keysym_to_keycode(old.XK.string_to_keysym('Right')); old.xtest.fake_input(d,old.X.KeyRelease,kc); d.sync(); d.close()
        except Exception: pass
        rd.close()

def integrity(r):
    if r['thread_errors'] or r['owner'].get('error') or r['watcher'].get('error'): return False
    if not r['owner'].get('verified_empty') or r['right_down_final']: return False
    kinds=[e['kind'] for e in r['events']]
    if kinds!=['app_key_press','app_key_release']: return False
    if r['final']['match_count']!=0 or r['derived']['detected']: return False
    if len(r['observation_metrics'])!=len(r['acquisitions']): return False
    return all(a['start_ns']==m['start_ns'] and a['end_ns']==m['acquire_end_ns'] for a,m in zip(r['acquisitions'],r['observation_metrics']))

def summarize(records):
    by={}
    for r in records: by.setdefault(r['case']['pair_id'],{})[r['case']['count_backend']]=r
    rows=[]
    for pid in sorted(by):
        p=by[pid]['python_count']; n=by[pid]['native_count']
        def metrics(r):
            ms=r['observation_metrics']; gaps=[(ms[i+1]['start_ns']-ms[i]['count_end_ns'])/1e6 for i in range(len(ms)-1)]
            return {'cpu_ms':sum(x['total_thread_cpu_ns'] for x in ms)/1e6,'wall_ms':sum(x['count_end_ns']-x['start_ns'] for x in ms)/1e6,'max_gap_ms':max(gaps),'samples':len(ms)}
        pm,nm=metrics(p),metrics(n)
        rows.append({'pair_id':pid,'python':pm,'native':nm,'cpu_ratio':nm['cpu_ms']/pm['cpu_ms'],'wall_ratio':nm['wall_ms']/pm['wall_ms'],'max_gap_ratio':nm['max_gap_ms']/pm['max_gap_ms']})
    cpu=[x['cpu_ratio'] for x in rows]; wall=[x['wall_ratio'] for x in rows]; gap=[x['max_gap_ratio'] for x in rows]
    stable=sum(x<=1.10 for x in gap)
    safety=all(integrity(r) for r in records)
    decision='REPLICATE_STABLE_SCOPED' if safety and statistics.median(cpu)<=0.80 and statistics.median(wall)<=0.90 and statistics.median(gap)<=1.10 and stable>=8 else ('FAIL_SAFETY_OR_SEMANTICS' if not safety else 'HOLD_GAP_STABILITY')
    return {'pairs':rows,'median_cpu_ratio':statistics.median(cpu),'median_wall_ratio':statistics.median(wall),'median_max_gap_ratio':statistics.median(gap),'pairs_gap_ratio_le_1_10':stable,'pair_count':len(rows),'safety_integrity_all':safety,'decision':decision}

def write(path,obj): Path(path).write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['preflight','formal'],required=True); ap.add_argument('--display',default=':95'); ap.add_argument('--out',required=True); a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=False)
    old=load_upstream(); lib=load_acquire(); pred,pbin=load_predicate(); sources={'run.py':digest(HERE/'run.py'),'native_acquire.c':digest(HERE/'native_acquire.c'),'native_predicate.c':digest(HERE/'native_predicate.c'),'upstream':digest(UPSTREAM)}
    payload={'schema':'quiet_watch_native_predicate_nuisance_repl_v1','mode':a.mode,'sources':sources,'binaries':{'native_acquire.so':digest(HERE/'native_acquire.so'),'native_predicate.so':digest(pbin)},'schedule':schedule(),'records':[],'errors':[]}
    if a.mode=='formal':
        pre=json.loads((HERE/'prereg.json').read_text())
        if pre['sources']!=sources or pre['binaries']!=payload['binaries'] or pre['schedule']!=payload['schedule']: raise RuntimeError('frozen prereg mismatch')
    cases=schedule() if a.mode=='formal' else [dict(schedule()[0],case_id='preflight-python',pair_id='preflight',count_backend='python_count',order=0),dict(schedule()[1],case_id='preflight-native',pair_id='preflight',count_backend='native_count',order=1)]
    try:
        for c in cases:
            r=run_one(old,lib,pred,a.display,c); payload['records'].append(r); write(out/'raw.json',payload)
            if not integrity(r): raise RuntimeError(f"integrity failure {c['case_id']}")
            print(c['case_id'],len(r['acquisitions']),flush=True)
        if a.mode=='formal': payload['summary']=summarize(payload['records'])
    except BaseException:
        payload['errors'].append(traceback.format_exc()); raise
    finally:
        write(out/'raw.json',payload); (out/'raw.json.xz').write_bytes(lzma.compress((out/'raw.json').read_bytes(),preset=9))
        if a.mode=='formal' and payload.get('summary'): write(out/'summary.json',payload['summary'])
if __name__=='__main__': main()
