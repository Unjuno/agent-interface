import argparse, copy, hashlib, json, pathlib

EXPECTED={'positive':'PASS','wrong_target':'FAIL','collateral':'FAIL','unsaved':'FAIL','unknown':'UNKNOWN'}
COVERAGE={'positive','wrong_target','collateral','unsaved','unknown'}
V1_SHA=hashlib.sha256(b"""def score(case, app_profile):
    if case.get('saved') is None or case.get('selected_id') is None:
        return 'UNKNOWN'
    if case.get('saved') is False or case.get('collateral'):
        return 'FAIL'
    return 'PASS' if case['selected_id'] == case['target'] else 'FAIL'
""").hexdigest()
# The frozen candidate pins this hash in FREEZE.json; audit's expected values and derivation are separately authored.

def validate(raw, freeze, deck):
    errors=[]
    if raw.get('freeze_id') != freeze.get('freeze_id'): errors.append('freeze_id_mismatch')
    if raw.get('deck_sha256') != freeze.get('deck_canonical_sha256'): errors.append('deck_hash_mismatch')
    if hashlib.sha256(pathlib.Path('deck.json').read_bytes()).hexdigest() != freeze.get('deck_source_sha256'): errors.append('deck_source_hash_mismatch')
    if hashlib.sha256(json.dumps(deck,sort_keys=True,separators=(',',':')).encode()).hexdigest() != freeze.get('deck_canonical_sha256'): errors.append('deck_canonical_hash_mismatch')
    if hashlib.sha256(json.dumps(deck['frozen_reference_labels'],sort_keys=True,separators=(',',':')).encode()).hexdigest() != freeze.get('reference_lock_sha256'): errors.append('reference_lock_file_mismatch')
    if raw.get('reference_lock_sha256') != freeze.get('reference_lock_sha256'): errors.append('reference_lock_mismatch')
    if raw.get('candidate_source_sha256') != freeze.get('candidate_source_sha256'): errors.append('candidate_source_mismatch')
    if raw.get('run_order') != ['precheck','candidate_event','postcheck']: errors.append('postcheck_order_missing_or_changed')
    if len(raw.get('results',[])) != 4: errors.append('scenario_denominator_mismatch')
    by={x.get('scenario'):x for x in raw.get('results',[])}
    expected_post={
      'nominal': {'positive':'PASS','wrong_target':'FAIL','collateral':'FAIL','unsaved':'FAIL','unknown':'UNKNOWN'},
      'semantic_drift_unchanged_scorer': {'positive':'PASS','wrong_target':'FAIL','collateral':'FAIL','unsaved':'FAIL','unknown':'UNKNOWN'},
      'equivalent_version_change': {'positive':'PASS','wrong_target':'FAIL','collateral':'FAIL','unsaved':'FAIL','unknown':'UNKNOWN'},
      'out_of_coverage': {'positive':'PASS','wrong_target':'FAIL','collateral':'FAIL','unsaved':'FAIL','unknown':'UNKNOWN'} }
    expected_references={
      'nominal': {'positive':'PASS','wrong_target':'FAIL','collateral':'FAIL','unsaved':'FAIL','unknown':'UNKNOWN'},
      'semantic_drift_unchanged_scorer': {'positive':'FAIL','wrong_target':'PASS','collateral':'FAIL','unsaved':'FAIL','unknown':'UNKNOWN'},
      'equivalent_version_change': {'positive':'PASS','wrong_target':'FAIL','collateral':'FAIL','unsaved':'FAIL','unknown':'UNKNOWN'},
      'out_of_coverage': {'positive':'PASS','wrong_target':'FAIL','collateral':'FAIL','unsaved':'FAIL','unknown':'UNKNOWN'} }
    for name in ['nominal','semantic_drift_unchanged_scorer','equivalent_version_change','out_of_coverage']:
        if name not in by: errors.append('scenario_missing:'+name); continue
        s=by[name]
        for k in ('precheck','postcheck'):
            rows=s.get(k,{}).get('rows',[])
            if [r.get('case_id') for r in rows] != list(EXPECTED): errors.append(f'{name}_{k}_deck_incomplete')
            for row in rows:
                cid=row.get('case_id')
                if cid in EXPECTED and row.get('frozen_label') != EXPECTED[cid]: errors.append(f'{name}_{k}_reference_label_mismatch:{cid}')
                table=EXPECTED if k=='precheck' else expected_post[name]
                reference=EXPECTED if k=='precheck' else expected_references[name]
                if cid in EXPECTED and row.get('prediction') != table[cid]: errors.append(f'{name}_{k}_unexpected_prediction:{cid}')
                if cid in EXPECTED and row.get('independent_reference') != reference[cid]: errors.append(f'{name}_{k}_independent_reference_mismatch:{cid}')
        if not s.get('postcheck',{}).get('rows'): errors.append(name+'_postcheck_missing')
    drift=by.get('semantic_drift_unchanged_scorer',{})
    drift_bad=any(r.get('prediction') != r.get('independent_reference') for r in drift.get('postcheck',{}).get('rows',[]))
    if not drift.get('scorer_hash_unchanged_from_v1') or not drift_bad: errors.append('semantic_drift_not_demonstrated_under_same_scorer_hash')
    if drift.get('disposition') != 'HOLD_ORACLE_DRIFT': errors.append('drift_interval_not_held')
    eq=by.get('equivalent_version_change',{})
    if eq.get('scorer_hash_unchanged_from_v1') or eq.get('disposition') != 'ELIGIBLE_FOR_FURTHER_TASK_AUDIT': errors.append('equivalent_version_control_false_reject')
    out=by.get('out_of_coverage',{})
    if out.get('coverage_declared') is not False or out.get('disposition') != 'UNKNOWN_COVERAGE': errors.append('out_of_coverage_not_unknown')
    return errors

