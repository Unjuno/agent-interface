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
 'operation_target_realstate_reservation':'eaf2e5c01288e2531a1767ffd22731ee6d9bb646'}
for k,v in expected_blobs.items():
    if e['sources'].get(k,{}).get('git_blob')!=v: errors.append('blob:'+k)
vm=e['sources']['cross_domain_rule_vm_result']
if not (vm['decision']=='PASS_CROSS_DOMAIN_RULE_VM_SCOPED' and vm['chromium_exact'] and vm['chromium_rows']==8192 and vm['openttd_retained_exact']==5 and vm['controls_fail_closed']): errors.append('deterministic_closure')
v31=e['sources']['map01_v31_representation']
if not (v31['decision']=='PASS_LAST_EFFECT_REPRESENTATION_V31_R2_SCOPED' and v31['eligible_rows']==5 and v31['enriched_collisions']==0 and v31['report_boundary_requires_larger_corpus'] and not v31['independent_semantic_effect_oracle']): errors.append('v31_boundary')
if e['sources']['operation_target_realstate_reservation']['status']!='ACTIVE_UPSTREAM_RESULT_NOT_CONSUMED': errors.append('active_upstream_boundary')
expected_failed=['representation_sufficient_for_frozen_residual','genuine_needs_policy_residual','enough_leakage_free_rows','independent_semantic_effect_oracle']
if r.get('decision')!='HOLD_NO_REAL_ADAPTIVE_RESIDUAL' or r.get('eligible') is not False or r.get('errors')!=[] or r.get('failed_prerequisites')!=expected_failed: errors.append('result')
if e['activation'].get('real_caller_visible_contract') is not True or e['activation'].get('first_rung_no_live_input_authority') is not True: errors.append('positive_prereqs')
for k in expected_failed:
    if e['activation'].get(k) is not False: errors.append('failed_prereq:'+k)
if not c.get('pass') or len(c.get('controls',{}))!=5: errors.append('controls')
for name,x in c.get('controls',{}).items():
    if x.get('decision')!='FAIL_INTEGRITY': errors.append('control_not_rejected:'+name)
out={
 'pass':not errors,
 'errors':errors,
 'decision':'HOLD_NO_REAL_ADAPTIVE_RESIDUAL' if not errors else 'FAIL_INTEGRITY',
 'snapshot_main':e['snapshot_main'],
 'source_blobs':expected_blobs,
 'eligible_rows':v31['eligible_rows'],
 'failed_prerequisites':expected_failed,
 'corruption_controls_rejected':len(c.get('controls',{})),
 'result_sha256':hashlib.sha256((R/'result.json').read_bytes()).hexdigest(),
 'evidence_sha256':hashlib.sha256((R/'evidence.json').read_bytes()).hexdigest(),
 'validator_sha256':hashlib.sha256((R/'validate.py').read_bytes()).hexdigest(),
}
(R/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
raise SystemExit(bool(errors))
