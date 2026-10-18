import hashlib, json, pathlib, subprocess, sys
SRC=pathlib.Path('/src/audit_v3_candidate.py')
CASES=pathlib.Path('/cases')
OUT=pathlib.Path('/output')
SEED=5665002
EXPECTED={
 'base':'f497948e2d45e793b612b43265ef5b12d81479695a7b27cf7ba733e3d12573f2',
 'nonexchangeable':'355ee8008035a14f682b2c31fc2bf371b6b87f2164e02445257cac728e8b0163',
 'denominator':'267e94250180dfbd1ecdde3d5c0a3e7b92b3d3423d3cb53c9cb97066d2c3f3f0',
 'taxonomy':'10b5f39cd2c71fcecf38e9985fc7c0afd6fb27bced82e58850967ccfddab6be5',
 'duplicate-unit':'1bc272c1a0e6128215d437403fd50e22b443d8d1aa2c431d07c8c8de28417f35'}
DISPOSITIONS={'nonexchangeable':'HOLD_NONEXCHANGEABLE','denominator':'HOLD_NO_ELIGIBLE_DENOMINATOR','taxonomy':'HOLD_TAXONOMY_UNSTABLE','duplicate-unit':'HOLD_NONEXCHANGEABLE'}
def rows(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
def classify(r):
    if r.get('kind')!='iid': return 'NON_IID'
    if r.get('train_planned_n')!=len(r.get('train',[]))+r.get('train_unknown_n',0) or r.get('train_unknown_n')!=0: return 'HOLD_NO_ELIGIBLE_DENOMINATOR'
    if r.get('validation_planned_n')!=len(r.get('validation',[]))+r.get('validation_unknown_n',0) or r.get('validation_unknown_n')!=0: return 'HOLD_NO_ELIGIBLE_DENOMINATOR'
    if len(r.get('train_unit_ids',[]))!=len(r.get('train',[])) or len(set(r.get('train_unit_ids',[])))!=len(r.get('train_unit_ids',[])): return 'HOLD_NONEXCHANGEABLE'
    if len(r.get('validation_unit_ids',[]))!=len(r.get('validation',[])) or len(set(r.get('validation_unit_ids',[])))!=len(r.get('validation_unit_ids',[])): return 'HOLD_NONEXCHANGEABLE'
    if r.get('train_taxonomy')!=r.get('validation_taxonomy'): return 'HOLD_TAXONOMY_UNSTABLE'
    if r.get('train_stratum')!=r.get('validation_stratum'): return 'HOLD_NONEXCHANGEABLE'
    return 'ELIGIBLE_IID'
def oracle_eligible(rs): return sum(classify(r)=='ELIGIBLE_IID' for r in rs)
def verify_inputs():
    names=('base','nonexchangeable','denominator','taxonomy','duplicate-unit')
    allrows={name:rows(CASES/f'{name}.jsonl') for name in names}
    base=allrows['base']; assert len(base)==204 and oracle_eligible(base)==200
    target_index=next(i for i,r in enumerate(base) if r.get('seed')==SEED)
    assert base[target_index].get('case_id')=='iid-001'
    results={}
    for name,rs in allrows.items():
        path=CASES/f'{name}.jsonl'; digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest==EXPECTED[name],(name,digest,EXPECTED[name])
        assert len(rs)==204 and sum(r.get('kind')=='iid' for r in rs)==200
        if name!='base':
            diffs=[i for i,(a,b) in enumerate(zip(base,rs)) if a!=b]
            assert diffs==[target_index],(name,diffs)
            target=rs[target_index]
            assert target.get('candidate',{}).get('disposition')==DISPOSITIONS[name]
            assert classify(target)==DISPOSITIONS[name]
            if name=='nonexchangeable': assert target.get('validation_stratum')!=target.get('train_stratum')
            if name=='denominator': assert target.get('validation_unknown_n')>0 and target.get('validation_planned_n')!=len(target.get('validation',[]))+target.get('validation_unknown_n',0)
            if name=='taxonomy': assert target.get('validation_taxonomy')!=target.get('train_taxonomy')
            if name=='duplicate-unit': assert len(set(target.get('validation_unit_ids',[])))<len(target.get('validation_unit_ids',[]))
        assert oracle_eligible(rs)==(200 if name=='base' else 199)
        results[name]={'sha256':digest,'scheduled_iid':200,'independent_eligible_iid':oracle_eligible(rs)}
    compile(SRC.read_text(encoding='utf-8'),str(SRC),'exec')
    assert OUT.is_dir()
    probe=OUT/'.write-probe'; probe.write_text('ok',encoding='utf-8'); probe.unlink()
    return results
def formal():
    audit_runs=[]
    for name in ('base','nonexchangeable','denominator','taxonomy','duplicate-unit'):
        path=CASES/f'{name}.jsonl'
        p=subprocess.run([sys.executable,'-B',str(SRC),str(path)],capture_output=True,text=True)
        try: parsed=json.loads(p.stdout)
        except Exception: parsed=None
        (OUT/f'{name}.stdout.txt').write_text(p.stdout,encoding='utf-8')
        (OUT/f'{name}.stderr.txt').write_text(p.stderr,encoding='utf-8')
        rs=rows(path)
        audit_runs.append({'name':name,'exit_code':p.returncode,'parsed':parsed,'oracle_eligible_iid':oracle_eligible(rs),'stdout_sha256':hashlib.sha256(p.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr.encode()).hexdigest()})
    expected={'base':0,'nonexchangeable':1,'denominator':1,'taxonomy':1,'duplicate-unit':1}; checks=[]
    for r in audit_runs:
        p=r['parsed']; name=r['name']; target=next(x for x in rows(CASES/f'{name}.jsonl') if x.get('seed')==SEED)
        expected_disposition=classify(target)
        ok=(p is not None and r['exit_code']==expected[name] and p.get('audit')==('PASS' if name=='base' else 'FAIL') and p.get('scheduled_iid_rows')==200 and p.get('eligible_iid_rows')==r['oracle_eligible_iid'] and p.get('decision',{}).get('iid_replicates')==r['oracle_eligible_iid'] and p.get('decision',{}).get('method_controls_pass')==(name=='base'))
        if name=='base': ok=ok and expected_disposition=='ELIGIBLE_IID' and len(p.get('errors',[]))==0 and all(p.get('mutation_controls',{}).values())
        else: ok=ok and p.get('errors',[]).count('iid_eligibility_count:199')==1 and expected_disposition==DISPOSITIONS[name]
        checks.append({'case':name,'expected_disposition':expected_disposition,'passed':bool(ok)})
    result={'status':'PASS_CORRECTED_GATE' if all(c['passed'] for c in checks) else 'FAIL_CORRECTED_GATE','formal_audit_invocations':5,'retries':0,'checks':checks,'runs':audit_runs}
    (OUT/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,sort_keys=True))
    return 0 if result['status']=='PASS_CORRECTED_GATE' else 1
if __name__=='__main__':
    if sys.argv[1:]==['--validate-inputs']:
        print(json.dumps({'status':'PREFLIGHT_PASS','audit_source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'cases':verify_inputs(),'target_audit_invocations':0},sort_keys=True))
        raise SystemExit(0)
    raise SystemExit(formal())
