"""Read-only post-formal comparison with restart and unconditional-stop baselines."""
from __future__ import annotations
import json
from pathlib import Path
OPS=("prepare_record","commit_record","send_receipt")
ROOT=Path(__file__).resolve().parent

def main():
    public=json.loads((ROOT/'public_trace.json').read_text())
    truth=json.loads((ROOT/'truth_sidecar.json').read_text())
    candidate=json.loads((ROOT/'candidate_output.json').read_text())
    audit=json.loads((ROOT/'audit.json').read_text())
    if audit['disposition']!='PASS_METHOD_SCOPED' or audit['independent_errors'] or candidate['rows']!=audit['reconstructed_rows']:
        raise SystemExit('saved formal rows do not pass the independent audit; no baseline comparison emitted')
    cases={x['case_id']:x for x in public['cases']}
    rows=[]
    total_replayed=0
    eligible=0
    for out in candidate['rows']:
        raw=cases[out['case_id']]
        truth_row=truth['cases'][out['case_id']]
        point=public['mapping']['safepoints'].get(raw['specialized_pc'])
        receipts=raw['effect_receipts']
        valid=(raw['observation_generation']==public['current_generation'] and point is not None
               and len(receipts)==point['semantic_cursor'])
        prefix=[]
        if valid:
            for index,receipt in enumerate(receipts):
                operation=OPS[index]
                state=receipt.get('state')
                if (receipt.get('operation_id')!=operation
                    or receipt.get('observation_generation')!=truth_row['current_generation']
                    or receipt.get('verifier_role')!='independent_effect_receipt'
                    or truth_row['actual_effect_states'].get(operation)!=state):
                    valid=False
                    break
                if state=='VERIFIED': prefix.append(operation)
                elif state not in {'UNKNOWN','NO_EFFECT'}:
                    valid=False
                    break
        if valid:
            eligible+=1
            total_replayed+=len(prefix)
        rows.append({
            'case_id':out['case_id'],
            'comparison_eligible':valid,
            'known_verified_prefix':prefix if valid else [],
            'restart_from_zero':{'cursor':0,'known_effect_replays':len(prefix) if valid else None},
            'unconditional_stop':{'cursor':None,'continued':False},
            'effect_indexed_map':{'disposition':out['disposition'],'cursor':out['generic_cursor'],'verified_prefix':out['verified_prefix'],'execution_authorized':out['execution_authorized']},
        })
    ready=[r for r in rows if r['comparison_eligible'] and r['effect_indexed_map']['disposition']=='READY_AT_CURSOR' and r['effect_indexed_map']['cursor']>0]
    result={
        'schema':'unjuno.issue8040.postformal_baseline_comparison.v1',
        'classification':'READ_ONLY_SUPPLEMENT; not a new candidate/auditor allocation and not part of FROZEN.json',
        'input_audit':'saved A01 candidate rows equal independent raw reconstruction; zero audit errors',
        'rows':rows,
        'summary':{
            'comparison_eligible_rows':eligible,
            'restart_from_zero_known_verified_effect_replays':total_replayed,
            'unconditional_stop_continuations':0,
            'effect_map_advanced_verified_prefix_continuations':len(ready),
            'advanced_case_ids':[r['case_id'] for r in ready],
            'end_of_macro_is_still_unverified':any(r['effect_indexed_map']['disposition']=='CURSOR_AT_END_UNVERIFIED' for r in rows),
            'execution_authorized_by_map':False,
        },
    }
    (ROOT/'baseline_comparison.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__': main()
