from __future__ import annotations
import hashlib,json
from pathlib import Path
import geometry
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/'result.json').read_text())

def sha(p): return hashlib.sha256((HERE/p).read_bytes()).hexdigest()
def fail(msg,errs): errs.append(msg)
def main():
 e=[]; T=round(1_000_000_000/35.0); bound=(2*T)//3; two=T//2
 if R.get('formal_deterministic_invocations')!=1:fail('invocations',e)
 if R.get('reruns')!=0:fail('reruns',e)
 if R.get('period_ns')!=T:fail('period',e)
 if R.get('source_sha256',{}).get('geometry.py')!=sha('geometry.py'):fail('geometry_sha',e)
 if R.get('source_sha256',{}).get('run.py')!=sha('run.py'):fail('run_sha',e)
 rows={x['span_ns']:x for x in R['rows']}
 for s in [10_000_000,18_000_000,bound]:
  r=rows[s]
  if r['interval_failure_exists'] or r['grid_failure_exists']:fail(f'below_bound_failure:{s}',e)
 above=((2*T+2)//3)+1_000
 r=rows[above]
 if not r['interval_failure_exists'] or not r['grid_failure_exists']:fail('above_bound_not_exposed',e)
 if not rows[T]['interval_failure_exists'] or not rows[T]['grid_failure_exists']:fail('full_tic_wrong',e)
 controls={x['span_ns']:x for x in R['two_attempt_controls']}
 if controls[two]['interval_failure_exists'] or controls[two]['grid_failure_exists']:fail('two_at_bound_failure',e)
 if not controls[two+1]['interval_failure_exists']:fail('two_above_bound_not_exposed',e)
 if R.get('rejected_spans') != [0,-1]:fail('invalid_span_controls',e)
 for phase in range(0,T,1_000):
  if geometry.all_attempts_fail(phase,bound,3,T): fail('sim_exact_bound_failure',e); break
 holds=[]
 for r in R['rows']+R['two_attempt_controls']:
  if r['interval_failure_exists'] != r['grid_failure_exists']:
   holds.append(r['span_ns'])
 decision='PASS_THREE_ATTEMPT_COHERENCE_GEOMETRY_SCOPED' if not e and not holds else ('HOLD_GRID_TOO_COARSE' if not e else 'FAIL_GEOMETRY_OR_IMPLEMENTATION')
 report={'decision':decision,'errors':e,'grid_disagreements':holds,'period_ns':T,'three_attempt_bound_floor_ns':bound,'bound_ms':bound/1e6}
 (HERE/'audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps(report,sort_keys=True)); raise SystemExit(decision!='PASS_THREE_ATTEMPT_COHERENCE_GEOMETRY_SCOPED')
if __name__=='__main__':main()
