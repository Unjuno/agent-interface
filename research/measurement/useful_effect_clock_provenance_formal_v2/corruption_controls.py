import copy,json
from pathlib import Path
HERE=Path(__file__).resolve().parent; r=json.loads((HERE/'FORMAL_RESULT.json').read_text())
def valid(x):
 return (x.get('candidate_git_blob')=='b8e35581eaf1f99f6ad973f4bde1367e43eb0a1b' and x.get('seed')==100420260917002 and x.get('records')==180000 and x.get('candidate_oracle_equal')==180000 and x.get('same_clock_parent_mismatches')==0 and x.get('cross_clock_bound_promotions')==0 and x.get('controls_passed')==x.get('controls_total')==13 and (x.get('formal_invocations'),x.get('reruns'))==(1,0) and x.get('decision')=='PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_FORMAL_SCOPED')
controls=[]
for name,fn in [
 ('seed',lambda x:x.update(seed=1)),('candidate_blob',lambda x:x.update(candidate_git_blob='bad')),('cross_promotion',lambda x:x.update(cross_clock_bound_promotions=1)),('parent_mismatch',lambda x:x.update(same_clock_parent_mismatches=1)),('invocation',lambda x:x.update(formal_invocations=2))]:
 y=copy.deepcopy(r);fn(y);controls.append({'name':name,'rejected':not valid(y)})
out={'passed':all(c['rejected'] for c in controls),'controls':controls};(HERE/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
