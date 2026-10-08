from __future__ import annotations
import json,sys
from pathlib import Path
from core import run_condition
SEEDS=[994101,994102,994103]
ORDERS=[('FRESH','STALE'),('STALE','FRESH'),('FRESH','STALE')]

def hard_gate(r):
    post=r.get('post_authority') or {}
    common=(r.get('first_status')=='authority_ended' and post.get('captures')==1 and post.get('sequence_advanced') is True
            and post.get('within_lifecycle_deadline') is True and post.get('error') is None
            and post.get('grants_input_authority') is False and post.get('tail_program_steps_resumed')==0
            and r.get('owner_expiry_releases')==1 and r.get('owner_expiry_all_verified') is True
            and r.get('owner_all_verified') is True and r.get('terminal_score_audit_exit')==0
            and r.get('shift_input_admissions')==1)
    if r['condition']=='FRESH':
        return common and r['current_sequence']>r['post_sequence'] and r['caller_outcome']=='TASK_NOT_VERIFIED' and r['caller_reason']=='unavailable' \
            and r['calls']==['reuse_revalidate','final_revalidate','execute','verify_effect'] and r['right_input_admissions']==1 \
            and r['second_terminal_status']=='completed' and r['second_terminal_release_verified'] is True
    return common and r['current_sequence']==r['post_sequence'] and r['caller_outcome']=='SAFE_STOP' and r['caller_reason']=='stale' \
        and r['calls']==['reuse_revalidate'] and r['right_input_admissions']==0 and r['second_terminal_status'] is None

def main(root):
    if root.exists():raise SystemExit('output exists')
    pairs=[]
    for i,(seed,order) in enumerate(zip(SEEDS,ORDERS),1):
        pr=[]
        for cond in order:
            r=run_condition(root/f'pair-{i:02d}',cond,seed);r['hard_gate_pass']=hard_gate(r);pr.append(r)
            print(json.dumps({'pair':i,'condition':cond,'hard_gate_pass':r['hard_gate_pass'],'outcome':r['caller_outcome'],'right':r['right_input_admissions']},sort_keys=True),flush=True)
        pairs.append(pr)
    flat=[r for p in pairs for r in p]
    hard=[f"pair-{i+1}:{r['condition']}" for i,p in enumerate(pairs) for r in p if not r['hard_gate_pass']]
    summary={'schema':'map01-live-two-dispatch-v1-result','pairs':pairs,'hard_failures':hard,
             'fresh_pass':sum(r['hard_gate_pass'] for r in flat if r['condition']=='FRESH'),
             'stale_pass':sum(r['hard_gate_pass'] for r in flat if r['condition']=='STALE'),
             'fresh_right_admissions':sum(r['right_input_admissions'] for r in flat if r['condition']=='FRESH'),
             'stale_right_admissions':sum(r['right_input_admissions'] for r in flat if r['condition']=='STALE'),
             'decision':'PASS_MAP01_LIVE_TWO_DISPATCH' if not hard else 'FAIL'}
    (root/'result.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='pairs'},indent=2,sort_keys=True))
    return 0 if not hard else 2
if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1])))
