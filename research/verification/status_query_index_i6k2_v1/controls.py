"""Well-formed, effective evidence-copy mutations. Never reruns a benchmark."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import audit

NAMES=('query_boolean_count','wrong_value_claim','negative_duration','readonly_change',
       'unique_index','wrong_request','source_identity','nonzero_exit',
       'missing_timing_sample','duplicate_record_promoted')

def changed(records,name):
    rows=copy.deepcopy(records)
    def edit(index,fn):
        o=json.loads(base64.b64decode(rows[index]['stdout_b64']))
        fn(o)
        raw=audit.b(o)+b'\n'
        rows[index]['stdout_b64']=base64.b64encode(raw).decode()
        rows[index]['stdout_sha256']=hashlib.sha256(raw).hexdigest()
    objs=[json.loads(base64.b64decode(r['stdout_b64'])) for r in rows]
    p=next(i for i,o in enumerate(objs) if o['kind']=='performance')
    ix=next(i for i,o in enumerate(objs) if o['kind']=='performance' and o['arm']=='INDEXED')
    c=next(i for i,o in enumerate(objs) if o['kind']=='contracts' and o['arm']=='INDEXED')
    if name=='query_boolean_count':edit(p,lambda o:o['samples'][0]['result'].__setitem__('request_commit_count',True))
    elif name=='wrong_value_claim':edit(p,lambda o:o['samples'][0]['result'].__setitem__('current_value_matches',True))
    elif name=='negative_duration':edit(p,lambda o:o['samples'][0]['wall'].__setitem__(1,o['samples'][0]['wall'][0]-1))
    elif name=='readonly_change':edit(p,lambda o:o.__setitem__('db_sha_after_queries','0'*64))
    elif name=='unique_index':edit(ix,lambda o:o['index_list'][0].__setitem__(2,1))
    elif name=='wrong_request':edit(p,lambda o:o['requests'][0].__setitem__('revision',True))
    elif name=='source_identity':edit(p,lambda o:o['source_ids'].__setitem__('query.py','0'*64))
    elif name=='nonzero_exit':rows[p]['exit']=True
    elif name=='missing_timing_sample':edit(p,lambda o:o['samples'].pop())
    elif name=='duplicate_record_promoted':
        def change(o):
            z=next(z for z in o['cases'] if z['name']=='duplicate_commit')
            z['result'].update(outcome='APPLIED_ONCE',stored_status='APPLIED',request_commit_count=1)
        edit(c,change)
    else:raise ValueError(name)
    return rows

def run(records,complete=True):
    initial=audit.analyze(records,complete=complete)
    if initial['errors'] or initial['unexpected_errors']:raise ValueError('intact baseline fails')
    baseline=audit.h(audit.b(records));results=[]
    for name in NAMES:
        rows=changed(records,name);digest=audit.h(audit.b(rows));a=audit.analyze(rows,complete=complete)
        results.append(dict(name=name,changed=digest!=baseline,before_sha256=baseline,
                            after_sha256=digest,rejected=bool(a['errors']) and not a['unexpected_errors'],
                            errors=a['errors'],unexpected_errors=a['unexpected_errors']))
    return dict(total=len(results),effective_rejected=sum(r['changed'] and r['rejected'] for r in results),results=results)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    r=run(audit.load(a.directory))
    with a.out.open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(dict(total=r['total'],effective_rejected=r['effective_rejected'])))
    raise SystemExit(0 if r['total']==r['effective_rejected'] else 1)
