import itertools, json
RES=('g','a','b','u')
POLICIES=('DYNAMIC_TYPED','DATA_ONLY','FULL_STATIC','GLOBAL_EPOCH')
rows=[]
summary={p:{'unsafe_acceptances':0,'false_invalidations':0,'accepted':0,'invalidated':0} for p in POLICIES}
exact_dynamic=0
branch_counts={0:0,1:0}

for vals in itertools.product((0,1), repeat=4):
    state=dict(zip(RES,vals))
    g=state['g']; branch_counts[g]+=1
    executed='a' if g else 'b'
    ground=frozenset({'g',executed})
    traces={
      'DYNAMIC_TYPED':frozenset({'g',executed}),
      'DATA_ONLY':frozenset({executed}),
      'FULL_STATIC':frozenset({'g','a','b'}),
      'GLOBAL_EPOCH':frozenset({'g','a','b','u'}),
    }
    if traces['DYNAMIC_TYPED']==ground: exact_dynamic+=1
    for mutated in RES:
        for p in POLICIES:
            invalidates=mutated in traces[p]
            required=mutated in ground
            if invalidates: summary[p]['invalidated']+=1
            else: summary[p]['accepted']+=1
            if required and not invalidates: summary[p]['unsafe_acceptances']+=1
            if (not required) and invalidates: summary[p]['false_invalidations']+=1
        rows.append({'state':state,'executed':executed,'ground':sorted(ground),'mutated':mutated})

result={
 'states':16,
 'mutation_cases':len(rows),
 'branch_counts':branch_counts,
 'dynamic_exact_set_states':exact_dynamic,
 'summary':summary,
 'decision':None
}
pass_gate=(exact_dynamic==16 and summary['DYNAMIC_TYPED']['unsafe_acceptances']==0 and
           summary['DYNAMIC_TYPED']['false_invalidations']==0 and
           summary['DATA_ONLY']['unsafe_acceptances']>0 and
           summary['FULL_STATIC']['unsafe_acceptances']==0 and
           summary['FULL_STATIC']['false_invalidations']>0 and
           summary['GLOBAL_EPOCH']['false_invalidations']>summary['FULL_STATIC']['false_invalidations'] and
           branch_counts[0]>0 and branch_counts[1]>0)
result['decision']='PASS_TYPED_DYNAMIC_BRANCH_READSET_SCOPED' if pass_gate else 'FAIL_TYPED_DYNAMIC_BRANCH_READSET'
print(json.dumps(result,indent=2,sort_keys=True))
