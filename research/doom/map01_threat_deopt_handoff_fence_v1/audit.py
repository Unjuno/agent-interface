from __future__ import annotations
import argparse,json
from pathlib import Path

def exp(s,p):
 b={'expired_old_deopt':{'locomotion':'deopt'},'expired_fresh_deopt':{'locomotion':'deopt'},'expired_old_threat':{'locomotion':'threat'},'expired_fresh_unowned_threat':{'locomotion':'threat'},'invalidated_old_deopt':{'locomotion':'deopt'},'no_authority_deopt':{'locomotion':'deopt'},'nonoverlap_resources':{'fire':'threat','locomotion':'deopt'},'active_overlap':{'locomotion':'threat'}}
 c={'expired_old_deopt':{},'expired_fresh_deopt':{'locomotion':'deopt'},'expired_old_threat':{},'expired_fresh_unowned_threat':{},'invalidated_old_deopt':{},'no_authority_deopt':{'locomotion':'deopt'},'nonoverlap_resources':{'fire':'threat','locomotion':'deopt'},'active_overlap':{'locomotion':'threat'}}
 return (b if p=='authority_guarded' else c)[s]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();d=json.loads(Path(a.result).read_text());rows=d['rows'];errs=[]
 if len(rows)!=64:errs.append(f'rows:{len(rows)}')
 ids=[r['row_id'] for r in rows]
 if len(ids)!=len(set(ids)):errs.append('duplicate_ids')
 for r in rows:
  e=exp(r['scenario'],r['policy'])
  if r['selected']!=e:errs.append(f"{r['row_id']}:selected:{r['selected']}:{e}")
  if r.get('correct') is not True:errs.append(f"{r['row_id']}:correct")
 base=[r for r in rows if r['policy']=='authority_guarded'];cand=[r for r in rows if r['policy']=='handoff_fenced']
 bad={'expired_old_deopt','expired_old_threat','expired_fresh_unowned_threat','invalidated_old_deopt'}
 baseline_bad=sum(1 for r in base if r['scenario'] in bad and bool(r['selected']))
 candidate_bad=sum(1 for r in cand if r['scenario'] in bad and bool(r['selected']))
 candidate_correct=sum(r['correct'] for r in cand)
 fresh=sum(1 for r in cand if r['scenario'] in {'expired_fresh_deopt','no_authority_deopt'} and r['selected'].get('locomotion')=='deopt')
 nonoverlap=sum(1 for r in cand if r['scenario']=='nonoverlap_resources' and r['selected']=={'fire':'threat','locomotion':'deopt'})
 active=sum(1 for r in cand if r['scenario']=='active_overlap' and r['selected']=={'locomotion':'threat'})
 if baseline_bad!=16:errs.append(f'baseline_bad:{baseline_bad}')
 if candidate_bad!=0:errs.append(f'candidate_bad:{candidate_bad}')
 if candidate_correct!=32:errs.append(f'candidate_correct:{candidate_correct}')
 if fresh!=8:errs.append(f'fresh_liveness:{fresh}')
 if nonoverlap!=4:errs.append(f'nonoverlap:{nonoverlap}')
 if active!=4:errs.append(f'active:{active}')
 decision='PASS_AUTHORITY_HANDOFF_GENERATION_FENCE_SCOPED' if not errs else 'FAIL_AUTHORITY_HANDOFF_FENCE'
 out={'schema':'agent-interface/map01-threat-deopt-handoff-fence-audit-v1','decision':decision,'errors':errs,'counts':{'candidate_correct':candidate_correct,'baseline_stale_or_unowned_executions':baseline_bad,'candidate_stale_or_unowned_executions':candidate_bad,'candidate_fresh_deopt_liveness':fresh,'candidate_nonoverlap_preserved':nonoverlap,'candidate_active_authority_preserved':active}}
 Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not errs else 1)
if __name__=='__main__':main()
