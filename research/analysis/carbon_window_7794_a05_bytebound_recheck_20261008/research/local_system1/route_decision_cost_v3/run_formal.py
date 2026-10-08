import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ.setdefault(k,'1')
import gc,hashlib,json,math,platform,resource,statistics,time
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from decision import LABELS,HSTAT,truth,make_payload,extract_validate
TASK='LOCAL-SYSTEM1-ROUTE-DECISION-COST-20260917-003'
SEED=89220260917
SKLEARN_SEED=SEED%(2**32)
UNIQUE=8192
MEASURED=32768
WARMUP=512

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def q(vals,p):
    vals=sorted(vals); pos=(len(vals)-1)*p; lo=int(pos); hi=min(lo+1,len(vals)-1); f=pos-lo; return float(vals[lo]*(1-f)+vals[hi]*f)
def summary_us(v): return {'p50':q(v,.5),'p95':q(v,.95),'p99':q(v,.99),'max':max(v),'mean':statistics.fmean(v)}
def compile_backends():
    X=[]; y=[]
    for m in range(256):
        x=np.array([(m>>i)&1 for i in range(8)],dtype=np.float64); X.append(x); y.append(truth(x))
    X=np.stack(X); y=np.array(y)
    t=time.perf_counter_ns(); linear=LogisticRegression(C=1e6,max_iter=10000,solver='lbfgs',random_state=SKLEARN_SEED).fit(X,y); linear_ms=(time.perf_counter_ns()-t)/1e6
    t=time.perf_counter_ns(); tree=DecisionTreeClassifier(random_state=SKLEARN_SEED).fit(X,y); tree_ms=(time.perf_counter_ns()-t)/1e6
    if not np.array_equal(linear.predict(X),y): raise RuntimeError('linear_truth')
    if not np.array_equal(tree.predict(X),y): raise RuntimeError('tree_truth')
    return linear,tree,{'linear_ms':linear_ms,'tree_ms':tree_ms,'tree_depth':tree.get_depth(),'tree_leaves':int(tree.get_n_leaves())}
def corpus():
    rng=np.random.default_rng(SEED)
    rows=[]
    for i in range(UNIQUE):
        bits=[int(v) for v in rng.integers(0,2,size=7)]
        live=int(rng.integers(0,2)); hs='LIVE' if live else HSTAT[1+int(rng.integers(0,len(HSTAT)-1))]
        payload=make_payload(bits,hs,int(rng.integers(0,2**31)))
        x=extract_validate(payload); rows.append((payload,x,truth(x)))
    return rows
def pred_rule(x): return truth(x)
def bench(rows, fn, end_to_end=False):
    vals=[]; errs=0; h=hashlib.sha256()
    for i in range(WARMUP):
        p,x,e=rows[i%len(rows)]; z=extract_validate(p) if end_to_end else x; fn(z)
    for i in range(MEASURED):
        p,x,e=rows[i%len(rows)]; t=time.perf_counter_ns(); z=extract_validate(p) if end_to_end else x; r=int(fn(z)); vals.append((time.perf_counter_ns()-t)/1000.0); errs += (r!=e); h.update(bytes([r]))
    return summary_us(vals),errs,h.hexdigest()
def bench_extract(rows):
    vals=[]
    for i in range(WARMUP): extract_validate(rows[i%len(rows)][0])
    for i in range(MEASURED):
        p=rows[i%len(rows)][0]; t=time.perf_counter_ns(); extract_validate(p); vals.append((time.perf_counter_ns()-t)/1000.0)
    return summary_us(vals)
def main():
    if Path('FORMAL_RESULT.json').exists() or Path('FORMAL_INVOKED.json').exists(): raise SystemExit('rerun forbidden')
    Path('FORMAL_INVOKED.json').write_text(json.dumps({'task':TASK,'formal_invocation':1})+'\n')
    freeze=json.loads(Path('FREEZE.json').read_text())
    for f,d in freeze['source_sha256'].items():
        if sha(f)!=d: raise SystemExit('source hash mismatch '+f)
    linear,tree,setup=compile_backends(); rows=corpus()
    extraction=bench_extract(rows)
    backends={}
    funcs={'RULE':pred_rule,'LINEAR':lambda x:int(linear.predict(x.reshape(1,-1))[0]),'TREE':lambda x:int(tree.predict(x.reshape(1,-1))[0])}
    for name,fn in funcs.items():
        bonly,be,bh=bench(rows,fn,False); total,te,th=bench(rows,fn,True)
        backends[name]={'backend_only_us':bonly,'end_to_end_us':total,'backend_errors':be,'end_to_end_errors':te,'backend_output_hash':bh,'end_to_end_output_hash':th}
    r95=backends['RULE']['end_to_end_us']['p95']; lr=backends['LINEAR']['end_to_end_us']['p95']/r95; tr=backends['TREE']['end_to_end_us']['p95']/r95; ef=extraction['p95']/r95
    errs=[]
    for n,b in backends.items():
        if b['backend_errors'] or b['end_to_end_errors']: errs.append('correctness_'+n)
        if b['end_to_end_us']['p95']>=1000: errs.append('under_1ms_'+n)
    if r95>=25: errs.append('rule_25us')
    if ef<0.5: errs.append('extraction_fraction')
    if lr<3: errs.append('linear_ratio')
    if tr<3: errs.append('tree_ratio')
    decision='PASS_REAL_TYPED_DECISION_COST_SCOPED' if not errs else ('REJECT_LOCAL_DECISION_COST' if r95>=1000 else 'HOLD_WRAPPER_OVERHEAD_NOT_STABLE')
    result={'schema':'route_decision_cost_result_v1','task':TASK,'formal_invocation':1,'reruns':0,'decision':decision,'errors':errs,'unique_payloads':UNIQUE,'measured_queries':MEASURED,'warmup':WARMUP,'labels':LABELS,'setup':setup,'extraction_only_us':extraction,'backends':backends,'derived':{'rule_p95_us':r95,'extraction_fraction_of_rule_p95':ef,'linear_to_rule_p95_ratio':lr,'tree_to_rule_p95_ratio':tr},'environment':{'python':platform.python_version(),'numpy':np.__version__,'sklearn':__import__('sklearn').__version__,'cpu_count':os.cpu_count(),'thread_env':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']},'rss_max_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024},'network_calls':0,'gradient_updates':0,'task_input_calls':0,'authority_grants':0}
    Path('FORMAL_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'errors':errs,'rule_p95_us':r95,'extraction_fraction':ef,'linear_ratio':lr,'tree_ratio':tr,'sha256':sha('FORMAL_RESULT.json')},sort_keys=True))
if __name__=='__main__': main()
