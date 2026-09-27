"""Posthoc descriptive model only; not a preregistered test or runtime policy."""
from pathlib import Path
import json,collections
ROOT=Path(__file__).resolve().parent
rows=[]
for path in sorted((ROOT/'formal').glob('*/result.json')):
 r=json.loads(path.read_text());streak=0;max_residual=0.;mismatches=0;slow=fast=0;predicted=0.;actual=0.
 for a,b in zip(r['samples'],r['samples'][1:]):
  dy=(b['yaw_deg']-a['yaw_deg']+180)%360-180
  if b['action'][1]:
   streak+=1
   magnitude=1.7578125 if streak<=5 else 3.515625
   slow+=int(streak<=5);fast+=int(streak>5)
  else:
   streak=0;magnitude=0.
  residual=abs(dy+magnitude);max_residual=max(max_residual,residual)
  mismatches+=int(residual>1e-6);predicted-=magnitude;actual+=dy
 rows.append(dict(case=path.parent.name,arm=r['arm'],slow_turn_tics=slow,fast_turn_tics=fast,
                  mismatch_samples=mismatches,max_abs_residual_deg=max_residual,
                  predicted_yaw_deg=predicted,observed_yaw_deg=actual))
report={'label':'POSTHOC_EXPLANATORY_MODEL_NOT_INDEPENDENT_VALIDATION','rule':'For each contiguous TURN_RIGHT episode, first five tics predict -1.7578125deg/tic, later tics -3.515625deg/tic; neutral predicts0. Constants and breakpoint inspected after formal.','rows':rows,'mismatch_samples':sum(r['mismatch_samples'] for r in rows),'max_abs_residual_deg':max(r['max_abs_residual_deg'] for r in rows)}
with (ROOT/'posthoc-turn-history.json').open('x') as f:json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(report,indent=2))
