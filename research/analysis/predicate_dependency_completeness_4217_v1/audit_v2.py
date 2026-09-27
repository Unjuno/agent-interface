#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path

POLICIES=('DECLARED_ONLY','COMPLETE_DECLARATION','COMPLETENESS_GATED')
SPECS={
 'READY_TO_SUBMIT':{'true_deps':('form','risk'),'declared_deps':('form',),'declaration_complete':False},
 'TARGET_MATCH':{'true_deps':('target',),'declared_deps':('target',),'declaration_complete':True},
}

def oracle(p,s):
    if not s['source_current']: return 'UNKNOWN'
    deps=SPECS[p]['true_deps']
    if any(s['generations'].get(k) is None or s['values'].get(k) is None for k in deps): return 'UNKNOWN'
    if p=='READY_TO_SUBMIT': return 'TRUE' if s['values']['form'] and not s['values']['risk'] else 'FALSE'
    if p=='TARGET_MATCH': return 'TRUE' if s['values']['target'] else 'FALSE'
    raise KeyError(p)

def graph(v):
    if any(v[p]=='UNKNOWN' for p in SPECS): return 'YIELD_UNKNOWN'
    if v['TARGET_MATCH']=='FALSE': return 'YIELD_TARGET'
    return 'SUBMIT_READY' if v['READY_TO_SUBMIT']=='TRUE' else 'CONTINUE'

def expected_key(policy,p,s):
    spec=SPECS[p]; deps=spec['true_deps'] if policy=='COMPLETE_DECLARATION' else spec['declared_deps']
    return {'predicate':p,'intent_version':s['intent_version'],'producer_version':s['producer_version'],'source_generation':s['source_generation'],'source_current':s['source_current'],'dependency_generations':{k:s['generations'].get(k) for k in deps}}

