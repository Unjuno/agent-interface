import itertools, json
TARGETS=('A','B')
RES=('mapping','A','B','u')
POLICIES=('DYNAMIC_RESOLVE','CONCRETE_ONLY','ALIAS_ONLY','STATIC_BOTH','GLOBAL_EPOCH')
summary={p:{'unsafe_acceptances':0,'false_invalidations':0,'accepted':0,'invalidated':0} for p in POLICIES}
exact=0
target_counts={'A':0,'B':0}
mutation_cases=0

for target in TARGETS:
  for vals in itertools.product((0,1), repeat=3):
    state=dict(zip(('A','B','u'), vals)); target_counts[target]+=1
    ground=frozenset({'mapping',target})
    traces={
      'DYNAMIC_RESOLVE':frozenset({'mapping',target}),
      'CONCRETE_ONLY':frozenset({target}),
      'ALIAS_ONLY':frozenset({'mapping'}),
      'STATIC_BOTH':frozenset({'mapping','A','B'}),
      'GLOBAL_EPOCH':frozenset({'mapping','A','B','u'}),
    }
    if traces['DYNAMIC_RESOLVE']==ground: exact+=1
    for mutated in RES:
      mutation_cases+=1
      for p in POLICIES:
        invalidates=mutated in traces[p]
        required=mutated in ground
        summary[p]['invalidated']+=int(invalidates)
        summary[p]['accepted']+=int(not invalidates)
        summary[p]['unsafe_acceptances']+=int(required and not invalidates)
        summary[p]['false_invalidations']+=int((not required) and invalidates)

result={'states':16,'mutation_cases':mutation_cases,'target_counts':target_counts,'dynamic_exact_set_states':exact,'summary':summary,'decision':None}
pass_gate=(exact==16 and summary['DYNAMIC_RESOLVE']['unsafe_acceptances']==0 and summary['DYNAMIC_RESOLVE']['false_invalidations']==0 and
 summary['CONCRETE_ONLY']['unsafe_acceptances']>0 and summary['ALIAS_ONLY']['unsafe_acceptances']>0 and
 summary['STATIC_BOTH']['unsafe_acceptances']==0 and summary['STATIC_BOTH']['false_invalidations']>0 and
 summary['GLOBAL_EPOCH']['false_invalidations']>summary['STATIC_BOTH']['false_invalidations'] and target_counts['A']==8 and target_counts['B']==8)
result['decision']='PASS_TYPED_RESOLVE_DEPENDENCY_SCOPED' if pass_gate else 'FAIL_TYPED_RESOLVE_DEPENDENCY'
print(json.dumps(result,indent=2,sort_keys=True))
