import json,pathlib
root=pathlib.Path(__file__).parent
fx=json.loads((root/'fixture.json').read_text())
r=json.loads((root/'RESULT.json').read_text())
out={x['id']:x['output'] for x in r['outputs']}
p=fx['pinned']

checks={
 'rows_12':r['rows']==12,
 'emit_reject_counts':r['emitted']==7 and r['rejected']==5,
 'focus_exact':True,
 'target_exact':True,
 'target_not_persisted':r['persistent_target_receipts']==0,
 'negative_controls':True,
 'provenance_exact':True,
 'decision_pass':r['decision']=='PASS_REAL_SOURCE_ROLE_ADAPTER_REGISTRY_SCOPED'
}

for row in fx['rows']:
    got=out[row['id']]
    if row['source_type']=='FOCUS_GENERATION_IDENTITY' and 'expected_current' in row:
        checks['focus_exact'] &= (
          got['disposition']=='EMIT' and
          got['role']=='PREPARED_REUSABLE_VERSIONED' and
          got['scope']=='FOCUS_OBSERVATION_CURRENTNESS' and
          got['storage']=='PERSIST_DEPENDENCY' and
          got['current']==row['expected_current'] and
          got['source_blob']==p['focus_formal_summary_blob'])
    elif row['source_type']=='TARGET_HANDLE_CHECK' and 'expected_truth' in row:
        checks['target_exact'] &= (
          got['disposition']=='EMIT' and
          got['role']=='FRESH_COMMIT_BOUND_CURRENT' and
          got['scope']=='TARGET_HANDLE_CURRENTNESS' and
          got['storage']=='EPHEMERAL_ONLY' and
          got['truth']==row['expected_truth'] and
          got['observation_sequence']==row['observation_sequence'] and
          got['source_blob']==p['chromium_events_blob'])
    elif 'expected_reject' in row:
        checks['negative_controls'] &= got['disposition']==row['expected_reject']

for x in r['outputs']:
    if x['output']['disposition']=='EMIT':
        expected=(p['focus_formal_summary_blob'] if x['output']['role']=='PREPARED_REUSABLE_VERSIONED'
                  else p['chromium_events_blob'])
        checks['provenance_exact'] &= x['output']['source_blob']==expected

audit={'checks':checks,'pass':all(checks.values())}
print(json.dumps(audit,indent=2,sort_keys=True))
raise SystemExit(0 if audit['pass'] else 1)
