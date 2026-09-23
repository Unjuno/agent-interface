import json, sys
from pathlib import Path

REQ = (
    'real_app','pre_action_decision','operation_target_choice_not_preselected',
    'finite_candidate_set','intent_fixed_predecision','independent_acceptable_set',
    'label_not_final_score_derived','arguments_complete','no_oracle_feature_leakage'
)
EXPECTED_SOURCES={
 'parent_1103':'7f0d47a7342076e3a5347e3753031f6e77c9a4b8',
 'parent_1223':'0b98bdfd7f00d063f252b5e9db27f9868eb4c9a8',
 'chromium_memory':'08fd6a91d7b71401e2c39941fa83c01119b739b4',
 'openttd_report':'83db0909c7224e25c013c3f1a37cc0e9a217284c',
 'openttd_prereg':'cd3afeac968c98cdc5413d402b863370ffcce392',
 'openttd_audit':'93d084bdcef408a3c767fbcba3a6216ddb6ebbc4',
 'mindustry_v1':'3125aa3bcf884f8e5cd33ba52c9bd2c0831b7f9a',
 'mindustry_v3':'8f3779abbc05e79389388cf16087e0226388d689',
 'compiled_v5':'1cc24856213983fb1c6292535a9d2f8d1be25234',
 'evidence_contract':'77440e2d1f2025ccab3d8ea93f1c4e50c7c54ef3',
}
# Facts frozen from source reports before formal. Auditor rejects attempts to promote a
# family by editing the ledger after the freeze.
EXPECTED_FACTS={
 'chromium_memory_ablation': {
   'rows':9,
   'must_false':['finite_candidate_set','independent_acceptable_set','label_not_final_score_derived'],
   'must_true':['real_app','pre_action_decision','operation_target_choice_not_preselected','intent_fixed_predecision','arguments_complete','no_oracle_feature_leakage'],
 },
 'openttd_positive': {
   'rows':1,
   'must_false':[],
   'must_true':list(REQ),
 },
 'openttd_no_match': {
   'rows':1,
   'must_false':[],
   'must_true':list(REQ),
 },
 'mindustry_revalidation': {
   'rows':6,
   'must_false':['operation_target_choice_not_preselected','independent_acceptable_set'],
   'must_true':['real_app','pre_action_decision','finite_candidate_set','intent_fixed_predecision','label_not_final_score_derived','arguments_complete','no_oracle_feature_leakage'],
 },
 'compiled_interface_v5': {
   'rows':4,
   'must_false':['operation_target_choice_not_preselected','independent_acceptable_set'],
   'must_true':['real_app','pre_action_decision','finite_candidate_set','intent_fixed_predecision','label_not_final_score_derived','arguments_complete','no_oracle_feature_leakage'],
 },
}

def q(e): return all(e['gates'][k] is True for k in REQ)

def recompute(ledger):
    entries=ledger['entries']; qual=[e for e in entries if q(e)]
    return {
      'reviewed_opportunities':sum(e['rows'] for e in entries),
      'oracle_qualified_rows':sum(e['rows'] for e in qual),
      'oracle_qualified_positive_rows':sum(e['rows'] for e in qual if e['semantic_class']=='positive'),
      'oracle_qualified_semantic_negative_rows':sum(e['rows'] for e in qual if e['semantic_class']=='negative'),
      'qualified_operation_families':sorted({e['operation_family'] for e in qual if e.get('operation_family')}),
      'target_alternative_rows':sum(e['rows'] for e in qual if e.get('target_alternatives',False)),
      'explicit_yield_no_local_action_rows':sum(e['rows'] for e in qual if e.get('explicit_yield_no_local_action',False)),
      'direct_1015_compatible_rows':sum(e['rows'] for e in qual if e.get('direct_1015_compatible',False)),
      'lossless_adapter_eligible_rows':sum(e['rows'] for e in qual if e.get('lossless_adapter_eligible',False)),
      'independent_split_units':len({e['split_unit'] for e in qual}),
    }

def verify(result,ledger,sources):
    errors=[]
    if sources.get('blobs')!=EXPECTED_SOURCES: errors.append('source_identity')
    by={e['id']:e for e in ledger.get('entries',[])}
    if set(by)!=set(EXPECTED_FACTS): errors.append('entry_ids')
    for eid,f in EXPECTED_FACTS.items():
        e=by.get(eid)
        if not e: continue
        if e.get('rows')!=f['rows']: errors.append(f'{eid}:rows')
        for k in f['must_true']:
            if e['gates'].get(k) is not True: errors.append(f'{eid}:{k}:expected_true')
        for k in f['must_false']:
            if e['gates'].get(k) is not False: errors.append(f'{eid}:{k}:expected_false')
    m=recompute(ledger)
    for k,v in m.items():
        if result.get(k)!=v: errors.append('metric:'+k)
    if result.get('qualified_operation_family_count')!=len(m['qualified_operation_families']):errors.append('metric:qualified_operation_family_count')
    ready_gates={
      'positive_rows_ge_32':m['oracle_qualified_positive_rows']>=32,
      'negative_rows_ge_32':m['oracle_qualified_semantic_negative_rows']>=32,
      'operation_families_ge_2':len(m['qualified_operation_families'])>=2,
      'target_alternative_rows_gt_0':m['target_alternative_rows']>0,
      'explicit_yield_no_action_gt_0':m['explicit_yield_no_local_action_rows']>0,
      'independent_split_units_ge_12':m['independent_split_units']>=12,
      'direct_1015_compatibility_for_all_qualified':m['direct_1015_compatible_rows']==m['oracle_qualified_rows'],
      'oracle_leakage_zero':True,
    }
    if result.get('ready_gates')!=ready_gates:errors.append('ready_gates')
    ready=all(ready_gates.values())
    expected='READY_RETAINED_REALDESKTOP_OPERATION_TARGET_CORPUS' if ready else ('PARTIAL_REALDESKTOP_ORACLE_PROGRESS_BLOCKED_DATA' if m['oracle_qualified_rows']>0 else 'BLOCKED_DATA_NO_NEW_ORACLE_ROWS')
    if result.get('decision')!=expected:errors.append('decision')
    if result.get('formal_invocations')!=1 or result.get('reruns')!=0:errors.append('invocations')
    if any(result.get(k)!=0 for k in ('model_calls','gui_actions','task_input_actions')):errors.append('forbidden_actions')
    return {'audit_pass':not errors,'errors':errors,'recomputed':m,'decision':expected}

def main():
    if len(sys.argv)!=5: raise SystemExit('usage: audit.py RESULT LEDGER SOURCES OUT')
    r=json.loads(Path(sys.argv[1]).read_text());l=json.loads(Path(sys.argv[2]).read_text());s=json.loads(Path(sys.argv[3]).read_text())
    o=verify(r,l,s);Path(sys.argv[4]).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
