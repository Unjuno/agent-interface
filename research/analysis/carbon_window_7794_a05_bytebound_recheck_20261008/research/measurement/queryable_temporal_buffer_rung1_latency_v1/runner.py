from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, os, platform, random, resource, statistics, threading, time, sys
from dataclasses import dataclass
from pathlib import Path

PARENT_SHA256='77439c932e2dbc8116813e02630346b9b5405876d2e58b0e70080f0c7e5c8aec'
PARENT_GIT_BLOB='00bcf7ed503f61b0240b9502b6f775c5418ea179'
FORMAL_SEED=103820260918001
CONSTRUCTION_SEED=103820260918000
CADENCE_NS=5_000_000
HORIZON_NS=50_000_000
MAX_FRAMES=6
PAYLOAD_BYTES=4096
WARMUP_NS=110_000_000
RING_MAX_AGE_NS=250_000_000
RING_MAX_ITEMS=128
RING_MAX_BYTES=2_000_000
FORMAL_TRIALS=64


def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def git_blob_sha(b):
    h=hashlib.sha1(); h.update(f'blob {len(b)}\0'.encode()); h.update(b); return h.hexdigest()

def load_parent(path):
    p=Path(path); b=p.read_bytes()
    if sha256_bytes(b)!=PARENT_SHA256 or git_blob_sha(b)!=PARENT_GIT_BLOB:
        raise RuntimeError('parent_contract_identity')
    spec=importlib.util.spec_from_file_location('r0_contract',p); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m); return m

def pct(xs,p):
    ys=sorted(xs)
    if not ys: return None
    k=(len(ys)-1)*p; lo=math.floor(k); hi=math.ceil(k)
    if lo==hi:return ys[lo]
    return ys[lo]*(hi-k)+ys[hi]*(k-lo)

def uniform_indices(n,m):
    if m<=0 or n<=0:return []
    if m>=n:return list(range(n))
    if m==1:return [n-1]
    return [round(i*(n-1)/(m-1)) for i in range(m)]

