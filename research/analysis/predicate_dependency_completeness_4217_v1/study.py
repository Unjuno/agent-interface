#!/usr/bin/env python3
from __future__ import annotations
import json, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
POLICIES=('DECLARED_ONLY','COMPLETE_DECLARATION','COMPLETENESS_GATED')
SPECS={
 'READY_TO_SUBMIT':{'true_deps':('form','risk'),'declared_deps':('form',),'declaration_complete':False},
 'TARGET_MATCH':{'true_deps':('target',),'declared_deps':('target',),'declaration_complete':True},
}

def oracle(predicate,state):
    if not state['source_current']:
        return 'UNKNOWN'
    deps=SPECS[predicate]['true_deps']
    if any(state['generations'].get(k) is None or state['values'].get(k) is None for k in deps):
        return 'UNKNOWN'
    if predicate=='READY_TO_SUBMIT':
        return 'TRUE' if state['values']['form'] and not state['values']['risk'] else 'FALSE'
    if predicate=='TARGET_MATCH':
        return 'TRUE' if state['values']['target'] else 'FALSE'
    raise KeyError(predicate)

def graph(values):
    if any(values[p]=='UNKNOWN' for p in SPECS): return 'YIELD_UNKNOWN'
    if values['TARGET_MATCH']=='FALSE': return 'YIELD_TARGET'
    return 'SUBMIT_READY' if values['READY_TO_SUBMIT']=='TRUE' else 'CONTINUE'

def cache_key(policy,predicate,state):
    spec=SPECS[predicate]
    deps=spec['true_deps'] if policy=='COMPLETE_DECLARATION' else spec['declared_deps']
    return {
      'predicate':predicate,
      'intent_version':state['intent_version'],
      'producer_version':state['producer_version'],
      'source_generation':state['source_generation'],
      'source_current':state['source_current'],
      'dependency_generations':{k:state['generations'].get(k) for k in deps},
    }

def run(trace):
    caches={p:{} for p in POLICIES}
    metrics={p:{'evaluator_calls':0,'cache_hits':0,'predicate_mismatches':0,'graph_mismatches':0,'hidden_false_reuse_events':0} for p in POLICIES}
    rows=[]
    for state in trace:
        full={p:oracle(p,state) for p in SPECS}
        prow={}
        for policy in POLICIES:
            values={}; events={}
            for predicate,spec in SPECS.items():
                prior=caches[policy].get(predicate)
                key=cache_key(policy,predicate,state)
                true_gens={k:state['generations'].get(k) for k in spec['true_deps']}
                t0=time.perf_counter_ns()
                gated=(policy=='COMPLETENESS_GATED' and not spec['declaration_complete'])
                key_valid=state['source_current'] and all(v is not None for v in key['dependency_generations'].values())
                if (not gated) and prior is not None and key_valid and prior['key']==key:
                    value=prior['value']; hit=True; reason='HIT'; metrics[policy]['cache_hits']+=1
                    hidden_changed=(prior['true_dependency_generations']!=true_gens)
                    if hidden_changed:
                        metrics[policy]['hidden_false_reuse_events']+=1
                else:
                    value=oracle(predicate,state); hit=False; hidden_changed=False; metrics[policy]['evaluator_calls']+=1
                    if gated: reason='DECLARATION_INCOMPLETE'
                    elif prior is None: reason='COLD'
                    elif prior['key']['source_generation']!=key['source_generation']: reason='SOURCE_GENERATION'
                    elif prior['key']['intent_version']!=key['intent_version']: reason='INTENT_VERSION'
                    elif prior['key']['producer_version']!=key['producer_version']: reason='PRODUCER_VERSION'
                    else: reason='DEPENDENCY_GENERATION'
                    if not gated:
                        caches[policy][predicate]={'key':key,'value':value,'true_dependency_generations':true_gens}
                t1=time.perf_counter_ns()
                values[predicate]=value
                events[predicate]={
                  'hit':hit,'reason':reason,'lookup_ns':t1-t0,'cache_key':key,
                  'declaration_complete':spec['declaration_complete'],
                  'true_dependency_generations':true_gens,
                  'hidden_dependency_changed_since_cached_value':hidden_changed,
                }
                if value!=full[predicate]: metrics[policy]['predicate_mismatches']+=1
            g=graph(values); fg=graph(full)
            if g!=fg: metrics[policy]['graph_mismatches']+=1
            prow[policy]={'values':values,'graph':g,'events':events,'authority_granted':False}
        rows.append({'step':state['step'],'name':state['name'],'state':state,'oracle_values':full,'oracle_graph':graph(full),'policies':prow})
    return {
      'allocation':'predicate-cache-completeness-4233-20260923-01',
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'state_count':len(trace),'policy_count':len(POLICIES),'predicate_count':len(SPECS),
      'policy_predicate_observations':len(trace)*len(POLICIES)*len(SPECS),
      'full_recompute_calls_per_policy':len(trace)*len(SPECS),
      'metrics':metrics,'rows':rows,
    }

def main():
    import sys
    if len(sys.argv)!=2: raise SystemExit('usage: study.py OUTPUT')
    trace=json.loads((ROOT/'trace.json').read_text())
    result=run(trace)
    out=Path(sys.argv[1]); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
