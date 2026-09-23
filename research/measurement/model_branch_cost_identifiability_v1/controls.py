import json,copy
from audit import verify
from pathlib import Path
HERE=Path(__file__).parent
r=json.loads((HERE/'RESULT.json').read_text());l=json.loads((HERE/'ledger.json').read_text()); controls=[]
def t(name,mut):
    x=copy.deepcopy(r); y=copy.deepcopy(l); mut(x,y); z=verify(x,y); controls.append({'name':name,'rejected':not z['audit_pass'],'errors':z['errors']})
t('fake_admissible',lambda x,y:x.__setitem__('admissible_pair_count',1))
t('fake_same_image',lambda x,y:x.__setitem__('same_image_pairs',1))
t('emit_per_branch_cost',lambda x,y:x.__setitem__('per_branch_cost_emitted',True))
t('launder_whole_run_delta',lambda x,y:x['whole_run_noncausal_diagnostic'].__setitem__('causal_per_branch_estimate',1.0))
def mutate_ledger(x,y):
    g=y['rows'][0]; u=y['rows'][12]
    for idx in [2,3,4,8,9,10,12]:u[idx]=copy.deepcopy(g[idx])
    u[11]=0 if g[11]==1 else 1
t('ledger_injected_match_without_result_update',mutate_ledger)
assert all(c['rejected'] for c in controls),controls
(HERE/'CORRUPTION.json').write_text(json.dumps({'controls':controls,'rejected':sum(c['rejected'] for c in controls),'total':len(controls)},indent=2,sort_keys=True)+'\n')
print(json.dumps(controls,indent=2))
