from __future__ import annotations
import hashlib,json,math,sys
from pathlib import Path

EXPECTED_TIERS={262144,1048576,4194304,16777216}
EXPECTED_ORDER=[1048576,16777216,262144,4194304]
EXPECTED_HEADS=33
EXPECTED_LOGITS=455
EXPECTED_INPUT=32

def audit(rows, invocation, freeze, root):
    errors=[]
    if invocation.get('formal_invocations')!=1: errors.append('invocations')
    if invocation.get('tier_order')!=EXPECTED_ORDER: errors.append('tier_order')
    if len(rows)!=4 or {r.get('parameter_count') for r in rows}!=EXPECTED_TIERS: errors.append('tiers')
    for r in rows:
        n=r.get('parameter_count'); tag=str(n)
        if r.get('parameter_bytes')!=n*4: errors.append(tag+':bytes')
        if r.get('head_count')!=EXPECTED_HEADS or r.get('total_logits')!=EXPECTED_LOGITS or r.get('input_dim')!=EXPECTED_INPUT: errors.append(tag+':schema')
        if r.get('warmups')!=16 or r.get('measured_queries')!=128: errors.append(tag+':schedule')
        if r.get('typed_errors')!=[]: errors.append(tag+':typed')
        if r.get('deterministic_repeated_input') is not True: errors.append(tag+':determinism')
        if r.get('yield_count_total',0)<=0: errors.append(tag+':yield')
        for k in ('p50','p95','p99','max','min'):
            v=(r.get('warm_single_ms') or {}).get(k)
            if not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0: errors.append(tag+':latency:'+k)
        if r.get('training_steps')!=0 or r.get('gradient_updates')!=0 or r.get('network_calls')!=0 or r.get('task_input_calls')!=0 or r.get('authority_grants')!=0: errors.append(tag+':forbidden')
        env=(r.get('environment') or {}).get('thread_env') or {}
        if any(env.get(k)!='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')): errors.append(tag+':threads')
    biggest=next((r for r in rows if r.get('parameter_count')==16777216),None)
    if biggest is None: errors.append('largest_missing'); p95=None
    else: p95=biggest['warm_single_ms']['p95']
    # Source-first identity check.
    for rel,want in freeze['source_sha256'].items():
        got=hashlib.sha256((Path(root)/rel).read_bytes()).hexdigest()
        if got!=want: errors.append('source:'+rel)
    if errors: decision='FAIL_INTEGRITY'
    elif p95>=60.0: decision='REJECT_COMPILED_KERNEL_60MS_SHAPE'
    else: decision='PASS_COMPILED_TYPED_DECISION_KERNEL_SCOPED'
    runtime_class=None
    if not errors and p95<1.0: runtime_class='SUBMILLISECOND_KERNEL_CANDIDATE'
    elif not errors and p95<10.0: runtime_class='HIGH_CADENCE_KERNEL_CANDIDATE'
    return {'decision':decision,'runtime_class':runtime_class,'errors':errors,'largest_p95_ms':p95,'rows':len(rows)}

if __name__=='__main__':
    rows=json.loads(Path(sys.argv[1]).read_text()); inv=json.loads(Path(sys.argv[2]).read_text()); freeze=json.loads(Path(sys.argv[3]).read_text())
    out=audit(rows,inv,freeze,sys.argv[4]); Path(sys.argv[5]).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out))
