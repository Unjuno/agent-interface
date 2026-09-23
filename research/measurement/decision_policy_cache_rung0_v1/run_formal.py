import json,random,hashlib,time,statistics,resource
from pathlib import Path
from generator import trace
from cache import monitor
from mechanics import evaluate_trace
H=Path(__file__).resolve().parent
seed=115520260918001; rng=random.Random(seed); n=50000
agg={'reference_semantic_calls':0,'candidate_semantic_calls':0,'mismatches':0,'stale_continuation_attempts':0,'missed_hard_invalidations':0,'unnecessary_yields':0,'authority_errors':0,'wrong_effects':0,'candidate_effect':0,'reference_effect':0,'reuse_cycles':0,'ambiguous_cases':0}
terminal_counts={}; monitor_ns=[]
for i in range(n):
    e,rows,terminal=trace(i,rng); terminal_counts[str(terminal)]=terminal_counts.get(str(terminal),0)+1
    r=evaluate_trace(e,rows)
    for k in agg: agg[k]+=r[k]
    # diagnostic monitor timing on one valid point, not a pass gate.
    t=time.perf_counter_ns(); monitor(e,rows[0]); monitor_ns.append(time.perf_counter_ns()-t)
errors=sum(agg[k] for k in ('mismatches','stale_continuation_attempts','missed_hard_invalidations','unnecessary_yields','authority_errors','wrong_effects'))
calls_avoided=agg['reference_semantic_calls']-agg['candidate_semantic_calls']
cache_pass=(errors==0 and agg['candidate_effect']==agg['reference_effect'] and calls_avoided>0 and terminal_counts.get('HARD_INVALIDATION',0)>0 and terminal_counts.get('AMBIGUOUS_BOUNDARY',0)>0)
supervisor_hold=(cache_pass and agg['ambiguous_cases']>0)
s=sorted(monitor_ns)
def pct(q): return s[min(len(s)-1,int((len(s)-1)*q))]/1e3
out={'schema':'decision_policy_cache_rung0_result_v1','task':'DECISION-POLICY-CACHE-RUNG0-20260918-001','decision':'PASS_DECISION_POLICY_CACHE_RUNG0_SCOPED' if cache_pass else 'FAIL_DECISION_POLICY_CACHE_RUNG0','supervisor_disposition':'HOLD_DETERMINISTIC_MONITOR_SUFFICIENT' if supervisor_hold else 'UNRESOLVED','seed':seed,'formal_invocation':1,'reruns':0,'traces':n,'terminal_counts':terminal_counts,**agg,'semantic_calls_avoided':calls_avoided,'semantic_call_reduction_fraction':calls_avoided/agg['reference_semantic_calls'],'monitor_timing_us_diagnostic':{'p50':pct(.50),'p95':pct(.95),'p99':pct(.99)},'max_rss_kb_diagnostic':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'model_calls':0,'gui_actions':0,'task_input_actions':0}
out['digest']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest();(H/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(out['decision'],out['supervisor_disposition'])
