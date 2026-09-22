#!/usr/bin/env python3
import argparse, json
from pathlib import Path
POLICIES=('DELIVERY_GC','ACK_PAGE_GC','ACK_REFCOUNT_GC')
SCENARIOS=('NO_ACK_DISTINCT','ACK_PAGE1_DISTINCT','ACK_PAGE1_SHARED','ACK_BOTH_SHARED','DUPLICATE_ACK_PAGE1','STALE_EPOCH_ACK','OVER_PREFIX_ACK')

def audit_rows(raws):
    errors=[]; rows=[]
    for raw in raws:
      rows += raw['rows']
    seen=set()
    for rec in rows:
      cid=rec.get('case_id'); pol=rec.get('policy'); sc=rec.get('scenario')
      if cid in seen: errors.append(f'duplicate:{cid}')
      seen.add(cid)
      if rec.get('returncode')!=0 or 'result' not in rec: errors.append(f'process:{cid}'); continue
      r=rec['result'];
      if r.get('case_id')!=cid or r.get('policy')!=pol or r.get('scenario')!=sc: errors.append(f'identity:{cid}'); continue
      ops=r['operations']; final=r['final']; resolution=r['resolution']; shared=r['shared']
      for op in ops:
        if op.get('authority')!='none' or op.get('input_dispatched') is not False: errors.append(f'authority:{cid}')
      if sc=='STALE_EPOCH_ACK' and ops[0]['status']!='refused_stale_epoch': errors.append(f'stale_accept:{cid}')
      if sc=='OVER_PREFIX_ACK' and ops[0]['status']!='refused_invalid_prefix': errors.append(f'over_accept:{cid}')
      if sc=='DUPLICATE_ACK_PAGE1' and len(ops)==2 and ops[1]['status']!='duplicate': errors.append(f'duplicate_nonidempotent:{cid}')
      if pol=='ACK_REFCOUNT_GC':
        if any(not x['available'] or x['actual_sha256']!=x['sha'] for x in resolution): errors.append(f'candidate_unresolved:{cid}')
        blobs={x[0] for x in final['blobs']}
        if sc=='ACK_PAGE1_DISTINCT' and r['source']['sha_a'] in blobs: errors.append(f'candidate_leak_a:{cid}')
        if sc=='ACK_PAGE1_DISTINCT' and r['source']['sha_b'] not in blobs: errors.append(f'candidate_lost_b:{cid}')
        if sc=='ACK_BOTH_SHARED' and blobs: errors.append(f'candidate_shared_not_collected:{cid}')
        if sc in ('STALE_EPOCH_ACK','OVER_PREFIX_ACK'):
          if final!=r['initial']: errors.append(f'candidate_refusal_mutated:{cid}')
      if pol=='DELIVERY_GC' and sc=='NO_ACK_DISTINCT':
        if not resolution or not all(not x['available'] for x in resolution): errors.append(f'delivery_control_not_exposed:{cid}')
      if pol=='ACK_PAGE_GC' and sc=='ACK_PAGE1_SHARED':
        p2=[x for x in resolution if x['seq']==2]
        if len(p2)!=1 or p2[0]['available']: errors.append(f'page_gc_shared_not_exposed:{cid}')
    expected=len(raws)*21
    if len(rows)!=expected: errors.append(f'denominator:{len(rows)}!={expected}')
    return {'schema':'agent-interface/referenced-image-ack-gc-audit-v1','cases':len(rows),'errors':errors,'pass':not errors}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('raw',nargs='+'); ap.add_argument('--out',required=True); a=ap.parse_args()
    raws=[json.loads(Path(p).read_text()) for p in a.raw]
    out=audit_rows(raws); Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['pass'] else 2)
if __name__=='__main__': main()
