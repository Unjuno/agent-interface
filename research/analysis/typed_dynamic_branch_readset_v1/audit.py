import json, pathlib
r=json.loads((pathlib.Path(__file__).parent/'RESULT.json').read_text())
s=r['summary']; b=r['branch_counts']
checks={
 'states_16':r['states']==16,
 'mutation_cases_64':r['mutation_cases']==64,
 'dynamic_exact_all_states':r['dynamic_exact_set_states']==16,
 'dynamic_safe':s['DYNAMIC_TYPED']['unsafe_acceptances']==0,
 'dynamic_no_false_invalidations':s['DYNAMIC_TYPED']['false_invalidations']==0,
 'data_only_unsafe':s['DATA_ONLY']['unsafe_acceptances']>0,
 'full_static_safe':s['FULL_STATIC']['unsafe_acceptances']==0,
 'full_static_overinvalidates':s['FULL_STATIC']['false_invalidations']>0,
 'global_more_overinvalidating':s['GLOBAL_EPOCH']['false_invalidations']>s['FULL_STATIC']['false_invalidations'],
 'both_branches':int(b['0'])==8 and int(b['1'])==8,
 'decision_pass':r['decision']=='PASS_TYPED_DYNAMIC_BRANCH_READSET_SCOPED'
}
out={'checks':checks,'pass':all(checks.values())}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
