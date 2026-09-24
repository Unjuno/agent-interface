"""Twelve effective copied-evidence mutations; baseline and parsing must pass."""
import base64, copy, hashlib, json, sys
from pathlib import Path
from audit import load_case, check_case, pack


def run(root, phase, output):
    root=Path(root);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    base=load_case(root/phase/'b3'/('r6k2-'+phase+'-3-0-SEAL_ABSENT'))
    if check_case(base)['errors']:raise ValueError('control baseline failed')
    def step(x):return next(r for r in x['sender'] if r['kind']=='STEP' and r['request']['op']=='RECONCILE')
    def body(x):return next(r for r in x['receiver'] if r['kind']=='BODY')
    def header(x):return next(r for r in x['receiver'] if r['kind']=='HEADER' and not r['response']['ready'])
    def query(x):return next(r for r in x['relay'] if r['kind']=='RPC' and r['request']['op']=='STATUS')
    changes={
      'missing_receiver_end':lambda x:x['receiver'].pop(),
      'bad_exit':lambda x:x['case']['processes']['sender'].__setitem__('exit',7),
      'duplicate_pid':lambda x:x['case']['processes']['sender'].__setitem__('pid',x['case']['processes']['receiver']['pid']),
      'payload_change':lambda x:body(x).__setitem__('payload',base64.b64encode(b'X'*4096).decode()),
      'body_identity':lambda x:body(x)['packet'].__setitem__('id','c1'),
      'terminal_header':lambda x:header(x)['response'].__setitem__('ready',True),
      'refund_erased':lambda x:step(x)['after']['c1'].__setitem__('charged',True),
      'foreign_query':lambda x:query(x)['response'].__setitem__('session','foreign'),
      'query_claim':lambda x:query(x)['actual'].__setitem__('state','ABSENT'),
      'authority':lambda x:step(x)['response'].__setitem__('authority_granted',True),
      'missing_dialogue':lambda x:x['dialogue'].pop(),
      'body_count':lambda x:next(r for r in x['relay'] if r['kind']=='FORWARD').__setitem__('body_bytes',0)
    }
    results=[]
    for name,fn in changes.items():
        obj=copy.deepcopy(base);fn(obj)
        if obj==base:raise ValueError('no-op:'+name)
        result=check_case(obj)
        if not result['errors']:raise ValueError('undetected:'+name)
        raw=pack(obj);(output/(name+'.json')).write_bytes(raw)
        (output/(name+'.audit.json')).write_bytes(pack(result))
        results.append({'name':name,'effective':True,'rejected':True,'sha256':hashlib.sha256(raw).hexdigest(),'errors':result['errors']})
    return {'controls':results,'total':len(results),'rejected':len(results),'exceptions':0}


if __name__=='__main__':
    sys.stdout.buffer.write(pack(run(*sys.argv[1:])))
