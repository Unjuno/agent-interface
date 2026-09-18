#!/usr/bin/env python3
import copy, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from validate import evaluate
base=json.loads((Path(__file__).parent/'evidence.json').read_text())
controls={}

def run(name, mut, expected_error):
    d=copy.deepcopy(base); mut(d); r=evaluate(d); controls[name]=r
    assert r['decision']=='FAIL_INTEGRITY', (name,r)
    assert expected_error in r['errors'], (name,r)

baseline=evaluate(base)
assert baseline['decision']=='HOLD_NO_REAL_ADAPTIVE_RESIDUAL'
assert baseline['failed_prerequisites']==[
    'representation_sufficient_for_frozen_residual',
    'genuine_needs_policy_residual',
    'enough_leakage_free_rows',
    'independent_semantic_effect_oracle']

run('consume_unpublished_1223',
    lambda d: d['integrity'].__setitem__('uses_unpublished_active_result',True),
    'unpublished_active_result_consumed')
run('five_rows_declared_enough',
    lambda d: d['activation'].__setitem__('enough_leakage_free_rows',True),
    'activation_rows_contradict_source')
run('invent_independent_oracle',
    lambda d: d['activation'].__setitem__('independent_semantic_effect_oracle',True),
    'oracle_claim_contradicts_source')
run('relabel_deterministic_rows_as_residual',
    lambda d: (d['activation'].__setitem__('genuine_needs_policy_residual',True), d['integrity'].__setitem__('claims_deterministic_exact_rows_as_residual',True)),
    'deterministic_closure_relabelled_as_residual')
run('future_or_oracle_feature_leakage',
    lambda d: d['integrity'].__setitem__('uses_future_or_oracle_as_feature',True),
    'feature_leakage')

out={'pass':True,'baseline':baseline,'controls':controls}
print(json.dumps(out,sort_keys=True))
(Path(__file__).parent/'controls.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
