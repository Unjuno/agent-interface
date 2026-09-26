#!/usr/bin/env python3
import copy, json, sys
from pathlib import Path
from audit import audit_rows

def main(paths):
    raws=[json.loads(Path(p).read_text()) for p in paths]
    base=audit_rows(raws)
    assert base['pass'],base
    controls=[]
    mutations=[
      ('drop_case', lambda x: x[0]['rows'].pop()),
      ('returncode', lambda x: x[0]['rows'][0].__setitem__('returncode',9)),
      ('identity', lambda x: x[0]['rows'][0]['result'].__setitem__('case_id','wrong')),
      ('authority', lambda x: x[0]['rows'][0]['result']['operations'][0].__setitem__('authority','input')),
      ('candidate_resolution', lambda x: next(r for r in x[0]['rows'] if r['policy']=='ACK_REFCOUNT_GC' and r['scenario']=='NO_ACK_DISTINCT')['result']['resolution'][0].__setitem__('available',False)),
      ('candidate_hash', lambda x: next(r for r in x[0]['rows'] if r['policy']=='ACK_REFCOUNT_GC' and r['scenario']=='NO_ACK_DISTINCT')['result']['resolution'][0].__setitem__('actual_sha256','0'*64)),
      ('stale_accept', lambda x: next(r for r in x[0]['rows'] if r['policy']=='ACK_REFCOUNT_GC' and r['scenario']=='STALE_EPOCH_ACK')['result']['operations'][0].__setitem__('status','applied')),
      ('over_accept', lambda x: next(r for r in x[0]['rows'] if r['policy']=='ACK_REFCOUNT_GC' and r['scenario']=='OVER_PREFIX_ACK')['result']['operations'][0].__setitem__('status','applied')),
      ('duplicate_status', lambda x: next(r for r in x[0]['rows'] if r['policy']=='ACK_REFCOUNT_GC' and r['scenario']=='DUPLICATE_ACK_PAGE1')['result']['operations'][1].__setitem__('status','applied')),
      ('control_hide_delivery', lambda x: next(r for r in x[0]['rows'] if r['policy']=='DELIVERY_GC' and r['scenario']=='NO_ACK_DISTINCT')['result']['resolution'][0].__setitem__('available',True)),
    ]
    for name,fn in mutations:
      y=copy.deepcopy(raws); fn(y); a=audit_rows(y); controls.append({'name':name,'rejected':not a['pass'],'errors':a['errors'][:4]})
    assert all(c['rejected'] for c in controls),controls
    print(json.dumps({'controls':controls,'rejected':len(controls)},indent=2,sort_keys=True))
if __name__=='__main__': main(sys.argv[1:])
