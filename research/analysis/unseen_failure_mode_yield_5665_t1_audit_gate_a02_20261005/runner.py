import hashlib, json, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
SRC=ROOT/'src'/'audit.py'
IN=ROOT/'input'
EXPECTED={'base':'f497948e2d45e793b612b43265ef5b12d81479695a7b27cf7ba733e3d12573f2','mutated':'355ee8008035a14f682b2c31fc2bf371b6b87f2164e02445257cac728e8b0163'}

def load_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]

def eligible(rows):
    return sum(1 for r in rows if r.get('kind')=='iid' and r.get('train_stratum')==r.get('validation_stratum') and r.get('train_taxonomy')==r.get('validation_taxonomy') and r.get('train_unknown_n')==0 and r.get('validation_unknown_n')==0 and len(r.get('train_unit_ids',[]))==len(r.get('train',[])) and len(set(r.get('train_unit_ids',[])))==len(r.get('train_unit_ids',[])) and len(r.get('validation_unit_ids',[]))==len(r.get('validation',[])) and len(set(r.get('validation_unit_ids',[])))==len(r.get('validation_unit_ids',[])))

def verify():
    a,b=load_rows(IN/'base.jsonl'),load_rows(IN/'mutated.jsonl')
    assert len(a)==len(b)==204
    assert sum(r.get('kind')=='iid' for r in a)==200
    diffs=[(x,y) for x,y in zip(a,b) if x!=y]
    assert len(diffs)==1
    old,new=diffs[0]
    assert old.get('case_id')=='iid-001' and old.get('seed')==5665002
    assert new.get('case_id')==old.get('case_id') and new.get('seed')==old.get('seed')
    assert new.get('validation_stratum')=='mutation-shifted-validation-stratum'
    assert new.get('candidate',{}).get('disposition')=='HOLD_NONEXCHANGEABLE'
    assert eligible(a)==200 and eligible(b)==199
    for name,expected in EXPECTED.items():
        assert hashlib.sha256((IN/f'{name}.jsonl').read_bytes()).hexdigest()==expected
    return {'status':'PREFLIGHT_PASS','target_audit_invocations':0,'rows':204,'mutation_records':1,'baseline_eligible':eligible(a),'mutated_eligible':eligible(b),'inputs':EXPECTED,'audit_source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest()}

def formal():
    out=pathlib.Path('/output')
    assert out.is_dir() and out.stat().st_mode & 0o222
    results=[]
    for name in ('base','mutated'):
        data=IN/f'{name}.jsonl'
        p=subprocess.run([sys.executable,'-B',str(SRC),str(data)],capture_output=True,text=True)
        (out/f'{name}.stdout.txt').write_text(p.stdout,encoding='utf-8')
        (out/f'{name}.stderr.txt').write_text(p.stderr,encoding='utf-8')
        try: parsed=json.loads(p.stdout)
        except Exception: parsed=None
        rows=load_rows(data)
        results.append({'name':name,'exit_code':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr.encode()).hexdigest(),'parsed':parsed,'oracle_eligible_iid_rows':eligible(rows)})
    base,mut=results
    reproduced=(base['exit_code']==0 and mut['exit_code']==0 and isinstance(base['parsed'],dict) and isinstance(mut['parsed'],dict) and base['parsed'].get('audit')=='PASS' and mut['parsed'].get('audit')=='PASS' and base['parsed'].get('eligible_iid_rows')==200 and mut['parsed'].get('eligible_iid_rows')==200 and mut['oracle_eligible_iid_rows']==199 and mut['parsed'].get('decision',{}).get('iid_replicates')==199)
    result={'status':'DEFECT_REPRODUCED' if reproduced else 'DEFECT_NOT_REPRODUCED','formal_invocations':2,'retries':0,'runs':results}
    (out/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__':
    if sys.argv[1:] == ['--validate-inputs']:
        print(json.dumps(verify(),sort_keys=True))
    else:
        formal()

