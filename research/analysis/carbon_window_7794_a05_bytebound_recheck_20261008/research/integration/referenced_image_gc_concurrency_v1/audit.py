#!/usr/bin/env python3
import argparse,json
from pathlib import Path

def audit(raws):
    rows=sum((x['rows'] for x in raws),[]); errors=[]; seen=set()
    for rec in rows:
      cid=rec.get('case_id'); p=rec.get('policy'); s=rec.get('scenario')
      if cid in seen: errors.append('duplicate:'+str(cid))
      seen.add(cid)
      if rec.get('returncode')!=0 or 'result' not in rec: errors.append('process:'+str(cid)); continue
      r=rec['result']
      if r.get('case_id')!=cid or r.get('policy')!=p or r.get('scenario')!=s: errors.append('identity:'+cid); continue
      if r.get('authority')!='none' or r.get('input_dispatched') is not False: errors.append('authority:'+cid)
      actors=r.get('actors',[])
      expected_actor_count=2 if s=='NO_NEW_REFERENCE' else 3
      if len(actors)!=expected_actor_count or any(a.get('returncode')!=0 for a in actors): errors.append('actors:'+cid)
      unresolved=[x for x in r['resolution'] if not x['available'] or x['actual_sha256']!=x['sha']]
      if p=='TXN_REVALIDATE_DELETE' and unresolved: errors.append('candidate_unresolved:'+cid)
      if p=='STALE_SCAN_DELETE' and s=='PRODUCER_BETWEEN_SCAN_DELETE':
        if len(unresolved)!=1 or unresolved[0]['seq']!=2: errors.append('unsafe_not_exposed:'+cid)
      if s in ('PRODUCER_BEFORE_SCAN','PRODUCER_AFTER_DELETE') and unresolved: errors.append(('before' if s=='PRODUCER_BEFORE_SCAN' else 'after')+'_unresolved:'+cid)
      if s=='NO_NEW_REFERENCE' and r['final']['blobs']: errors.append('no_ref_not_collected:'+cid)
      if s=='PRODUCER_BEFORE_SCAN' and not r['final']['blobs']: errors.append('live_blob_deleted:'+cid)
    expected=len(raws)*8
    if len(rows)!=expected: errors.append(f'denominator:{len(rows)}!={expected}')
    return {'schema':'agent-interface/referenced-image-gc-concurrency-audit-v1','cases':len(rows),'errors':errors,'pass':not errors}

def main():
    a=argparse.ArgumentParser(); a.add_argument('raw',nargs='+'); a.add_argument('--out',required=True); x=a.parse_args(); raws=[json.loads(Path(p).read_text()) for p in x.raw]; o=audit(raws); Path(x.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,sort_keys=True)); raise SystemExit(0 if o['pass'] else 2)
if __name__=='__main__': main()
