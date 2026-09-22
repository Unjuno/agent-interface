import argparse, hashlib, json, pathlib, sqlite3, sys
POLICIES=('STALE_METADATA','LIFETIME_UNION','SCHEMA_SCOPED_REPLACE')
SCENARIOS=(
'STABLE_A_NONE','RETARGET_B_NONE','RETARGET_B_MUTATE_B','RETARGET_B_MUTATE_A',
'UNRELATED_SCHEMA_A_MUTATE_A','UNRELATED_SCHEMA_A_MUTATE_B',
'RETARGET_B_EXECUTE_BACK_A_MUTATE_B','RETARGET_B_EXECUTE_BACK_A_MUTATE_A')

def target_for(s):
    return 'a' if s.startswith('STABLE_A_') or s.startswith('UNRELATED_SCHEMA_A_') or s.startswith('RETARGET_B_EXECUTE_BACK_A_') else 'b'
def mutation_for(s):
    if s.endswith('_MUTATE_A'): return 'a'
    if s.endswith('_MUTATE_B'): return 'b'
    return None

def audit(root):
    root=pathlib.Path(root); raw=json.loads((root/'RAW.json').read_text()); errors=[]
    freeze_path=root/'source_snapshot'/'FREEZE.json'
    try:
        freeze=json.loads(freeze_path.read_text())
        for name,expected_hash in freeze.get('sources',{}).items():
            p=root/'source_snapshot'/name
            if not p.is_file(): errors.append(['source_missing',name]); continue
            actual=hashlib.sha256(p.read_bytes()).hexdigest()
            if actual!=expected_hash: errors.append(['source_hash',name,actual,expected_hash])
    except Exception as e:
        errors.append(['freeze_read',str(e)])
    expected={(p,s,r) for r in range(2) for s in SCENARIOS for p in POLICIES}
    got=set(); summary={p:{'cases':0,'missing_dependency_cases':0,'extra_dependency_cases':0,'unsafe_acceptances':0,'false_invalidations':0,'decision_errors':0} for p in POLICIES}
    for row in raw.get('rows',[]):
        key=(row.get('policy'),row.get('scenario'),row.get('rep'))
        if key in got: errors.append(['duplicate_key',key])
        got.add(key)
        p,s,r=key
        if key not in expected: errors.append(['unexpected_key',key]); continue
        cid=row.get('case_id'); cdir=root/cid
        try: ex=json.loads((cdir/'EXIT.json').read_text())
        except Exception as e: errors.append(['missing_exit',cid,str(e)]); continue
        if type(ex.get('returncode')) is not int or ex['returncode']!=0: errors.append(['bad_exit',cid,ex.get('returncode')])
        try: saved=json.loads((cdir/'CASE.json').read_text())
        except Exception as e: errors.append(['missing_case_json',cid,str(e)]); continue
        for k in saved:
            if row.get(k)!=saved[k]: errors.append(['raw_case_mismatch',cid,k]); break
        target=target_for(s); mutation=mutation_for(s); deps=set(row.get('deps',[])); accepted=row.get('accepted') is True
        if row.get('target')!=target: errors.append(['target',cid,row.get('target'),target])
        if row.get('mutation')!=mutation: errors.append(['mutation',cid,row.get('mutation'),mutation])
        missing=target not in deps; extra=bool(deps-{target}); should_accept=(mutation!=target)
        unsafe=accepted and not should_accept; false=(not accepted) and should_accept
        sm=summary[p]; sm['cases']+=1; sm['missing_dependency_cases']+=int(missing); sm['extra_dependency_cases']+=int(extra); sm['unsafe_acceptances']+=int(unsafe); sm['false_invalidations']+=int(false)
        expected_decision=not any(row['current_revisions_at_validation'].get(d)!=row['prepared_revisions'].get(d) for d in deps)
        if accepted!=expected_decision: errors.append(['validation_decision',cid,accepted,expected_decision]); sm['decision_errors']+=1
        db=sqlite3.connect(cdir/'case.db'); effects=db.execute('select value,policy,scenario,rep from effects order by id').fetchall(); vals={t:db.execute(f'select value,revision from {t}').fetchone() for t in ('a','b')}; db.close()
        if len(effects)!=(1 if accepted else 0): errors.append(['effect_count',cid,len(effects),accepted])
        if effects and tuple(effects[0])!=(row['prepared']['value'],p,s,r): errors.append(['effect_payload',cid,effects[0]])
        for t in ('a','b'):
            exp_rev=2 if mutation==t else 1
            if int(vals[t][1])!=exp_rev: errors.append(['final_revision',cid,t,vals[t][1],exp_rev])
        final_reads={e['table'] for e in row.get('authorizer_events',[]) if e.get('phase')=='final_prepare' and e.get('table') in ('a','b')}
        schema_changed=row['prepared']['schema_version']!=row['initial']['schema_version']
        if schema_changed and final_reads!={target}: errors.append(['final_callback_set',cid,sorted(final_reads),target])
    if got!=expected: errors.append(['denominator',len(got),len(expected),sorted(map(str,expected-got))[:3]])
    gates={
      'raw_case_count_48':raw.get('case_count')==48 and len(raw.get('rows',[]))==48,
      'stale_missing':summary['STALE_METADATA']['missing_dependency_cases']>0,
      'stale_unsafe':summary['STALE_METADATA']['unsafe_acceptances']>0,
      'stale_false':summary['STALE_METADATA']['false_invalidations']>0,
      'union_no_unsafe':summary['LIFETIME_UNION']['unsafe_acceptances']==0,
      'union_no_missing':summary['LIFETIME_UNION']['missing_dependency_cases']==0,
      'union_extra':summary['LIFETIME_UNION']['extra_dependency_cases']>0,
      'union_false':summary['LIFETIME_UNION']['false_invalidations']>0,
      'replace_exact':summary['SCHEMA_SCOPED_REPLACE']['missing_dependency_cases']==0 and summary['SCHEMA_SCOPED_REPLACE']['extra_dependency_cases']==0,
      'replace_safe_minimal':summary['SCHEMA_SCOPED_REPLACE']['unsafe_acceptances']==0 and summary['SCHEMA_SCOPED_REPLACE']['false_invalidations']==0,
      'all_policy_counts':all(summary[p]['cases']==16 for p in POLICIES),
      'formal_budget':raw.get('formal_invocations')==1 and raw.get('reruns')==0 and raw.get('replacements')==0 and raw.get('tuning')==0,
    }
    passed=not errors and all(gates.values())
    out={'decision':'PASS_SCHEMA_SCOPED_SQL_DEPENDENCY_REPLACE_SCOPED' if passed else 'FAIL_OR_HOLD','pass':passed,'summary':summary,'gates':gates,'errors':errors}
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if passed else 1
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('root'); sys.exit(audit(ap.parse_args().root))
