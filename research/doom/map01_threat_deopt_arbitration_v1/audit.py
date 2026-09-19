from __future__ import annotations
import argparse, json
from pathlib import Path

def expected(s,p):
    table={
      'overlap_deopt_late':({'locomotion':'deopt'},{'locomotion':'threat'}),
      'overlap_threat_late':({'locomotion':'threat'},{'locomotion':'threat'}),
      'active_lease_missing_threat_command':({'locomotion':'deopt'},{}),
      'expired_lease_deopt':({'locomotion':'deopt'},{'locomotion':'deopt'}),
      'invalid_context_deopt':({'locomotion':'deopt'},{'locomotion':'deopt'}),
      'nonoverlap_resources':({'fire':'threat','locomotion':'deopt'},{'fire':'threat','locomotion':'deopt'}),
      'deopt_only':({'locomotion':'deopt'},{'locomotion':'deopt'}),
      'threat_only':({'locomotion':'threat'},{'locomotion':'threat'})
    }
    return table[s][0 if p=='latest_ready' else 1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    data=json.loads(Path(a.result).read_text()); rows=data['rows']; errs=[]
    if len(rows)!=64: errs.append(f'row_count:{len(rows)}')
    ids=[r['row_id'] for r in rows]
    if len(set(ids))!=len(ids): errs.append('duplicate_ids')
    for r in rows:
        exp=expected(r['scenario'],r['policy'])
        if r['selected']!=exp: errs.append(f"{r['row_id']}:selected:{r['selected']}:{exp}")
        if r['correct'] is not True: errs.append(f"{r['row_id']}:correct_flag")
    cand=[r for r in rows if r['policy']=='authority_guarded']; base=[r for r in rows if r['policy']=='latest_ready']
    candidate_correct=sum(r['correct'] for r in cand)
    base_overlap_violations=sum(1 for r in base if r['scenario'] in ('overlap_deopt_late','active_lease_missing_threat_command') and r['selected'].get('locomotion')=='deopt')
    candidate_overlap_violations=sum(1 for r in cand if r['scenario'] in ('overlap_deopt_late','active_lease_missing_threat_command') and r['selected'].get('locomotion')=='deopt')
    candidate_liveness=sum(1 for r in cand if r['scenario'] in ('expired_lease_deopt','invalid_context_deopt','deopt_only') and r['selected'].get('locomotion')=='deopt')
    nonoverlap=sum(1 for r in cand if r['scenario']=='nonoverlap_resources' and r['selected']=={'fire':'threat','locomotion':'deopt'})
    if candidate_correct!=32: errs.append(f'candidate_correct:{candidate_correct}')
    if base_overlap_violations!=8: errs.append(f'baseline_override_controls:{base_overlap_violations}')
    if candidate_overlap_violations!=0: errs.append(f'candidate_override:{candidate_overlap_violations}')
    if candidate_liveness!=12: errs.append(f'candidate_liveness:{candidate_liveness}')
    if nonoverlap!=4: errs.append(f'nonoverlap:{nonoverlap}')
    decision='PASS_THREAT_DEOPT_AUTHORITY_ARBITRATION_SCOPED' if not errs else 'FAIL_AUTHORITY_ARBITRATION'
    out={"schema":"agent-interface/map01-threat-deopt-arbitration-audit-v1","decision":decision,"errors":errs,"counts":{"candidate_correct":candidate_correct,"baseline_overlap_violations":base_overlap_violations,"candidate_overlap_violations":candidate_overlap_violations,"candidate_deopt_liveness":candidate_liveness,"candidate_nonoverlap_preserved":nonoverlap}}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if not errs else 1)
if __name__=='__main__':main()
