import json,hashlib
from pathlib import Path
HERE=Path(__file__).parent
EXPECTED={'mean':7.76753079678,'p50':7.774381,'p95':7.721722,'p99':7.60722}
def verify(r,p):
    e=[]
    raw=p['k1']['temporal_mean_ms']-p['k2']['temporal_mean_ms']
    if abs(r.get('raw_k2_advantage_ms',-1)-raw)>1e-12 or abs(raw-7.82655)>1e-12:e.append('raw_gap')
    for k,v in EXPECTED.items():
        if abs(r.get('model_side_break_even_ms',{}).get(k,-1)-v)>1e-12:e.append('budget_'+k)
    if r.get('same_generation_k2',{}).get('incremental_model_wall_ms') is not None:e.append('invented_same_generation_cost')
    if r.get('actual_model_incremental_cost_estimated') is not False:e.append('actual_cost_laundering')
    x=r.get('extra_generation_k2',{})
    if x.get('reference_only') is not True or x.get('same_generation_cost_estimate') is not False:e.append('reference_type')
    if r.get('source_identity_ok') is not True:e.append('source_identity')
    if any(r.get(k)!=0 for k in ('model_calls','provider_actions','gui_actions','task_input_actions')):e.append('forbidden_actions')
    if r.get('decision')!='PASS_MODEL_BRANCH_AUTHORING_BREAK_EVEN_LOCALIZED_SCOPED':e.append('decision')
    return {'audit_pass':not e,'errors':e,'recomputed_raw_gap_ms':raw,'recomputed_budgets_ms':EXPECTED}
def main():
    r=json.loads((HERE/'RESULT.json').read_text());p=json.loads((HERE/'parents.json').read_text());o=verify(r,p)
    o['result_sha256']=hashlib.sha256((HERE/'RESULT.json').read_bytes()).hexdigest();o['parents_sha256']=hashlib.sha256((HERE/'parents.json').read_bytes()).hexdigest()
    (HERE/'AUDIT.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
