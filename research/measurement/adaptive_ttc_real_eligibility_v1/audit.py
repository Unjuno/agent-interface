#!/usr/bin/env python3
import hashlib, json
from pathlib import Path
R=Path(__file__).parent
e=json.loads((R/'evidence.json').read_text())
r=json.loads((R/'result.json').read_text())
c=json.loads((R/'controls.json').read_text())
errors=[]
expected_blobs={
 'cross_domain_rule_vm_result':'20ed6bc4c682e5d2e1cf60fb44f4fcdf5a1bd21d',
 'map01_v31_representation':'9b131cc22860ca210959202790688a0759bc8b24',
 'operation_target_private_x11_result':'0b98bdfd7f00d063f252b5e9db27f9868eb4c9a8'}
for k,v in expected_blobs.items():
    if e['sources'].get(k,{}).get('git_blob')!=v: errors.append('blob:'+k)
vm=e['sources']['cross_domain_rule_vm_result']
if not (vm['decision']=='PASS_CROSS_DOMAIN_RULE_VM_SCOPED' and vm['chromium_exact'] and vm['chromium_rows']==8192 and vm['openttd_retained_exact']==5 and vm['controls_fail_closed'] and vm['learned_residual_rows']==0): errors.append('deterministic_cross_domain_closure')
v31=e['sources']['map01_v31_representation']
if not (v31['decision']=='PASS_LAST_EFFECT_REPRESENTATION_V31_R2_SCOPED' and v31['eligible_rows']==5 and v31['enriched_collisions']==0 and v31['report_boundary_requires_larger_corpus']): errors.append('v31_boundary')
x=e['sources']['operation_target_private_x11_result']
if not (x['decision']=='PASS_PRIVATE_X11_OPERATION_TARGET_CONTRACT_SCOPED' and x['git_blob']==expected_blobs['operation_target_private_x11_result'] and x['audit_git_blob']=='9f22e0291e38b450bdbac105d5ec42b3e4941b65' and x['rows']==96 and x['acceptable_membership']==96 and x['positive_coverage']==48 and x['semantic_negatives']==48 and x['false_executable_negatives']==0 and x['stale_executable']==0 and x['missing_arguments']==0 and x['public_oracle_leakage']==0 and x['independent_decision_oracle'] and x['learned_residual_rows']==0): errors.append('private_x11_closure')
expected_failed=['representation_sufficient_for_frozen_residual','genuine_needs_policy_residual','enough_leakage_free_rows']
if r.get('decision')!='HOLD_NO_REAL_ADAPTIVE_RESIDUAL' or r.get('eligible') is not False or r.get('errors')!=[] or r.get('failed_prerequisites')!=expected_failed: errors.append('result')
if e['activation'].get('real_caller_visible_contract') is not True or e['activation'].get('independent_semantic_effect_oracle') is not True or e['activation'].get('first_rung_no_live_input_authority') is not True: errors.append('positive_prereqs')
for k in expected_failed:
    if e['activation'].get(k) is not False: errors.append('failed_prereq:'+k)
if not c.get('pass') or len(c.get('controls',{}))!=5: errors.append('controls')
for name,z in c.get('controls',{}).items():
    if z.get('decision')!='FAIL_INTEGRITY': errors.append('control_not_rejected:'+name)
out={
 'pass':not errors,
 'errors':errors,
 'decision':'HOLD_NO_REAL_ADAPTIVE_RESIDUAL' if not errors else 'FAIL_INTEGRITY',
 'snapshot_main':e['snapshot_main'],
 'source_blobs':expected_blobs,
 'private_x11_audit_blob':'9f22e0291e38b450bdbac105d5ec42b3e4941b65',
 'map01_eligible_rows':v31['eligible_rows'],
 'private_x11_rows':x['rows'],
 'learned_residual_rows_cross_domain':vm['learned_residual_rows'],
 'learned_residual_rows_private_x11':x['learned_residual_rows'],
 'failed_prerequisites':expected_failed,
 'corruption_controls_rejected':len(c.get('controls',{})),
 'result_sha256':hashlib.sha256((R/'result.json').read_bytes()).hexdigest(),
 'evidence_sha256':hashlib.sha256((R/'evidence.json').read_bytes()).hexdigest(),
 'validator_sha256':hashlib.sha256((R/'validate.py').read_bytes()).hexdigest(),
}
(R/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
raise SystemExit(bool(errors))
