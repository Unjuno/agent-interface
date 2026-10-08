import json,pathlib
r=json.loads((pathlib.Path(__file__).parent/'RESULT.json').read_text()); s=r['summary']; t=r['target_counts']
checks={
 'states_16':r['states']==16,'mutation_cases_64':r['mutation_cases']==64,'dynamic_exact_all':r['dynamic_exact_set_states']==16,
 'dynamic_safe':s['DYNAMIC_RESOLVE']['unsafe_acceptances']==0,'dynamic_minimal':s['DYNAMIC_RESOLVE']['false_invalidations']==0,
 'concrete_only_misses_retarget':s['CONCRETE_ONLY']['unsafe_acceptances']>0,
 'alias_only_misses_object':s['ALIAS_ONLY']['unsafe_acceptances']>0,
 'static_both_safe':s['STATIC_BOTH']['unsafe_acceptances']==0,'static_both_overinvalidates':s['STATIC_BOTH']['false_invalidations']>0,
 'global_more_overinvalidating':s['GLOBAL_EPOCH']['false_invalidations']>s['STATIC_BOTH']['false_invalidations'],
 'both_targets':t['A']==8 and t['B']==8,'decision_pass':r['decision']=='PASS_TYPED_RESOLVE_DEPENDENCY_SCOPED'}
out={'checks':checks,'pass':all(checks.values())}; print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['pass'] else 1)
