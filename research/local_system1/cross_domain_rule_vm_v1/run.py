#!/usr/bin/env python3
import argparse,gc,hashlib,json,os,platform,statistics,time
from pathlib import Path
import numpy as np
import decision_900 as d900
from rule_vm import Request,Decision,eval_program,CHROMIUM_PROGRAM,OPENTTD_PROGRAM,CHROMIUM_ALLOWED,OPENTTD_ALLOWED

N_UNIQUE=8192
WARMUP=1024
TIMING_N=65536

def pct(vals,p): return float(np.percentile(np.asarray(vals,dtype=np.float64),p,method='linear'))
def stats(vals): return {'n':len(vals),'p50_us':pct(vals,50)/1000,'p95_us':pct(vals,95)/1000,'p99_us':pct(vals,99)/1000,'max_us':max(vals)/1000,'mean_us':statistics.fmean(vals)/1000}
def h(items): return hashlib.sha256(json.dumps(items,separators=(',',':'),sort_keys=True).encode()).hexdigest()

def chrom_request_from_x(x):
    ns,nc,cp,np_,s,w,g,l=[bool(int(v)) for v in x]
    return Request('chromium_route',{'need_scale':ns,'need_center':nc,'ctrl_capability':cp,'native_capability':np_,'session_current':s,'surface_current':w,'geometry_current':g,'handle_live':l},CHROMIUM_ALLOWED,frozenset({'CAPABILITY','CURRENTNESS'}))

def chrom_native_label(payload):
    x=d900.extract_validate(payload); return d900.LABELS[d900.truth(x)]
def chrom_vm_label(payload):
    x=d900.extract_validate(payload); out=eval_program(chrom_request_from_x(x),CHROMIUM_PROGRAM)
    if out.kind=='EXECUTE': return out.value
    if out.value=='STALE_CAPABILITY': return 'STALE_CAPABILITY'
    return 'UNSUPPORTED'

def make_chromium():
    rng=np.random.default_rng(9341701); rows=[]
    for nonce in range(N_UNIQUE):
        bits=[int(v) for v in rng.integers(0,2,size=7)]
        hs=d900.HSTAT[int(rng.integers(0,len(d900.HSTAT)))]
        rows.append(d900.make_payload(bits,hs,nonce))
    assert len(set(rows))==N_UNIQUE
    return rows

def openttd_native(row):
    if not row.get('binding_current',False): return Decision('YIELD','BINDING_CHANGED')
    r=row.get('guard_reason')
    if r=='met': return Decision('EXECUTE','CONTINUE_PROGRAM')
    if r=='target_not_reached': return Decision('YIELD','TARGET_NOT_REACHED')
    return Decision('YIELD','UNKNOWN_EVIDENCE')
def openttd_vm(row):
    req=Request('openttd_guard',{'binding_current':bool(row.get('binding_current',False)),'guard_reason':row.get('guard_reason')},OPENTTD_ALLOWED,frozenset({'CURRENT_BINDING','LOCAL_GUARD'}))
    return eval_program(req,OPENTTD_PROGRAM)

