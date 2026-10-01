import argparse,copy,json
from pathlib import Path
SCENARIOS=('E_FRESH_A','E_WRONG_SCOPE_B','D_STALE_E_SNAPSHOT','D_FRESH_A','D_WRONG_SCOPE_B')

def evaluate(r):
    e=[];m=r['metrics'];pairs=16 if r['phase']=='formal' else 2
    if m['pairs_completed']!=pairs or m['rows']!=pairs*5:e.append('shape')
    if m['scenario_counts']!={s:pairs for s in SCENARIOS}:e.append('scenario_counts')
    for k in ('candidate_oracle_mismatch','wrong_expected','stale_selected','wrong_scope_selected','authority_grants','task_input_calls','xtest_action_calls','focus_changed','cap_changed','socket_disappearance_failures','E_present_failures','D_absent_failures','stops'):
        if m[k]!=0:e.append(k)
    if r['phase']=='formal' and r['formal_invocations']!=1:e.append('formal_count')
    if r['reruns'] or r['replacements'] or r['tuning']:e.append('counters')
    return sorted(set(e))
def controls(r):
    t={}
    for name,key in [('stale','stale_selected'),('scope','wrong_scope_selected'),('authority','authority_grants'),('xtest_action','xtest_action_calls'),('lifecycle','socket_disappearance_failures'),('oracle','candidate_oracle_mismatch')]:
        q=copy.deepcopy(r);q['metrics'][key]=1;t[name]=bool(evaluate(q))
    return t
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());errs=evaluate(r);cc=controls(r);o={'pass':not errs and all(cc.values()),'errors':errs,'corruption_controls':cc,'controls_pass':all(cc.values())};Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['pass'] else 4)
