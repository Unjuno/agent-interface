#!/usr/bin/env python3
import copy,json,sys
from pathlib import Path
from audit import audit

def main(paths):
  raws=[json.loads(Path(p).read_text()) for p in paths]; assert audit(raws)['pass']; controls=[]
  def hide_unsafe(x):
    r=next(r for r in x[0]['rows'] if r['policy']=='STALE_SCAN_DELETE' and r['scenario']=='PRODUCER_BETWEEN_SCAN_DELETE')['result']; r['resolution'][0]['available']=True; r['resolution'][0]['actual_sha256']=r['resolution'][0]['sha']
  muts=[('drop',lambda x:x[0]['rows'].pop()),('returncode',lambda x:x[0]['rows'][0].__setitem__('returncode',9)),('identity',lambda x:x[0]['rows'][0]['result'].__setitem__('case_id','wrong')),('authority',lambda x:x[0]['rows'][0]['result'].__setitem__('authority','input')),('actor_exit',lambda x:x[0]['rows'][0]['result']['actors'][0].__setitem__('returncode',7)),('candidate_missing',lambda x:next(r for r in x[0]['rows'] if r['policy']=='TXN_REVALIDATE_DELETE' and r['scenario']=='PRODUCER_BEFORE_SCAN')['result']['resolution'][0].__setitem__('available',False)),('candidate_hash',lambda x:next(r for r in x[0]['rows'] if r['policy']=='TXN_REVALIDATE_DELETE' and r['scenario']=='PRODUCER_BEFORE_SCAN')['result']['resolution'][0].__setitem__('actual_sha256','0'*64)),('hide_unsafe',hide_unsafe),('keep_orphan',lambda x:next(r for r in x[0]['rows'] if r['scenario']=='NO_NEW_REFERENCE')['result']['final']['blobs'].append(['fake',1,'fake'])),('delete_live',lambda x:next(r for r in x[0]['rows'] if r['scenario']=='PRODUCER_BEFORE_SCAN')['result']['final'].__setitem__('blobs',[]))]
  for n,f in muts:
    y=copy.deepcopy(raws); f(y); a=audit(y); controls.append({'name':n,'rejected':not a['pass'],'errors':a['errors'][:3]})
  assert all(c['rejected'] for c in controls),controls; print(json.dumps({'controls':controls,'rejected':len(controls)},indent=2,sort_keys=True))
if __name__=='__main__': main(sys.argv[1:])
