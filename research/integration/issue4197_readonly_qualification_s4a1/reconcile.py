"""Independent data-only receipt check; imports neither old nor new runner."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()


def check(root, case_file):
    result=json.loads((root/'RESULT.json').read_bytes())
    cases=json.loads(case_file.read_bytes())
    original_bytes=(root/'original.json').read_bytes()
    original=json.loads(original_bytes)
    errors=[]
    count=0
    def require(condition,label):
        nonlocal count
        count+=1
        if not condition:
            errors.append(label)
    require(sha(original_bytes)=='b67790414851ebbe0ed82cb835eefc03b884ac89190d6d39040f004b416dd193','original digest')
    rows=result['auditor_cases']
    require([r['name'] for r in rows]==['original']+[c['name'] for c in cases],'case order')
    require(len(rows)==13,'denominator')
    accepted=[]
    for index,row in enumerate(rows):
        name=row['name'];folder=root/name
        data=(folder/'input.json').read_bytes()
        expected=original_bytes
        if index:
            spec=cases[index-1]; obj=copy.deepcopy(original); cursor=obj
            for part in spec['path'][:-1]:
                cursor=cursor[part]
            cursor[spec['path'][-1]]=spec['value']
            expected=canonical(obj)
            require(data!=canonical(original),'effective change:'+name)
            require(canonical({'path':row['path'],'value':row['value']})==canonical({'path':spec['path'],'value':spec['value']}),'definition:'+name)
        require(data==expected,'full input:'+name)
        require(sha(data)==row['input_sha256'],'input hash:'+name)
        stdout=(folder/'stdout').read_bytes();stderr=(folder/'stderr').read_bytes()
        require(sha(stdout)==row['stdout_sha256'],'stdout hash:'+name)
        require(sha(stderr)==row['stderr_sha256'],'stderr hash:'+name)
        parsed=json.loads(stdout)
        require(canonical(parsed)==canonical(row['result']),'stdout/result:'+name)
        require(stderr==b'','stderr empty:'+name)
        require(type(row['exit_code']) is int,'exit type:'+name)
        require(type(row['pid']) is int and row['pid']>0,'pid:'+name)
        require(row['exit_code']==(0 if parsed['errors']==[] else 1),'exit/error consistency:'+name)
        require(parsed['decision']==('PASS_LIFECYCLE_BOUND_NATIVE_ADMISSION_SCOPED' if not parsed['errors'] else 'FAIL_AUDIT'),'decision/error consistency:'+name)
        if index and row['exit_code']==0 and not parsed['errors']:
            accepted.append(name)
    require(rows[0]['exit_code']==0,'original baseline')
    require(accepted==result['accepted_inconsistent_derivatives'],'accepted list')
    controls=result['original_controls']; out=(root/'controls.stdout').read_bytes();err=(root/'controls.stderr').read_bytes()
    require(sha(out)==controls['stdout_sha256'] and sha(err)==controls['stderr_sha256'],'controls hashes')
    require(canonical(json.loads(out))==canonical(controls['result']),'controls stdout')
    require(controls['exit_code']==0 and err==b'','controls exit')
    require(controls['result']['rejected']==10 and controls['result']['total']==10,'original control count')
    require(result['native_runs']==0 and result['model_calls']==0 and result['historical_result_changed'] is False,'scope')
    return {'integrity':'PASS_READONLY_RECEIPTS' if not errors else 'FAIL_READONLY_RECEIPTS',
            'checks':count,'errors':errors,'auditor_cases':len(rows),
            'accepted_inconsistent_derivatives':len(accepted),'historical_native_runs':0}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('result_dir',type=Path);parser.add_argument('--cases',type=Path,default=Path(__file__).with_name('CASES.json'))
    args=parser.parse_args();r=check(args.result_dir,args.cases)
    print(json.dumps(r,indent=2,sort_keys=True))
    raise SystemExit(0 if not r['errors'] else 1)
