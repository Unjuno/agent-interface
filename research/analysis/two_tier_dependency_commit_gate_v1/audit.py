import json,pathlib
r=json.loads((pathlib.Path(__file__).parent/'RESULT.json').read_text());s=r['stats'];w=r['unsafe_witnesses']
checks={
 'rows_24':r['rows']==24,
 'two_tier_exact':s['TWO_TIER']['unsafe_admissions']==0 and s['TWO_TIER']['false_rejections']==0,
 'dependency_only_unsafe':s['DEP_ONLY']['unsafe_admissions']>0 and 'DEP_ONLY' in w,
 'gate_only_unsafe':s['GATE_ONLY']['unsafe_admissions']>0 and 'GATE_ONLY' in w,
 'cached_gate_unsafe':s['CACHED_GATE']['unsafe_admissions']>0 and 'CACHED_GATE' in w,
 'valid_rows_exist':r['valid_oracle_rows']>0,
 'bad_gate_never_admitted':r['two_tier_bad_gate_admissions']==0,
 'scalar_safe_but_overconservative':s['SCALAR_ALL_CURRENT']['unsafe_admissions']==0 and s['SCALAR_ALL_CURRENT']['false_rejections']>0,
 'roles_retained':r['role_labels']==['PREPARED_REUSABLE_VERSIONED','FRESH_COMMIT_BOUND_CURRENT'],
 'decision_pass':r['decision']=='PASS_TWO_TIER_DEPENDENCY_COMMIT_GATE_SCOPED'
}
out={'checks':checks,'pass':all(checks.values())}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
