import itertools,json
POLICIES=('DYNAMIC_QUERY','MEMBER_ONLY','QUERY_ONLY','STATIC_SCOPE','GLOBAL_EPOCH')
summary={p:{'unsafe_acceptances':0,'false_invalidations':0,'accepted':0,'invalidated':0} for p in POLICIES}
exact=0; mutation_cases=0; membership_shapes={'empty':0,'partial':0,'full':0}
for mA,mB,vA,vB,u in itertools.product((0,1), repeat=5):
    present={x for x,m in [('A',mA),('B',mB)] if m}
    shape='empty' if not present else ('full' if len(present)==2 else 'partial')
    membership_shapes[shape]+=1
    ground=frozenset({'query'} | {f'value_{x}' for x in present})
    traces={
      'DYNAMIC_QUERY':ground,
      'MEMBER_ONLY':frozenset({f'value_{x}' for x in present}),
      'QUERY_ONLY':frozenset({'query'}),
      'STATIC_SCOPE':frozenset({'query','value_A','value_B'}),
      'GLOBAL_EPOCH':frozenset({'query','value_A','value_B','u'}),
    }
    if traces['DYNAMIC_QUERY']==ground: exact+=1
    mutations=[('membership_A','query'),('membership_B','query'),('value_A','value_A'),('value_B','value_B'),('u','u')]
    for name,res in mutations:
      mutation_cases+=1
      for p in POLICIES:
        invalidates=res in traces[p]; required=res in ground
        summary[p]['invalidated']+=int(invalidates); summary[p]['accepted']+=int(not invalidates)
        summary[p]['unsafe_acceptances']+=int(required and not invalidates)
        summary[p]['false_invalidations']+=int((not required) and invalidates)
result={'states':32,'mutation_cases':mutation_cases,'membership_shapes':membership_shapes,'dynamic_exact_set_states':exact,'summary':summary,'decision':None}
pass_gate=(exact==32 and summary['DYNAMIC_QUERY']['unsafe_acceptances']==0 and summary['DYNAMIC_QUERY']['false_invalidations']==0 and
 summary['MEMBER_ONLY']['unsafe_acceptances']>0 and summary['QUERY_ONLY']['unsafe_acceptances']>0 and
 summary['STATIC_SCOPE']['unsafe_acceptances']==0 and summary['STATIC_SCOPE']['false_invalidations']>0 and
 summary['GLOBAL_EPOCH']['false_invalidations']>summary['STATIC_SCOPE']['false_invalidations'] and
 all(membership_shapes[k]>0 for k in ('empty','partial','full')))
result['decision']='PASS_TYPED_QUERY_DEPENDENCY_SCOPED' if pass_gate else 'FAIL_TYPED_QUERY_DEPENDENCY'
print(json.dumps(result,indent=2,sort_keys=True))
