import json, sys
from pathlib import Path

f=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
rows=[]
def outcome(case, policy):
    state=dict(case['state']); ident=case['identity']; events=case['events']; gen=case['generation']
    decision='CONFLICT'; reason='policy_refusal'; after=dict(state); after_id=ident; after_gen=gen; changed=False
    if policy=='BLIND_INVERSE':
        after=dict(f['base_state']); changed=True; decision='COMPENSATED'; reason='unconditional_snapshot_inverse'
    elif policy=='WHOLE_OBJECT_VERSION_GUARD':
        if ident is None or not case['history_complete'] or not case['version_integrity']:
            decision='UNKNOWN'; reason='identity_or_version_history_unverified'
        elif ident!=f['base_identity']:
            reason='target_identity_changed'
        elif gen!=f['post_effect_generation']:
            reason='object_generation_changed'
        else:
            after=dict(f['base_state']); after_gen=gen+1; changed=True; decision='COMPENSATED'; reason='same_object_generation'
    elif policy=='FIELD_SCOPED_COMPARE_AND_COMPENSATE':
        if ident is None or not case['history_complete'] or not case['ordering_known'] or not case['version_integrity']:
            decision='UNKNOWN'; reason='identity_or_history_unverified'
        elif ident!=f['base_identity']:
            reason='target_identity_changed'
        elif not case['footprint_verified'] or case['footprint_claim']!=f['agent_effect']['footprint']:
            decision='UNKNOWN'; reason='effect_footprint_unverified'
        elif any(e.get('field')==f['agent_effect']['field'] for e in events):
            reason='agent_field_changed_in_history'
        elif state.get(f['agent_effect']['field'])!=f['agent_effect']['after']:
            reason='expected_post_effect_value_mismatch'
        else:
            after[f['agent_effect']['field']]=f['agent_effect']['before']; after_gen=gen+1; changed=True; decision='COMPENSATED'; reason='field_compare_and_compensate'
    elif policy=='NO_AUTO_COMPENSATION':
        decision='REFUSED'; reason='manual_recovery_required'
    return {'decision':decision,'reason':reason,'state_after':after,'identity_after':after_id,'generation_after':after_gen,'new_effect_recorded':changed,'exact_rollback_claim':False,'external_disjoint_update_preserved':all(after.get(k)==v for k,v in state.items() if k!=f['agent_effect']['field']),'agent_field_restored':after.get(f['agent_effect']['field'])==f['agent_effect']['before'] if changed else False}
for c in f['cases']:
    rows.append({'case_id':c['id'],'policies':{p:outcome(c,p) for p in f['policies']}})
print(json.dumps({'allocation_id':f['allocation_id'],'fixture_schema':f['schema'],'status':'CANDIDATE_METHOD_RESULT','rows':rows},sort_keys=True,separators=(',',':')))
