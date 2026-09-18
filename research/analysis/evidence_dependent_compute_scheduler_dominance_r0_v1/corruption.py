from fractions import Fraction as F
import json, pathlib, sys

def correct(cur,t,c,d): return cur and t+c<=d
rows=[]
T=(F(0),F(1,2),F(1)); C=(F(0),F(1,2),F(1)); D=(F(0),F(1),F(2))
for cur in (True,False):
  for t in T:
    for c in C:
      for d in D: rows.append((cur,t,c,d))
controls={}
controls['reverse_slack_inequality']=any((cur and t+c>=d)!=correct(cur,t,c,d) for cur,t,c,d in rows)
controls['reject_inclusive_tie']=any((cur and t+c<d)!=correct(cur,t,c,d) for cur,t,c,d in rows)
controls['permit_stale_publication']=any((t+c<=d)!=correct(cur,t,c,d) for cur,t,c,d in rows)
stable_preference='RUN'; invalidate_preference='WAIT'
controls['universal_run_for_feasible']= stable_preference != invalidate_preference
out={"schema":"evidence_compute_scheduler_dominance_corruption_v1","all_rejected":all(controls.values()),"controls":controls}
pathlib.Path(__file__).with_name('CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['all_rejected'] else 1)
