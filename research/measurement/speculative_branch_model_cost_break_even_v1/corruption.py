import copy,json
from pathlib import Path
from audit import verify
HERE=Path(__file__).parent
r=json.loads((HERE/'RESULT.json').read_text()); p=json.loads((HERE/'parents.json').read_text()); out=[]
def t(name,mut):
    x=copy.deepcopy(r); y=copy.deepcopy(p); mut(x,y); z=verify(x,y); out.append({'name':name,'rejected':not z['audit_pass'],'errors':z['errors']})
t('raw_gap',lambda x,y:x.__setitem__('raw_k2_advantage_ms',0.0))
t('p95_budget',lambda x,y:x['model_side_break_even_ms'].__setitem__('p95',0.0))
t('invent_same_generation_cost',lambda x,y:x['same_generation_k2'].__setitem__('incremental_model_wall_ms',1.0))
t('launder_full_boundary_reference',lambda x,y:x['extra_generation_k2'].__setitem__('same_generation_cost_estimate',True))
t('source_identity',lambda x,y:x.__setitem__('source_identity_ok',False))
assert all(v['rejected'] for v in out),out
(HERE/'CORRUPTION.json').write_text(json.dumps({'controls':out,'rejected':sum(v['rejected'] for v in out),'total':len(out)},indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2))
