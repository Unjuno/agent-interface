import json,pathlib
root=pathlib.Path(__file__).parent
fx=json.loads((root/'fixture.json').read_text())
p=fx['pinned']
REGISTRY={
 'FOCUS_GENERATION_IDENTITY':{
   'scope':'FOCUS_OBSERVATION_CURRENTNESS',
   'role':'PREPARED_REUSABLE_VERSIONED',
   'storage':'PERSIST_DEPENDENCY',
   'source_blob':p['focus_formal_summary_blob']},
 'TARGET_HANDLE_CHECK':{
   'scope':'TARGET_HANDLE_CURRENTNESS',
   'role':'FRESH_COMMIT_BOUND_CURRENT',
   'storage':'EPHEMERAL_ONLY',
   'source_blob':p['chromium_events_blob']}
}

def adapt(row):
    spec=REGISTRY.get(row['source_type'])
    if spec is None:
        return {'disposition':'REJECT_SOURCE'}
    if row.get('source_blob')!=spec['source_blob']:
        return {'disposition':'REJECT_PROVENANCE'}
    if row.get('requested_role',spec['role'])!=spec['role']:
        return {'disposition':'REJECT_ROLE'}

    common={
      'disposition':'EMIT',
      'scope':spec['scope'],
      'role':spec['role'],
      'storage':spec['storage'],
      'source_blob':spec['source_blob']}

    if row['source_type']=='FOCUS_GENERATION_IDENTITY':
        current=(row['generation_delta']==0 and not row['identity_changed'])
        return {**common,
          'current':current,
          'lineage':row['case'],
          'prepared_version':'g0',
          'current_version':f"g{row['generation_delta']}",
          'identity_relation':'OTHER' if row['identity_changed'] else 'SAME'}

    if row['status'] not in ('VALID','MISSING'):
        return {'disposition':'REJECT_STATUS'}
    truth='TRUE' if row['status']=='VALID' and row['eligible'] else 'FALSE'
    return {**common,
      'truth':truth,
      'lineage':f"{row['handle']}@{row['observation_sequence']}",
      'handle':row['handle'],
      'observation_sequence':row['observation_sequence'],
      'patch_sha256':row.get('patch_sha256')}

results=[{'id':row['id'],'output':adapt(row)} for row in fx['rows']]
emitted=[x for x in results if x['output']['disposition']=='EMIT']
focus=[x for x in emitted if x['output']['role']=='PREPARED_REUSABLE_VERSIONED']
target=[x for x in emitted if x['output']['role']=='FRESH_COMMIT_BOUND_CURRENT']
result={
 'rows':len(results),
 'emitted':len(emitted),
 'rejected':len(results)-len(emitted),
 'focus_emitted':len(focus),
 'target_emitted':len(target),
 'persistent_target_receipts':sum(x['output']['storage'].startswith('PERSIST') for x in target),
 'outputs':results,
 'decision':None
}
pass_gate=(
 result['rows']==12 and result['emitted']==7 and result['rejected']==5 and
 len(focus)==5 and len(target)==2 and result['persistent_target_receipts']==0 and
 all(x['output']['scope']=='FOCUS_OBSERVATION_CURRENTNESS' and
     x['output']['storage']=='PERSIST_DEPENDENCY' for x in focus) and
 all(x['output']['scope']=='TARGET_HANDLE_CURRENTNESS' and
     x['output']['storage']=='EPHEMERAL_ONLY' for x in target)
)
result['decision']='PASS_REAL_SOURCE_ROLE_ADAPTER_REGISTRY_SCOPED' if pass_gate else 'FAIL_REAL_SOURCE_ROLE_ADAPTER_REGISTRY'
print(json.dumps(result,indent=2,sort_keys=True))
