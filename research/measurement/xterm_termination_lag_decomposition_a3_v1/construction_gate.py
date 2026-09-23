import argparse,json,statistics,hashlib
from pathlib import Path
ROI={'source':'fixed_center_roi','window':[640,360],'roi':[160,90,320,180],'bytes':230400}
def pct(xs,q): return sorted(xs)[int(q*(len(xs)-1))]
def summ(xs): return {'n':len(xs),'min_ns':min(xs),'max_ns':max(xs),'p50_ns':statistics.median(xs),'p95_ns':pct(xs,.95),'mean_ns':sum(xs)/len(xs)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('rows');ap.add_argument('--out',required=True);a=ap.parse_args()
 raw=Path(a.rows).read_bytes();rows=json.loads(raw);errs=[];e2c=[];c2x=[]
 if len(rows)!=4: errs.append(['rows',len(rows),4])
 for i,r in enumerate(rows):
  d=r.get('decomposition') or {}
  if not r.get('score',{}).get('ok'):errs.append([i,'score'])
  if r.get('observation')!=ROI:errs.append([i,'roi'])
  if r.get('child_ready_observed_ns') is None:errs.append([i,'marker'])
  if d.get('reconstruction_error_ns',10**18)>2_000_000:errs.append([i,'reconstruct'])
  if 'effect_to_child_ready_ns' in d:e2c.append(d['effect_to_child_ready_ns'])
  if 'child_ready_to_proc_exit_ns' in d:c2x.append(d['child_ready_to_proc_exit_ns'])
 if len(e2c)!=len(rows) or len(c2x)!=len(rows):errs.append(['interval_count'])
 es=summ(e2c) if e2c else None; cs=summ(c2x) if c2x else None
 eligible=(not errs and es['p95_ns']<30_000_000 and cs['p50_ns']>100_000_000)
 out={'task':'TIMING-XTERM-TERMINATION-LAG-DECOMPOSITION-A3-INTERPRETER-20260918-003','construction_sessions':len(rows),'construction_eligible':eligible,'errors':errs,'effect_to_child_ready':es,'child_ready_to_proc_exit':cs,'max_reconstruction_error_ns':max((r['decomposition']['reconstruction_error_ns'] for r in rows),default=None),'rows_sha256':hashlib.sha256(raw).hexdigest(),'note':'Formal native-exit spread gate is not applied to excluded n=4 construction; matches #1563 construction policy.'}
 Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
 raise SystemExit(0 if eligible else 4)
if __name__=='__main__': main()
