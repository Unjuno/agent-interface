import copy,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;r=json.loads((HERE/'FORMAL_RESULT.json').read_text())
def valid(x):return (x.get('candidate_git_blob')=='404a452aa304b4bde73ec0182450d241e2a744af' and x.get('seed')==100820260917002 and x.get('random_batches')==x.get('random_equal')==25000 and x.get('exhaustive_batches')==x.get('exhaustive_equal') and x.get('critical_batch_errors')==0 and x.get('stale_noncritical_delivered_batches')==0 and x.get('scope_cardinality_errors')==0 and x.get('controls_passed')==x.get('controls_total')==10 and (x.get('formal_invocations'),x.get('reruns'))==(1,0) and x.get('decision')=='PASS_FRESHNESS_BACKPRESSURE_FORMAL_SCOPED')
controls=[]
for name,fn in [('blob',lambda x:x.update(candidate_git_blob='bad')),('random_count',lambda x:x.update(random_equal=24999)),('critical_loss',lambda x:x.update(critical_batch_errors=1)),('stale_delivery',lambda x:x.update(stale_noncritical_delivered_batches=1)),('invocation',lambda x:x.update(formal_invocations=2))]:
 y=copy.deepcopy(r);fn(y);controls.append({'name':name,'rejected':not valid(y)})
out={'passed':all(x['rejected'] for x in controls),'controls':controls};(HERE/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
