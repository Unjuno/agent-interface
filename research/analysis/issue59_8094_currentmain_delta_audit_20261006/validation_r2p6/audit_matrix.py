"""Independent raw-record audit. Imports neither candidate nor driver/fixture."""
import hashlib
import itertools
import json
from pathlib import Path
import sys

NAMES = ('valid','row_order','compact_json','main_sha_changed','candidate_equals_main',
         'classification_changed','addition_gets_base','drop_row','duplicate_replace',
         'modified_candidate_null','invalid_class','forged_equal_base_main',
         'candidate_ref_is_main','main_ref_is_candidate','source_commit_missing',
         'unknown_path','bool_count_alias','wrong_decision','duplicate_json_key','malformed_sha')

def audit(root):
    errors = []
    out = root/'matrix'
    rows = json.loads((out/'records.json').read_bytes())
    cases = json.loads((out/'CASES.json').read_bytes())
    freeze = json.loads((root/'FREEZE.json').read_bytes())
    checks = 0
    def ck(cond,message):
        nonlocal checks
        checks += 1
        if not cond:errors.append(message)
    def sha(b):return hashlib.sha256(b).hexdigest()
    for p,h in freeze['sha256'].items():ck(sha((root/p).read_bytes())==h,'source:'+p)
    ck(tuple(x['name'] for x in cases)==NAMES,'case membership')
    inputs={x['name']:x['input'].encode() for x in cases}
    for i,c in enumerate(cases):ck(c['expected_accept'] is (i<3),'case expected label')
    want=set(itertools.product(NAMES,('v1','v2'),(False,True)))
    got=[(r['case'],r['version'],r['optimized']) for r in rows]
    ck(len(got)==80 and set(got)==want and len(set(got))==80,'complete unique denominator')
    summary={v+'_'+m:dict(cases=0,positive_accept=0,negative_reject=0,false_accept=0,false_reject=0)
             for v in ('v1','v2') for m in ('normal','optimized')}
    for r in rows:
        folder=out/r['name']; label=r['name']; positive=r['case'] in NAMES[:3]
        expected_source='original/verify.py' if r['version']=='v1' else 'verify_v2.py'
        payload=(folder/'RESULT.json').read_bytes(); stdout=(folder/'stdout.txt').read_bytes();stderr=(folder/'stderr.txt').read_bytes()
        ck(payload==inputs[r['case']] and sha(payload)==r['input_sha256'],label+':input')
        ck(sha((folder/'subject.py').read_bytes())==freeze['sha256'][expected_source]==r['source_sha256'],label+':subject')
        ck(sha(stdout)==r['stdout_sha256'] and sha(stderr)==r['stderr_sha256'],label+':streams')
        ck(json.loads((folder/'execution.json').read_bytes())==r,label+':receipt copy')
        ck(type(r['returncode']) is int and r['returncode'] in (0,1,2) and r['timeout'] is False,label+':actual exit')
        ck(type(r['pid']) is int and r['pid']>0 and r['finished_wall_ns']>=r['started_wall_ns'],label+':process')
        ck(('-O' in r['argv']) is r['optimized'],label+':optimization')
        accepted=r['returncode']==0
        s=summary[r['version']+'_'+('optimized' if r['optimized'] else 'normal')];s['cases']+=1
        if positive:s['positive_accept' if accepted else 'false_reject']+=1
        else:s['false_accept' if accepted else 'negative_reject']+=1
        if r['version']=='v2':
            ck(accepted is positive,label+':v2 truth')
            result=json.loads(stdout)
            expected='PASS_SOURCE_TABLE_VERIFIED' if positive else ('HOLD_SOURCE_OBJECTS_OR_IO_UNAVAILABLE' if r['case']=='source_commit_missing' else 'REJECT_SOURCE_TABLE')
            ck(result['status']==expected and not stderr,label+':v2 disposition')
            if positive:
                ck(result['counts']==dict(total=11,clean_add=3,main_unchanged_candidate_only=8,conflicts=0),label+':counts')
                ck(result['grants_input_authority'] is False and result['runtime_compatibility_verified'] is False,label+':limits')
        elif accepted:ck(stdout.startswith(b'PASS 11 paths:') and not stderr,label+':v1 pass stream')
    ck(json.loads((out/'END.json').read_bytes())==dict(records=80,source_unchanged=True,returncode=0),'outer completion')
    return dict(scope='SYNTHETIC_GIT_ENGINEERING_ONLY',checks=checks,errors=errors,summary=summary)

if __name__=='__main__':
    result=audit(Path(sys.argv[1]).resolve())
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(1 if result['errors'] else 0)
