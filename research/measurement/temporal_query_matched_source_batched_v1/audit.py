from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import model,oracle
TASK='TEMPORAL-QUERY-MATCHED-SOURCE-COVERAGE-BATCHED-20260918-002';BATCH=11000
def expected_batch(start):
 by={k:{"n":0,"fixed":0,"query":0} for k in model.CLASSES};c={"n":0,"mismatch":0,"future":0,"cross_scope":0,"budget":0,"authority":0,"fixed":0,"query":0};h=hashlib.sha256()
 for i in range(start,start+BATCH):
  a=model.one(i);o=oracle.one(i);m=(a['class']!=o['class'] or a['fixed_covered']!=o['fixed_covered'] or a['query_covered']!=o['query_covered'])
  c['n']+=1;c['mismatch']+=int(m);c['future']+=a['future_selected'];c['cross_scope']+=a['cross_scope_selected'];c['budget']+=a['budget_violations'];c['authority']+=a['authority_grants'];c['fixed']+=int(a['fixed_covered']);c['query']+=int(a['query_covered']);z=by[a['class']];z['n']+=1;z['fixed']+=int(a['fixed_covered']);z['query']+=int(a['query_covered']);h.update(f"{i}|{a['class']}|{int(a['fixed_covered'])}|{int(a['query_covered'])}\n".encode())
 return c,by,h.hexdigest()
def verify(result,batch_dir,regenerate=True):
 e=[]
 if result.get('task')!=TASK:e.append('task')
 if result.get('formal_invocations')!=1 or result.get('batch_invocations')!=20 or result.get('batch_reruns')!=0:e.append('invocation')
 if result.get('total')!=220000:e.append('total')
 if len(result.get('manifest',[]))!=20:e.append('manifest_count')
 if regenerate:
  for bi,m in enumerate(result.get('manifest',[])):
   real=batch_dir/f'BATCH_{bi:02d}.json'
   if not real.exists():e.append('missing_batch');continue
   raw=real.read_bytes();x=json.loads(raw);c,by,h=expected_batch(bi*BATCH)
   if hashlib.sha256(raw).hexdigest()!=m.get('sha256') or len(raw)!=m.get('bytes'):e.append('batch_hash')
   if x.get('counters')!=c or x.get('by_class')!=by or x.get('row_digest')!=h:e.append('batch_regen')
 totals=result.get('counters',{})
 if any(totals.get(k) for k in ('mismatch','future','cross_scope','budget','authority')):e.append('leakage')
 cr=result.get('class_rates',{})
 if any(z.get('query_rate',0)<z.get('fixed_rate',0) for z in cr.values()):e.append('class_regression')
 delta=result.get('delta_pp')
 exp='PASS_MATCHED_SOURCE_TEMPORAL_QUERY_BATCHED_SCOPED' if not e and delta is not None and delta>=15 else ('HOLD_NO_SELECTION_DISCRIMINATOR' if not e else 'FAIL_INTEGRITY')
 if result.get('decision')!=exp:e.append('decision')
 return {"audit_pass":not e,"errors":e,"recomputed_decision":exp}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('batch_dir');ap.add_argument('--out',required=True);a=ap.parse_args();p=Path(a.result);r=json.loads(p.read_text());o=verify(r,Path(a.batch_dir));o['result_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
