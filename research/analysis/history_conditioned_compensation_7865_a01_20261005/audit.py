import json,sys
from pathlib import Path
fixture=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
candidate=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
errors=[]
if candidate.get('allocation_id')!=fixture['allocation_id']: errors.append('allocation_id')
by={r.get('case_id'):r for r in candidate.get('rows',[])}
expected_cases={c['id'] for c in fixture['cases']}
if set(by)!=expected_cases: errors.append('case_set')
for c in fixture['cases']:
    row=by.get(c['id'],{}).get('policies',{})
    base=fixture['base_state']; fld=fixture['agent_effect']['field']; before=fixture['agent_effect']['before']; effect=fixture['agent_effect']['after']; same=fixture['base_identity']
    def must(policy, decision, reason=None, state=None, changed=None):
        got=row.get(policy,{})
        if got.get('decision')!=decision: errors.append(c['id']+':'+policy+':decision')
        if reason is not None and got.get('reason')!=reason: errors.append(c['id']+':'+policy+':reason')
        if state is not None and got.get('state_after')!=state: errors.append(c['id']+':'+policy+':state')
        if changed is not None and got.get('new_effect_recorded')!=changed: errors.append(c['id']+':'+policy+':effect_record')
        if got.get('exact_rollback_claim') is not False: errors.append(c['id']+':'+policy+':exact_rollback_overclaim')
    def add(s,k,v): x=dict(s);x[k]=v;return x
    p='WHOLE_OBJECT_VERSION_GUARD'; q='FIELD_SCOPED_COMPARE_AND_COMPENSATE'; n='NO_AUTO_COMPENSATION'; b='BLIND_INVERSE'
    if c['id']=='no_interleaving':
        must(p,'COMPENSATED','same_object_generation',base,True); must(q,'COMPENSATED','field_compare_and_compensate',base,True)
    elif c['id']=='disjoint_field_update':
        expected=add(c['state'],fld,before)
        must(p,'CONFLICT','object_generation_changed',c['state'],False); must(q,'COMPENSATED','field_compare_and_compensate',expected,True)
        if row.get(q,{}).get('external_disjoint_update_preserved') is not True: errors.append('disjoint_update_lost')
        if row.get(b,{}).get('state_after')!=base or row.get(b,{}).get('external_disjoint_update_preserved') is not False: errors.append('blind_inverse_did_not_expose_lost_update')
    elif c['id']=='same_field_update':
        must(p,'CONFLICT','object_generation_changed',c['state'],False); must(q,'CONFLICT','agent_field_changed_in_history',c['state'],False)
    elif c['id']=='aba_write_away_back':
        must(p,'CONFLICT','object_generation_changed',c['state'],False); must(q,'CONFLICT','agent_field_changed_in_history',c['state'],False)
    elif c['id']=='object_replacement':
        must(p,'CONFLICT','target_identity_changed',c['state'],False); must(q,'CONFLICT','target_identity_changed',c['state'],False)
    elif c['id']=='unknown_event_order':
        must(p,'UNKNOWN','identity_or_version_history_unverified',c['state'],False); must(q,'UNKNOWN','identity_or_history_unverified',c['state'],False)
    elif c['id']=='unknown_identity':
        must(p,'UNKNOWN','identity_or_version_history_unverified',c['state'],False); must(q,'UNKNOWN','identity_or_history_unverified',c['state'],False)
    elif c['id']=='mutation_missing_version_increment':
        must(p,'UNKNOWN','identity_or_version_history_unverified',c['state'],False); must(q,'UNKNOWN','identity_or_history_unverified',c['state'],False)
    elif c['id']=='mutation_corrupt_footprint':
        must(q,'UNKNOWN','effect_footprint_unverified',c['state'],False)
    elif c['id']=='mutation_reordered_history':
        must(q,'UNKNOWN','identity_or_history_unverified',c['state'],False)
    must(n,'REFUSED','manual_recovery_required',c['state'],False)
    for pol,out in row.items():
        if out.get('new_effect_recorded') and out.get('decision')!='COMPENSATED': errors.append(c['id']+':effect_without_compensation')
# Global discriminators
if by.get('disjoint_field_update',{}).get('policies',{}).get('FIELD_SCOPED_COMPARE_AND_COMPENSATE',{}).get('agent_field_restored') is not True: errors.append('agent_field_not_restored')
if by.get('disjoint_field_update',{}).get('policies',{}).get('FIELD_SCOPED_COMPARE_AND_COMPENSATE',{}).get('state_after',{}).get('b')!='Y': errors.append('external_field_not_preserved')
if candidate.get('status')!='CANDIDATE_METHOD_RESULT': errors.append('candidate_status')
print(json.dumps({'allocation_id':fixture['allocation_id'],'independent_auditor':'raw_only_policy_oracle_v1','status':'PASS_METHOD_SCOPED' if not errors else 'FAIL_METHOD','independent_case_match':not errors,'errors':errors,'gate_results':{'blind_inverse_loses_disjoint_write':not bool(errors),'whole_object_guard_refuses_disjoint_update':not bool(errors),'field_policy_preserves_disjoint_update':not bool(errors),'same_field_and_aba_refused':not bool(errors),'replacement_and_unknown_history_refused':not bool(errors),'mutations_fail_closed':not bool(errors),'no_exact_rollback_overclaim':not bool(errors)}} ,sort_keys=True,separators=(',',':')))
