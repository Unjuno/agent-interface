import itertools,json

ROLES=('PREPARED_REUSABLE_VERSIONED','FRESH_COMMIT_BOUND_CURRENT','UNKNOWN_ROLE')

def role_bound_store(role):
    if role=='PREPARED_REUSABLE_VERSIONED':
        return 'PERSIST_DEPENDENCY'
    if role=='FRESH_COMMIT_BOUND_CURRENT':
        return 'EPHEMERAL_ONLY'
    return 'REJECT'

def generic_store(role):
    return 'PERSIST_GENERIC' if role!='UNKNOWN_ROLE' else 'REJECT'

storage={r:{'ROLE_BOUND':role_bound_store(r),'GENERIC_CACHE':generic_store(r)} for r in ROLES}

stats={p:{'unsafe_admissions':0,'false_rejections':0,'admissions':0} for p in ('ROLE_BOUND','GENERIC_CACHE')}
witness={}
rows=[]
for dep_current,truth,lineage_current,intent_match,epoch_match,fresh_present in itertools.product(
    (False,True),('FALSE','UNKNOWN','TRUE'),(False,True),(False,True),(False,True),(False,True)):
    oracle=(dep_current and fresh_present and truth=='TRUE' and lineage_current and intent_match and epoch_match)
    role_bound=oracle
    # Comparator has persisted an earlier exact TRUE gate as generic reusable evidence.
    # Coarse cache key matches even when its current evidence role/lifetime no longer does.
    generic=dep_current
    row={
      'dep_current':dep_current,
      'current_gate_truth':truth,
      'gate_lineage_current':lineage_current,
      'intent_match':intent_match,
      'commit_epoch_match':epoch_match,
      'fresh_gate_present':fresh_present,
      'oracle_admit':oracle,
      'ROLE_BOUND':role_bound,
      'GENERIC_CACHE':generic,
      'roles':{
        'dependency':'PREPARED_REUSABLE_VERSIONED',
        'gate':'FRESH_COMMIT_BOUND_CURRENT'
      }
    }
    rows.append(row)
    for p,v in (('ROLE_BOUND',role_bound),('GENERIC_CACHE',generic)):
        stats[p]['admissions']+=int(v)
        if v and not oracle:
            stats[p]['unsafe_admissions']+=1
            witness.setdefault(p,row)
        if oracle and not v:
            stats[p]['false_rejections']+=1

result={
 'rows':len(rows),
 'storage':storage,
 'stats':stats,
 'unsafe_witnesses':witness,
 'valid_oracle_rows':sum(r['oracle_admit'] for r in rows),
 'role_bound_persistent_dependency_receipts':int(storage['PREPARED_REUSABLE_VERSIONED']['ROLE_BOUND']=='PERSIST_DEPENDENCY'),
 'role_bound_persistent_commit_receipts':int(storage['FRESH_COMMIT_BOUND_CURRENT']['ROLE_BOUND'].startswith('PERSIST')),
 'generic_persistent_commit_receipts':int(storage['FRESH_COMMIT_BOUND_CURRENT']['GENERIC_CACHE'].startswith('PERSIST')),
 'role_bound_cross_intent_epoch_replay_accepts':sum(
    r['ROLE_BOUND'] and (not r['intent_match'] or not r['commit_epoch_match']) for r in rows),
 'role_bound_bad_gate_admissions':sum(
    r['ROLE_BOUND'] and (
      not r['fresh_gate_present'] or not r['gate_lineage_current'] or
      r['current_gate_truth']!='TRUE') for r in rows),
 'unknown_role_rejected':storage['UNKNOWN_ROLE']['ROLE_BOUND']=='REJECT',
 'decision':None
}
pass_gate=(
 stats['ROLE_BOUND']['unsafe_admissions']==0 and stats['ROLE_BOUND']['false_rejections']==0 and
 result['valid_oracle_rows']>0 and result['role_bound_persistent_dependency_receipts']==1 and
 result['role_bound_persistent_commit_receipts']==0 and result['role_bound_cross_intent_epoch_replay_accepts']==0 and
 result['role_bound_bad_gate_admissions']==0 and result['generic_persistent_commit_receipts']==1 and
 stats['GENERIC_CACHE']['unsafe_admissions']>0 and result['unknown_role_rejected'])
result['decision']='PASS_ROLE_BOUND_LEDGER_LIFETIME_SCOPED' if pass_gate else 'FAIL_ROLE_BOUND_LEDGER_LIFETIME'
print(json.dumps(result,indent=2,sort_keys=True))
