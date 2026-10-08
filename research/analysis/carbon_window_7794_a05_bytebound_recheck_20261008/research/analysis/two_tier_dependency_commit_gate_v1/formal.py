import itertools,json
POLICIES=('TWO_TIER','DEP_ONLY','GATE_ONLY','CACHED_GATE','SCALAR_ALL_CURRENT')
stats={p:{'unsafe_admissions':0,'false_rejections':0,'admissions':0} for p in POLICIES}
witness={}
rows=[]
for dep_current,gate_truth,gate_lineage_current,cached_prepare_gate in itertools.product(
    (False,True),('FALSE','UNKNOWN','TRUE'),(False,True),(False,True)):
    oracle=dep_current and gate_lineage_current and gate_truth=='TRUE'
    pred={
      'TWO_TIER':oracle,
      'DEP_ONLY':dep_current,
      'GATE_ONLY':gate_lineage_current and gate_truth=='TRUE',
      'CACHED_GATE':dep_current and cached_prepare_gate,
      'SCALAR_ALL_CURRENT':dep_current and gate_lineage_current and gate_truth=='TRUE' and cached_prepare_gate,
    }
    row={
      'roles':{
        'dependency':'PREPARED_REUSABLE_VERSIONED',
        'gate':'FRESH_COMMIT_BOUND_CURRENT'
      },
      'dep_current':dep_current,
      'gate_truth':gate_truth,
      'gate_lineage_current':gate_lineage_current,
      'cached_prepare_gate':cached_prepare_gate,
      'oracle_admit':oracle,
      'predictions':pred
    }
    rows.append(row)
    for p,v in pred.items():
        stats[p]['admissions']+=int(v)
        if v and not oracle:
            stats[p]['unsafe_admissions']+=1
            witness.setdefault(p,row)
        if oracle and not v:
            stats[p]['false_rejections']+=1

result={
 'rows':len(rows),
 'stats':stats,
 'unsafe_witnesses':witness,
 'valid_oracle_rows':sum(r['oracle_admit'] for r in rows),
 'two_tier_bad_gate_admissions':sum(
    r['predictions']['TWO_TIER'] and
    (not r['gate_lineage_current'] or r['gate_truth']!='TRUE')
    for r in rows),
 'role_labels':['PREPARED_REUSABLE_VERSIONED','FRESH_COMMIT_BOUND_CURRENT'],
 'decision':None
}
pass_gate=(
 stats['TWO_TIER']['unsafe_admissions']==0 and stats['TWO_TIER']['false_rejections']==0 and
 stats['DEP_ONLY']['unsafe_admissions']>0 and stats['GATE_ONLY']['unsafe_admissions']>0 and
 stats['CACHED_GATE']['unsafe_admissions']>0 and result['valid_oracle_rows']>0 and
 result['two_tier_bad_gate_admissions']==0 and
 stats['SCALAR_ALL_CURRENT']['unsafe_admissions']==0 and stats['SCALAR_ALL_CURRENT']['false_rejections']>0
)
result['decision']='PASS_TWO_TIER_DEPENDENCY_COMMIT_GATE_SCOPED' if pass_gate else 'FAIL_TWO_TIER_DEPENDENCY_COMMIT_GATE'
print(json.dumps(result,indent=2,sort_keys=True))