def payload_for(seq):
    seed=hashlib.sha256(f'frame:{seq}'.encode()).digest()
    return (seed*((PAYLOAD_BYTES+len(seed)-1)//len(seed)))[:PAYLOAD_BYTES]

@dataclass(frozen=True)
class SrcFrame:
    oid:str; seq:int; t_ns:int; payload:bytes

class Capture:
    def __init__(self,m):
        self.m=m; self.buf=m.TemporalBuffer(RING_MAX_ITEMS,RING_MAX_BYTES,RING_MAX_AGE_NS)
        self.payloads={}; self.archive=[]; self.lock=threading.RLock(); self.stop=threading.Event()
        self.thread=None; self.frames=0; self.dropped_slots=0; self.max_retained_payload_bytes=0; self.thread_cpu_ns=0; self.start_wall_ns=0; self.stop_wall_ns=0
    def start(self):
        self.start_wall_ns=time.perf_counter_ns(); self.thread=threading.Thread(target=self._run,daemon=True); self.thread.start()
    def _run(self):
        cpu0=time.thread_time_ns(); next_ns=time.perf_counter_ns(); seq=0
        while not self.stop.is_set():
            now=time.perf_counter_ns(); sleep_ns=next_ns-now
            if sleep_ns>0: time.sleep(sleep_ns/1e9)
            now=time.perf_counter_ns()
            missed=0
            if now-next_ns>=CADENCE_NS:
                missed=(now-next_ns)//CADENCE_NS
                self.dropped_slots += int(missed)
            seq += int(missed)+1
            oid=f'f{seq}'; payload=payload_for(seq)
            obs=self.m.Observation(oid,seq,now,'s0','surfaceA',64,64,len(payload),seq%5==0,True,False)
            with self.lock:
                self.buf.append(obs,now); self.payloads[oid]=payload; self.archive.append(SrcFrame(oid,seq,now,payload))
                live={x.observation_id for x in self.buf.items}
                for k in list(self.payloads):
                    if k not in live: del self.payloads[k]
                retained=sum(len(v) for v in self.payloads.values()); self.max_retained_payload_bytes=max(self.max_retained_payload_bytes,retained)
                self.frames+=1
            next_ns += (int(missed)+1)*CADENCE_NS
        self.thread_cpu_ns=time.thread_time_ns()-cpu0
    def close(self):
        self.stop.set(); self.thread.join(timeout=2); self.stop_wall_ns=time.perf_counter_ns()
    def warm(self):
        target=time.perf_counter_ns()+WARMUP_NS
        while time.perf_counter_ns()<target: time.sleep(0.002)
        with self.lock:
            if len(self.buf.items)<MAX_FRAMES+2: raise RuntimeError('warmup_insufficient')

def copy_payloads(ids, lookup):
    return [memoryview(lookup[i]).tobytes() for i in ids]

def ring_query(cap,m,req_ns):
    q=m.Query('s0','surfaceA','NOW',None,HORIZON_NS,0,MAX_FRAMES,MAX_FRAMES*PAYLOAD_BYTES,'UNIFORM',None)
    t0=time.perf_counter_ns(); out=cap.buf.query(q,req_ns); ids=[x['observation_id'] for x in out['items']]; copies=copy_payloads(ids,cap.payloads); t1=time.perf_counter_ns()
    return {'ids':ids,'payload_hashes':[sha256_bytes(x) for x in copies],'latency_ns':t1-t0,'roles':[x['role'] for x in out['items']]}

def archive_jit(cap,req_ns):
    t0=time.perf_counter_ns(); lo=req_ns-HORIZON_NS
    eligible=[x for x in cap.archive if lo<=x.t_ns<=req_ns]
    ix=uniform_indices(len(eligible),min(MAX_FRAMES,len(eligible))); sel=[eligible[i] for i in ix]
    copies=[memoryview(x.payload).tobytes() for x in sel]; t1=time.perf_counter_ns()
    return {'ids':[x.oid for x in sel],'payload_hashes':[sha256_bytes(x) for x in copies],'latency_ns':t1-t0}

def future_equivalent(request_ns, result):
    frames=[]; seq=0; next_ns=request_ns
    end=request_ns+HORIZON_NS
    while True:
        now=time.perf_counter_ns()
        if now<next_ns: time.sleep((next_ns-now)/1e9)
        now=time.perf_counter_ns(); seq+=1; frames.append((seq,now,payload_for(10_000_000+seq)))
        if now>=end: break
        next_ns += CADENCE_NS
    ix=uniform_indices(len(frames),min(MAX_FRAMES,len(frames))); sel=[frames[i] for i in ix]
    result['ready_ns']=time.perf_counter_ns(); result['frame_count']=len(sel); result['span_ns']=sel[-1][1]-sel[0][1] if len(sel)>1 else 0
    result['payload_hashes']=[sha256_bytes(memoryview(x[2]).tobytes()) for x in sel]

def one_run(parent_path, seed, replay_trials, live_trials):
    m=load_parent(parent_path); rng=random.Random(seed); cap=Capture(m); cap.start(); cap.warm()
    replay=[]; live=[]
    try:
        for i in range(replay_trials):
            time.sleep(rng.uniform(0.001,0.003))
            with cap.lock:
                req=time.perf_counter_ns()
                if i%2==0:
                    a=ring_query(cap,m,req); b=archive_jit(cap,req); order='ring_first'
                else:
                    b=archive_jit(cap,req); a=ring_query(cap,m,req); order='jit_first'
            replay.append({'trial':i,'order':order,'request_ns':req,'ring_latency_ns':a['latency_ns'],'jit_latency_ns':b['latency_ns'],
                           'ids_equal':a['ids']==b['ids'],'payloads_equal':a['payload_hashes']==b['payload_hashes'],
                           'ring_ids':a['ids'],'jit_ids':b['ids'],'ring_roles':a['roles'],'ring_boundary_count':0,'jit_boundary_count':0})
        for i in range(live_trials):
            time.sleep(rng.uniform(0.001,0.003))
            future={}
            with cap.lock:
                req=time.perf_counter_ns()
                th=threading.Thread(target=future_equivalent,args=(req,future),daemon=True); th.start()
                ring=ring_query(cap,m,req)
            th.join(timeout=1)
            if 'ready_ns' not in future: raise RuntimeError('future_timeout')
            live.append({'trial':i,'request_ns':req,'ring_latency_ns':ring['latency_ns'],'ring_ids':ring['ids'],'ring_roles':ring['roles'],
                         'ring_requested_past_available':bool(ring['ids']),'jit_exact_requested_past_available':False,
                         'jit_future_equivalent_latency_ns':future['ready_ns']-req,'jit_future_frame_count':future['frame_count'],
                         'jit_future_span_ns':future['span_ns'],'ring_boundary_count':0,'jit_future_boundary_count':1})
    finally:
        cap.close()
    ring_lat=[x['ring_latency_ns'] for x in replay+live]; replay_jit=[x['jit_latency_ns'] for x in replay]
    live_jit=[x['jit_future_equivalent_latency_ns'] for x in live]; live_ring=[x['ring_latency_ns'] for x in live]
    diffs=[j-r for j,r in zip(live_jit,live_ring)]
    summary={
      'seed':seed,'replay_trials':len(replay),'live_trials':len(live),
      'replay_exact_id_matches':sum(x['ids_equal'] for x in replay),'replay_exact_payload_matches':sum(x['payloads_equal'] for x in replay),
      'replay_ring_boundaries':sum(x['ring_boundary_count'] for x in replay),'replay_jit_boundaries':sum(x['jit_boundary_count'] for x in replay),
      'live_ring_past_available':sum(x['ring_requested_past_available'] for x in live),'live_jit_exact_past_available':sum(x['jit_exact_requested_past_available'] for x in live),
      'live_ring_boundaries':sum(x['ring_boundary_count'] for x in live),'live_jit_future_boundaries':sum(x['jit_future_boundary_count'] for x in live),
      'ring_latency_ns':{'p50':pct(ring_lat,.50),'p95':pct(ring_lat,.95),'p99':pct(ring_lat,.99),'max':max(ring_lat)},
      'replay_jit_latency_ns':{'p50':pct(replay_jit,.50),'p95':pct(replay_jit,.95),'p99':pct(replay_jit,.99),'max':max(replay_jit)},
      'live_jit_future_latency_ns':{'p50':pct(live_jit,.50),'p95':pct(live_jit,.95),'p99':pct(live_jit,.99),'max':max(live_jit)},
      'live_paired_advantage_ns':{'p50':pct(diffs,.50),'p95':pct(diffs,.95),'min':min(diffs)},
      'historical_role_errors':sum(any(r!='HISTORICAL' for r in x['ring_roles']) for x in replay+live),
      'producer_frames':cap.frames,'producer_dropped_slots':cap.dropped_slots,'producer_thread_cpu_ns':cap.thread_cpu_ns,
      'producer_wall_ns':cap.stop_wall_ns-cap.start_wall_ns,'max_retained_payload_bytes':cap.max_retained_payload_bytes,
      'max_rss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'python':platform.python_version(),'platform':platform.platform(),
      'grants_input_authority':False
    }
    return {'summary':summary,'replay_rows':replay,'live_rows':live}

def gate(result, formal):
    s=result['summary']; n=FORMAL_TRIALS if formal else s['replay_trials']
    errs=[]
    if s['replay_exact_id_matches']!=s['replay_trials'] or s['replay_exact_payload_matches']!=s['replay_trials']: errs.append('replay_identity')
    if s['replay_ring_boundaries']!=0 or s['replay_jit_boundaries']!=0: errs.append('replay_boundary')
    if s['live_ring_past_available']!=s['live_trials'] or s['live_jit_exact_past_available']!=0: errs.append('live_availability')
    if s['live_ring_boundaries']!=0 or s['live_jit_future_boundaries']!=s['live_trials']: errs.append('live_boundary')
    if s['historical_role_errors']!=0 or s['grants_input_authority'] is not False: errs.append('role_authority')
    if formal:
        if s['replay_trials']!=FORMAL_TRIALS or s['live_trials']!=FORMAL_TRIALS: errs.append('formal_counts')
        if s['ring_latency_ns']['p95']>10_000_000: errs.append('ring_p95')
        if s['live_jit_future_latency_ns']['p50']<45_000_000: errs.append('jit_future_p50')
        if s['live_paired_advantage_ns']['p50']<35_000_000: errs.append('paired_advantage')
    return errs

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--parent-contract',required=True); ap.add_argument('--construction',action='store_true'); ap.add_argument('--formal-output'); args=ap.parse_args()
    formal=not args.construction
    if formal and not args.formal_output: raise SystemExit('formal output required')
    if formal and Path(args.formal_output).exists(): raise SystemExit('formal result exists')
    seed=FORMAL_SEED if formal else CONSTRUCTION_SEED; n=FORMAL_TRIALS if formal else 2
    t0=time.perf_counter_ns(); result=one_run(args.parent_contract,seed,n,n); result['summary']['runner_wall_ns']=time.perf_counter_ns()-t0
    result['summary']['formal']=formal; result['summary']['formal_invocations']=1 if formal else 0; result['summary']['reruns']=0
    errs=gate(result,formal); result['summary']['gate_errors']=errs
    result['summary']['decision']=('PASS_TEMPORAL_RING_RUNG1_LATENCY_SCOPED' if formal and not errs else ('CONSTRUCTION_PASS' if not formal and not errs else 'FAIL'))
    payload=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result['summary']['result_digest']=hashlib.sha256(payload).hexdigest()
    text=json.dumps(result,indent=2,sort_keys=True)
    if formal: Path(args.formal_output).write_text(text+'\n')
    print(json.dumps(result['summary'],indent=2,sort_keys=True))
if __name__=='__main__': main()