def run():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',required=True); ap.add_argument('--deck',required=True); ap.add_argument('--freeze',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    if hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest() != json.loads(pathlib.Path(a.freeze).read_text())['audit_source_sha256']:
        raise SystemExit('FROZEN_AUDITOR_HASH_MISMATCH')
    raw=json.loads(pathlib.Path(a.raw).read_text()); deck=json.loads(pathlib.Path(a.deck).read_text(encoding='utf-8-sig')); freeze=json.loads(pathlib.Path(a.freeze).read_text())
    base=validate(raw,freeze,deck); mutations=[]
    m=copy.deepcopy(raw); m['run_order']=['precheck','candidate_event']; mutations.append(('omit_postcheck',m))
    m=copy.deepcopy(raw); m['reference_lock_sha256']='backfilled-after-candidate'; m['results'][0]['postcheck']['rows'][0]['frozen_label']='FAIL'; mutations.append(('swap_reference_label',m))
    m=copy.deepcopy(raw); next(r for r in m['results'] if r['scenario']=='nominal')['postcheck']['rows'][-1]['prediction']='PASS'; mutations.append(('unknown_as_pass',m))
    m=copy.deepcopy(raw); m['reference_lock_sha256']='new-reference-created-after-candidate'; mutations.append(('backfill_reference',m))
    mutation_results=[{'mutation':name,'rejected':bool(validate(mut,freeze,deck)),'errors':validate(mut,freeze,deck)} for name,mut in mutations]
    report={'status':'PASS_METHOD_SCOPED' if not base and all(x['rejected'] for x in mutation_results) else 'FAIL_T0_CONTRACT',
      'base_errors':base,'mutation_results':mutation_results,'scenario_dispositions':{x['scenario']:x['disposition'] for x in raw.get('results',[])},
      'scope':'finite synthetic method construction only; no empirical GUI scorer drift or task-effect claim'}
    pathlib.Path(a.out).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,sort_keys=True))
if __name__=='__main__': run()
