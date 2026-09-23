import json,pathlib
r=json.loads((pathlib.Path(__file__).parent/'RESULT.json').read_text()); s=r['summary']; m=r['membership_shapes']
checks={'states_32':r['states']==32,'mutation_cases_160':r['mutation_cases']==160,'dynamic_exact_all':r['dynamic_exact_set_states']==32,
'dynamic_safe':s['DYNAMIC_QUERY']['unsafe_acceptances']==0,'dynamic_minimal':s['DYNAMIC_QUERY']['false_invalidations']==0,
'member_only_misses_phantoms':s['MEMBER_ONLY']['unsafe_acceptances']>0,'query_only_misses_value':s['QUERY_ONLY']['unsafe_acceptances']>0,
'static_scope_safe':s['STATIC_SCOPE']['unsafe_acceptances']==0,'static_scope_overinvalidates':s['STATIC_SCOPE']['false_invalidations']>0,
'global_more_overinvalidating':s['GLOBAL_EPOCH']['false_invalidations']>s['STATIC_SCOPE']['false_invalidations'],
'membership_shapes':m['empty']>0 and m['partial']>0 and m['full']>0,'decision_pass':r['decision']=='PASS_TYPED_QUERY_DEPENDENCY_SCOPED'}
out={'checks':checks,'pass':all(checks.values())}; print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['pass'] else 1)
