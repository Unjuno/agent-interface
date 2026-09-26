"""Effective, well-formed copied-record mutations; original evidence untouched."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from audit import audit

root=Path(sys.argv[1]); original=root/'RECORDS.json'
base=json.loads(original.read_text())

def response_change(x,key,value):
    e=next(e for e in x['cases'][0]['io'] if json.loads(e['request_raw'])['op']=='apply')
    a=json.loads(e['response_raw']);a[key]=value
    e['response_raw']=json.dumps(a)+'\n'

mutations={
 'missing_case':lambda x:x['cases'].pop(),
 'duplicate_case':lambda x:x['cases'].__setitem__(1,copy.deepcopy(x['cases'][0])),
 'wrong_policy':lambda x:x['cases'][0].__setitem__('mode','MAX_SEEN'),
 'wrong_scope':lambda x:x['cases'][0].__setitem__('id','foreign'),
 'false_decision':lambda x:response_change(x,'status','WRONG_EPOCH'),
 'authority':lambda x:response_change(x,'authority_granted',True),
 'task_success':lambda x:response_change(x,'task_success',True),
 'exit':lambda x:x['cases'][0]['peers'][0].__setitem__('exit',23),
 'duplicate_pid':lambda x:x['cases'][0]['peers'][1].__setitem__('pid',x['cases'][0]['peers'][0]['pid']),
 'clock_order':lambda x:x['cases'][0]['io'][0].__setitem__('end_ns',0),
 'batch_exit':lambda x:x['batches'][0].__setitem__('returncode',7),
 'database_state':lambda x:x['cases'][0]['final_db'].__setitem__('resource.db',x['cases'][0]['initial_db']['resource.db'])}
results=[]
with tempfile.TemporaryDirectory() as temp:
    for name,fn in mutations.items():
        x=copy.deepcopy(base);fn(x)
        p=Path(temp)/'records.json';p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
        effective=x!=base
        a=audit(root,p)
        results.append({'name':name,'effective':effective,'rejected':bool(a['errors']),
                        'changed_sha256':a['records_sha256'],'errors':a['errors']})
output={'controls':results,'passed':all(r['effective'] and r['rejected'] for r in results)}
print(json.dumps(output,sort_keys=True,indent=2))
raise SystemExit(not output['passed'])