def audit(root_path,formal_path):
    root=Path(root_path); obj=json.loads(Path(formal_path).read_text()); errors=[]; checks=0
    freeze=json.loads((root/'FREEZE.json').read_text())
    for name,digest in freeze['sha256'].items():
        checks+=1
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: errors.append('source_hash:'+name)
    expected_trace=json.loads((root/'trace.json').read_text()); rows=obj.get('rows',[])
    checks+=2
    if len(rows)!=12: errors.append('row_count')
    if len(expected_trace)!=12: errors.append('trace_count')
    derived={p:{'predicate_mismatches':0,'graph_mismatches':0,'cache_hits':0,'evaluator_calls':0,'hidden_false_reuse_events':0} for p in POLICIES}
    prior_true={p:{} for p in POLICIES}
    for i,(expected,row) in enumerate(zip(expected_trace,rows)):
        checks+=5
        if row.get('step')!=i or row.get('name')!=expected['name']: errors.append(f'{i}:identity')
        if row.get('state')!=expected: errors.append(f'{i}:state')
        full={p:oracle(p,expected) for p in SPECS}
        if row.get('oracle_values')!=full or row.get('oracle_graph')!=graph(full): errors.append(f'{i}:oracle')
        policies=row.get('policies',{})
        if set(policies)!=set(POLICIES): errors.append(f'{i}:policies')
        for policy in POLICIES:
            pr=policies.get(policy,{}); values=pr.get('values',{}); events=pr.get('events',{})
            checks+=7
            if set(values)!=set(SPECS) or set(events)!=set(SPECS): errors.append(f'{i}:{policy}:shape')
            if pr.get('authority_granted') is not False: errors.append(f'{i}:{policy}:authority')
            if pr.get('graph')!=graph(values): errors.append(f'{i}:{policy}:graph_self')
            if pr.get('graph')!=graph(full): derived[policy]['graph_mismatches']+=1
            for predicate,spec in SPECS.items():
                e=events.get(predicate,{})
                checks+=6
                if e.get('cache_key')!=expected_key(policy,predicate,expected): errors.append(f'{i}:{policy}:{predicate}:key')
                if e.get('declaration_complete') is not spec['declaration_complete']: errors.append(f'{i}:{policy}:{predicate}:complete_flag')
                true_gens={k:expected['generations'].get(k) for k in spec['true_deps']}
                if e.get('true_dependency_generations')!=true_gens: errors.append(f'{i}:{policy}:{predicate}:true_gens')
                if type(e.get('hit')) is not bool: errors.append(f'{i}:{policy}:{predicate}:hit_type')
                if values.get(predicate)!=full[predicate]: derived[policy]['predicate_mismatches']+=1
                if e.get('hit'): derived[policy]['cache_hits']+=1
                else: derived[policy]['evaluator_calls']+=1
                if e.get('hidden_dependency_changed_since_cached_value') is True: derived[policy]['hidden_false_reuse_events']+=1
    checks+=12
    if obj.get('state_count')!=12 or obj.get('policy_count')!=3 or obj.get('predicate_count')!=2 or obj.get('policy_predicate_observations')!=72: errors.append('denominator')
    if obj.get('full_recompute_calls_per_policy')!=24: errors.append('full_calls')
    if obj.get('metrics')!=derived: errors.append('metrics')
    if derived['DECLARED_ONLY']['predicate_mismatches']<1 or derived['DECLARED_ONLY']['hidden_false_reuse_events']<1: errors.append('negative_control_not_discriminating')
    for policy in ('COMPLETE_DECLARATION','COMPLETENESS_GATED'):
        if derived[policy]['predicate_mismatches'] or derived[policy]['graph_mismatches'] or derived[policy]['hidden_false_reuse_events']: errors.append(policy+':unsafe')
    # Postformal v2: preserve the same gates but fail closed on truncated evidence instead of indexing past it.
    if len(rows)>1:
        if rows[1]['policies']['COMPLETE_DECLARATION']['events']['READY_TO_SUBMIT']['hit'] is not True: errors.append('complete_unrelated_ready_hit')
        if any(r['policies']['COMPLETENESS_GATED']['events']['READY_TO_SUBMIT']['hit'] for r in rows if 'policies' in r): errors.append('gated_incomplete_hit')
        if sum(bool(r['policies']['COMPLETENESS_GATED']['events']['TARGET_MATCH']['hit']) for r in rows if 'policies' in r)<1: errors.append('gated_complete_no_hit')
    else:
        errors.append('directed_gate_denominator')
    for idx in (4,):
        if idx>=len(rows): errors.append(f'{idx}:missing_directed_row'); continue
        if rows[idx]['policies']['COMPLETE_DECLARATION']['events']['READY_TO_SUBMIT']['hit'] is not False: errors.append('aba_complete_hit')
        if rows[idx]['policies']['COMPLETENESS_GATED']['events']['READY_TO_SUBMIT']['hit'] is not False: errors.append('aba_gated_hit')
    for idx in (9,10,11):
        if idx>=len(rows): errors.append(f'{idx}:missing_identity_row'); continue
        for policy in POLICIES:
            for predicate in SPECS:
                if rows[idx]['policies'][policy]['events'][predicate]['hit'] is not False: errors.append(f'{idx}:{policy}:{predicate}:identity_hit')
    if obj.get('formal_invocations')!=1 or any(obj.get(k)!=0 for k in ('reruns','replacements','tuning')): errors.append('execution_discipline')
    decision='PASS_DEPENDENCY_COMPLETENESS_GATE_SCOPED_POSTHOC_AUDIT_V2' if not errors else ('FAIL_COMPLETENESS_GATE_FALSE_REUSE' if any(x.endswith(':unsafe') for x in errors) else 'FAIL_INTEGRITY_OR_GATE')
    return {'decision':decision,'errors':errors,'checks':checks,'row_count':len(rows),'policy_predicate_observations':len(rows)*6,'derived_metrics':derived,'formal_sha256':hashlib.sha256(Path(formal_path).read_bytes()).hexdigest()}
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: audit.py ROOT FORMAL')
    r=audit(sys.argv[1],sys.argv[2]); print(json.dumps(r,sort_keys=True,indent=2)); raise SystemExit(bool(r['errors']))
