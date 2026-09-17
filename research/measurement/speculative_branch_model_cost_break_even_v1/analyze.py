import json, hashlib
from pathlib import Path
HERE=Path(__file__).parent
EXPECTED_BLOBS={
 'k2_summary':'cec7c4a48cddf8ed4e9845c6a454b36c769326c0',
 'k1_summary':'96098fa35bbc13de189581d97eb332efac22b4be',
 'local_cost_result':'83fda0abdd2a0c5a7e410bd6f23870394d302e62',
 'model_probe2_audit':'d5f136d5a2ed92690fdce054e362aaf37a7c476e'}
def compute(p):
    raw=p['k1']['temporal_mean_ms']-p['k2']['temporal_mean_ms']
    local={k:v/1_000_000 for k,v in p['local_marginal_ns'].items() if k in ('mean','p50','p95','p99')}
    budgets={k:raw-v for k,v in local.items()}
    ref_ms=p['full_boundary_reference']['local_agent_message_arrival_seconds']*1000
    return raw,local,budgets,ref_ms

def main():
    p=json.loads((HERE/'parents.json').read_text())
    raw,local,budgets,ref_ms=compute(p)
    source_ok=p['source_blobs']==EXPECTED_BLOBS
    result={
      'task':'SPECULATIVE-BRANCH-MODEL-COST-BREAK-EVEN-20260918-001',
      'formal_invocations':1,'reruns':0,'source_blobs':p['source_blobs'],'source_identity_ok':source_ok,
      'k2_temporal_mean_ms':p['k2']['temporal_mean_ms'],'k1_temporal_mean_ms':p['k1']['temporal_mean_ms'],
      'raw_k2_advantage_ms':raw,'local_marginal_ms':local,'model_side_break_even_ms':budgets,
      'conservative_future_gate':'compare measured same-generation incremental model wall against p95 break-even budget',
      'same_generation_k2':{'incremental_model_wall_ms':None,'status':'UNMEASURED'},
      'extra_generation_k2':{'observed_full_boundary_reference_ms':ref_ms,'reference_only':True,'same_generation_cost_estimate':False},
      'full_boundary_reference_to_p95_budget_ratio':ref_ms/budgets['p95'],
      'actual_model_incremental_cost_estimated':False,
      'model_calls':0,'provider_actions':0,'gui_actions':0,'task_input_actions':0
    }
    exact=(abs(raw-7.82655)<1e-12 and all(v>0 for v in budgets.values()) and source_ok and result['same_generation_k2']['incremental_model_wall_ms'] is None and result['extra_generation_k2']['reference_only'])
    result['decision']='PASS_MODEL_BRANCH_AUTHORING_BREAK_EVEN_LOCALIZED_SCOPED' if exact else 'FAIL_INTEGRITY'
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
