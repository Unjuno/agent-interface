import json,pathlib
r=json.loads((pathlib.Path(__file__).parent/'RESULT.json').read_text());s=r['stats'];st=r['storage']
checks={
 'rows_96':r['rows']==96,
 'role_bound_exact':s['ROLE_BOUND']['unsafe_admissions']==0 and s['ROLE_BOUND']['false_rejections']==0,
 'valid_row_exists':r['valid_oracle_rows']>0,
 'dependency_persisted':r['role_bound_persistent_dependency_receipts']==1,
 'commit_not_persisted':r['role_bound_persistent_commit_receipts']==0,
 'commit_ephemeral':st['FRESH_COMMIT_BOUND_CURRENT']['ROLE_BOUND']=='EPHEMERAL_ONLY',
 'cross_scope_replay_zero':r['role_bound_cross_intent_epoch_replay_accepts']==0,
 'bad_gate_admission_zero':r['role_bound_bad_gate_admissions']==0,
 'generic_persists_commit':r['generic_persistent_commit_receipts']==1,
 'generic_unsafe_replay':s['GENERIC_CACHE']['unsafe_admissions']>0 and 'GENERIC_CACHE' in r['unsafe_witnesses'],
 'unknown_rejected':r['unknown_role_rejected'],
 'decision_pass':r['decision']=='PASS_ROLE_BOUND_LEDGER_LIFETIME_SCOPED'
}
out={'checks':checks,'pass':all(checks.values())}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
