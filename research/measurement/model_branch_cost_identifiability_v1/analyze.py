import json, hashlib, itertools, sys
from pathlib import Path
HERE=Path(__file__).parent

def row(x):
    keys=['run','i','img','input','cached','output','reasoning','model_ns','effect','state','primary','branches','session']
    return dict(zip(keys,x))

def gate(a,b):
    return {
      'model_effort': True,
      'exact_image': a['img']==b['img'],
      'effect_memory': a['effect']==b['effect'],
      'action_state': a['state']==b['state'],
      'primary_shape': a['primary']==b['primary'],
      'cache_counters': (a['input'],a['cached'])==(b['input'],b['cached']),
      'session_state': a['session']==b['session'],
      'branch_count_diff': a['branches']!=b['branches'],
    }

def main():
    d=json.loads((HERE/'ledger.json').read_text())
    rows=[row(x) for x in d['rows']]
    g=[x for x in rows if x['run']=='grouped']; u=[x for x in rows if x['run']=='ungrouped']
    pairs=[]; fail_counts={k:0 for k in ['exact_image','effect_memory','action_state','primary_shape','cache_counters','session_state']}
    same_image=0; diff_branch=0; admissible=[]
    for a,b in itertools.product(g,u):
        q=gate(a,b)
        if q['exact_image']: same_image+=1
        if q['branch_count_diff']: diff_branch+=1
        for k in fail_counts:
            if not q[k]: fail_counts[k]+=1
        matched=all(q[k] for k in ['model_effort','exact_image','effect_memory','action_state','primary_shape','cache_counters','session_state'])
        if matched and q['branch_count_diff']:
            admissible.append({'g':a['i'],'u':b['i'],'gates':q})
        pairs.append({'g':a['i'],'u':b['i'],'gates':q,'admissible':bool(matched and q['branch_count_diff'])})
    wr=d['whole_run']
    diagnostic={
      'contingencies_delta_grouped_minus_ungrouped':wr['grouped']['contingencies_authored']-wr['ungrouped']['contingencies_authored'],
      'model_seconds_delta':wr['grouped']['model_seconds']-wr['ungrouped']['model_seconds'],
      'input_tokens_delta':wr['grouped']['input_tokens']-wr['ungrouped']['input_tokens'],
      'cached_input_tokens_delta':wr['grouped']['cached_input_tokens']-wr['ungrouped']['cached_input_tokens'],
      'output_tokens_delta':wr['grouped']['output_tokens']-wr['ungrouped']['output_tokens'],
      'reasoning_output_tokens_delta':wr['grouped']['reasoning_output_tokens']-wr['ungrouped']['reasoning_output_tokens'],
      'causal_per_branch_estimate': None
    }
    probes=d['probe_usage']
    endpoint=all(p['audit_passed'] and all(type(p[k]) is int and p[k]>=0 for k in ('input','cached','output','reasoning')) for p in probes)
    result={
      'task':d['task'],'formal_invocations':1,'reruns':0,
      'source_blobs':d['source_blobs'],'rows':len(rows),'candidate_pairs':len(pairs),
      'different_branch_count_pairs':diff_branch,'same_image_pairs':same_image,
      'admissible_pairs':admissible,'admissible_pair_count':len(admissible),
      'gate_failure_counts':fail_counts,
      'provider_usage_endpoint_confirmed':endpoint,
      'provider_probe_usage':probes,
      'whole_run_noncausal_diagnostic':diagnostic,
      'per_branch_cost_emitted':False,
      'model_calls':0,'gui_actions':0,'task_input_actions':0
    }
    if not endpoint:
        result['decision']='HOLD_SOURCE_GAP'
    elif len(admissible)==0:
        result['decision']='PASS_RETAINED_MODEL_BRANCH_COST_NOT_IDENTIFIABLE_SCOPED'
    else:
        result['decision']='PASS_RETAINED_MODEL_BRANCH_COST_IDENTIFIABLE_SCOPED'
    raw=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    (HERE/'RESULT.json').write_bytes(raw)
    (HERE/'PAIR_LEDGER.json').write_text(json.dumps(pairs,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
