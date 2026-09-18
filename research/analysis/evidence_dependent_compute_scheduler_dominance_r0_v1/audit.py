from fractions import Fraction as F
import json, pathlib, hashlib, sys
D0=pathlib.Path(__file__).parent
r=json.loads((D0/'RESULT.json').read_text())
s=r['summary']
T=(F(0),F(1,2),F(1),F(3,2),F(2)); C=(F(0),F(1,4),F(1,2),F(1),F(3,2),F(2)); DL=(F(0),F(1,2),F(1),F(3,2),F(2),F(5,2),F(3),F(4))
def parse(v):
    return F(v)
expected_rows=2*len(T)*len(C)*len(DL)
errors=[]
if s.get('rows')!=expected_rows: errors.append('row_count')
if len(r.get('rows',[]))!=expected_rows: errors.append('row_payload_count')
mis=stale=tardy=ties=tie_ok=0
for row in r.get('rows',[]):
    current=row['current']; t=parse(row['t']); c=parse(row['c']); d=parse(row['d'])
    direct=bool(current and t+c<=d)
    mis += row['candidate_feasible'] != direct
    stale += (not current and row['candidate_feasible'])
    tardy += (current and t+c>d and row['candidate_feasible'])
    if current and t+c==d:
        ties += 1; tie_ok += row['candidate_feasible']
if mis or s.get('mismatches')!=0: errors.append('feasibility_mismatch')
if stale or s.get('stale_run_accepted')!=0: errors.append('stale_accept')
if tardy or s.get('tardy_run_accepted')!=0: errors.append('tardy_accept')
if not ties or tie_ok!=ties or s.get('exact_tie_feasible_rows')!=s.get('exact_tie_current_rows'): errors.append('inclusive_tie')
p=s.get('paired_futures',{})
if p.get('stable',{}).get('preference')!='RUN': errors.append('stable_not_run')
if p.get('invalidate_soon',{}).get('preference')!='WAIT': errors.append('invalidate_not_wait')
if not s.get('universal_hard_metadata_choice_rejected'): errors.append('identifiability_not_rejected')
if s.get('reuse_decisions')!=0: errors.append('reuse_scope_violation')
if (s.get('formal_invocations'),s.get('reruns'),s.get('replacements'),s.get('tuning'))!=(1,0,0,0): errors.append('allocation_counts')
if s.get('decision')!='PASS_COMPUTE_SCHEDULER_HARD_DOMINANCE_SCOPED': errors.append('decision')
out={"schema":"evidence_compute_scheduler_dominance_audit_v1","passed":not errors,"errors":errors,
     "result_sha256":hashlib.sha256((D0/'RESULT.json').read_bytes()).hexdigest()}
(D0/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['passed'] else 1)