def timed(fn,rows):
    for i in range(WARMUP): fn(rows[i%len(rows)])
    vals=[]; outs=[]
    gc.disable()
    try:
        for i in range(TIMING_N):
            row=rows[i%len(rows)]; t0=time.perf_counter_ns(); out=fn(row); t1=time.perf_counter_ns(); vals.append(t1-t0); outs.append(out if isinstance(out,str) else [out.kind,out.value])
    finally: gc.enable()
    return stats(vals),h(outs)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['construction','formal'],required=True); ap.add_argument('--fixture',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    fixture=json.loads(Path(a.fixture).read_text())
    if a.mode=='construction':
        toys=[{'binding_current':True,'guard_reason':'met'},{'binding_current':True,'guard_reason':'other'},{'binding_current':False,'guard_reason':'met'}]
        assert [[openttd_vm(x).kind,openttd_vm(x).value] for x in toys]==[['EXECUTE','CONTINUE_PROGRAM'],['YIELD','UNKNOWN_EVIDENCE'],['YIELD','BINDING_CHANGED']]
        p1=d900.make_payload([1,1,1,0,1,1,1],'LIVE',1); p2=d900.make_payload([1,0,0,1,0,1,1],'LIVE',2); p3=d900.make_payload([0,0,1,1,1,1,1],'LIVE',3)
        assert [chrom_vm_label(p1),chrom_vm_label(p2),chrom_vm_label(p3)]==['CTRL_WHEEL','STALE_CAPABILITY','UNSUPPORTED']
        print(json.dumps({'construction':'PASS_MECHANICS'})); return
    chrom=make_chromium(); chrom_errors=[]
    for i,p in enumerate(chrom):
        n=chrom_native_label(p); v=chrom_vm_label(p)
        if n!=v: chrom_errors.append([i,n,v])
    retained=[]
    for row in fixture['openttd_retained']:
        n=openttd_native(row); v=openttd_vm(row); exp=row['expected']; retained.append({'id':row['id'],'native':[n.kind,n.value],'vm':[v.kind,v.value],'expected':exp,'ok':[n.kind,n.value]==exp and [v.kind,v.value]==exp})
    controls=[]
    for row in fixture['openttd_controls']:
        n=openttd_native(row); v=openttd_vm(row); exp=row['expected']; controls.append({'id':row['id'],'native':[n.kind,n.value],'vm':[v.kind,v.value],'expected':exp,'ok':[n.kind,n.value]==exp and [v.kind,v.value]==exp and v.kind!='EXECUTE'})
    chrom_req=[chrom_request_from_x(d900.extract_validate(p)) for p in chrom]
    open_rows=fixture['openttd_retained']+fixture['openttd_controls']
    open_req=[Request('openttd_guard',{'binding_current':bool(r.get('binding_current',False)),'guard_reason':r.get('guard_reason')},OPENTTD_ALLOWED,frozenset({'CURRENT_BINDING','LOCAL_GUARD'})) for r in open_rows]
    chrom_vm_only=lambda req: eval_program(req,CHROMIUM_PROGRAM)
    open_vm_only=lambda req: eval_program(req,OPENTTD_PROGRAM)
    timings={}
    timings['chromium_native_e2e']=timed(chrom_native_label,chrom)[0]
    timings['chromium_vm_e2e']=timed(chrom_vm_label,chrom)[0]
    timings['chromium_vm_only']=timed(chrom_vm_only,chrom_req)[0]
    timings['openttd_native_e2e']=timed(openttd_native,open_rows)[0]
    timings['openttd_vm_e2e']=timed(openttd_vm,open_rows)[0]
    timings['openttd_vm_only']=timed(open_vm_only,open_req)[0]
    timings['chromium_adapter_only']=timed(lambda p: chrom_request_from_x(d900.extract_validate(p)),chrom)[0]
    timings['openttd_adapter_only']=timed(lambda r: Request('openttd_guard',{'binding_current':bool(r.get('binding_current',False)),'guard_reason':r.get('guard_reason')},OPENTTD_ALLOWED,frozenset({'CURRENT_BINDING','LOCAL_GUARD'})),open_rows)[0]
    gates={
      'chromium_exact':len(chrom_errors)==0,
      'openttd_retained_5of5':all(x['ok'] for x in retained) and len(retained)==5,
      'controls_fail_closed':all(x['ok'] for x in controls),
      'chromium_vm_p95_lt10us':timings['chromium_vm_only']['p95_us']<10,
      'openttd_vm_p95_lt10us':timings['openttd_vm_only']['p95_us']<10,
      'chromium_e2e_p95_lt25us':timings['chromium_vm_e2e']['p95_us']<25,
      'openttd_e2e_p95_lt25us':timings['openttd_vm_e2e']['p95_us']<25,
    }
    decision='PASS_CROSS_DOMAIN_RULE_VM_SCOPED' if all(gates.values()) else ('FAIL_CROSS_DOMAIN_SEMANTICS' if not gates['chromium_exact'] or not gates['openttd_retained_5of5'] else ('FAIL_FAIL_CLOSED' if not gates['controls_fail_closed'] else 'HOLD_VM_OVERHEAD_NOT_SMALL'))
    result={'task':'LOCAL-SYSTEM1-CROSS-DOMAIN-RULE-VM-20260917-001','decision':decision,'formal_invocation':1,'reruns':0,'source_blobs':fixture['source_blobs'],'chromium':{'unique_payloads':len(chrom),'errors':chrom_errors[:20]},'openttd_retained':retained,'openttd_controls':controls,'timings':timings,'gates':gates,'counters':{'authority_grants':0,'task_input_calls':0,'network_calls':0,'gradient_updates':0},'environment':{'python':platform.python_version(),'platform':platform.platform(),'cpu_count':os.cpu_count()},'timing_schedule':{'warmup':WARMUP,'measured':TIMING_N,'batch':1}}
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); (out/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'gates':gates,'timings':timings},sort_keys=True))
if __name__=='__main__': main()
