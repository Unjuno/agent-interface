import json, pathlib, sys

ORIGINS=[10**12+123,10**15+123,3*10**15+123,10**16+123]
NONSTATIC=['positive_velocity_jitter','negative_velocity_jitter','slow_velocity_jitter']

def pred_abs(ts,xs,h):
    t=[n/1_000_000_000.0 for n in ts]; target=(ts[-1]+h)/1_000_000_000.0
    mt=sum(t)/len(t); mx=sum(xs)/len(xs); den=sum((z-mt)**2 for z in t)
    b=sum((z-mt)*(x-mx) for z,x in zip(t,xs))/den; a=mx-b*mt
    return a+b*target

def pred_shift(ts,xs,h):
    o=ts[-1]; t=[(n-o)/1_000_000_000.0 for n in ts]; target=h/1_000_000_000.0
    mt=sum(t)/len(t); mx=sum(xs)/len(xs); den=sum((z-mt)**2 for z in t)
    b=sum((z-mt)*(x-mx) for z,x in zip(t,xs))/den; a=mx-b*mt
    return a+b*target

def audit(path):
    d=json.loads(pathlib.Path(path).read_text()); errors=[]
    if d.get('formal_invocations')!=1 or d.get('formal_reruns')!=0: errors.append('formal_count')
    rows=d.get('rows',[])
    if len(rows)!=32: errors.append('row_count')
    by={}
    for r in rows:
        f=pred_abs if r['policy']=='absolute_float_seconds' else pred_shift
        p=f(r['timestamps_ns'],r['positions'],r['horizon_ns'])
        if p!=r['prediction']: errors.append(['prediction_mismatch',r['case_id']])
        e=abs(p-r['truth'])
        if e!=r['abs_error']: errors.append(['error_mismatch',r['case_id']])
        by[(r['trace'],r['policy'],r['origin_ns'])]=r
    candidate_rows=[r for r in rows if r['policy']=='origin_shifted_delta_seconds']
    candidate_error_gate=all(r['abs_error']<=1e-10 for r in candidate_rows)
    candidate_spread={}
    for tr in NONSTATIC:
        ps=[by[(tr,'origin_shifted_delta_seconds',o)]['prediction'] for o in ORIGINS]
        candidate_spread[tr]=max(ps)-min(ps)
    candidate_spread_gate=all(v<=1e-12 for v in candidate_spread.values())
    baseline_high={}
    baseline_spread={}
    for tr in ['positive_velocity_jitter','negative_velocity_jitter']:
        errs=[by[(tr,'absolute_float_seconds',o)]['abs_error'] for o in ORIGINS[2:]]
        baseline_high[tr]=max(errs)
        ps=[by[(tr,'absolute_float_seconds',o)]['prediction'] for o in ORIGINS]
        baseline_spread[tr]=max(ps)-min(ps)
    baseline_exposes=all(v>1e-8 for v in baseline_high.values()) and all(v>1e-8 for v in baseline_spread.values())
    static_exact=all(r['abs_error']==0.0 for r in rows if r['trace']=='static')
    gates={'candidate_error':candidate_error_gate,'candidate_origin_spread':candidate_spread_gate,'baseline_exposes':baseline_exposes,'static_exact':static_exact}
    if not all(gates.values()): errors.append(['gates',gates])
    decision='PASS_ORIGIN_SHIFTED_TIMESTAMP_CONDITIONING_SCOPED' if not errors else 'HOLD_NUMERIC_CONDITIONING'
    return {'decision':decision,'errors':errors,'gates':gates,'candidate_spread':candidate_spread,'baseline_high_error':baseline_high,'baseline_spread':baseline_spread,'rows':len(rows)}

if __name__=='__main__':
    out=audit(sys.argv[1]); print(json.dumps(out,sort_keys=True,indent=2)); sys.exit(0 if not out['errors'] else 1)
