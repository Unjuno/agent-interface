#!/usr/bin/env python3
import argparse, copy, hashlib, itertools, json
from pathlib import Path
NAMES=["TWO_REGISTER","GENERATION_ONLY","TARGET_ONLY","CONTROL_ONLY_ACCEPT"]
def cand(n,bg,bt,qg,qt):
  if n=='TWO_REGISTER': return bg==qg and bt==qt
  if n=='GENERATION_ONLY': return bg==qg
  if n=='TARGET_ONLY': return bt==qt
  if n=='CONTROL_ONLY_ACCEPT': return True
  raise KeyError(n)
def upd(h,r): h.update(json.dumps(r,sort_keys=True,separators=(",",":")).encode()); h.update(b"\n")
def recompute(lo,hi):
  totals={n:{"unsafe_accept":0,"false_reject":0,"mismatch":0} for n in NAMES}; h=hashlib.sha256(); cases=0; lower=[]
  for G in range(lo,hi+1):
    for T in range(lo,hi+1):
      for bg in range(G):
       for bt in range(T):
        for qg in range(G):
         for qt in range(T):
          want=(bg==qg and bt==qt); r={"G":G,"T":T,"bg":bg,"bt":bt,"qg":qg,"qt":qt,"oracle":want}
          for n in NAMES:
           got=cand(n,bg,bt,qg,qt); r[n]=got
           if got!=want:
            totals[n]['mismatch']+=1
            if got: totals[n]['unsafe_accept']+=1
            else: totals[n]['false_reject']+=1
          upd(h,r); cases+=1
      b=G*T; lower.append({"G":G,"T":T,"bound_prefixes":b,"pairwise_bound_witnesses":b*(b-1)//2,"unbound_witnesses":b,"required_literal_states":b+1})
  ec=0; em=0; vals=range(3)
  for pg in itertools.permutations(vals):
   for pt in itertools.permutations(vals):
    for bg in vals:
     for bt in vals:
      for qg in vals:
       for qt in vals:
        a=(bg==qg and bt==qt); b=(pg[bg]==pg[qg] and pt[bt]==pt[qt]); ec+=1; em+=a!=b
  return {"cases":cases,"stream_sha256":h.hexdigest(),"totals":totals,"lower":lower,"equivariance":{"domain":"3x3","checks":ec,"mismatches":em}}
def compare(result, ref):
  e=[]
  if result['cases']!=ref['cases']:e.append('cases')
  if result['stream_sha256']!=ref['stream_sha256']:e.append('stream_sha256')
  if result['totals']!=ref['totals']:e.append('totals')
  if result['lower_bound']['checks']!=ref['lower']:e.append('lower_bound')
  if result['equivariance']!=ref['equivariance']:e.append('equivariance')
  ok=(ref['totals']['TWO_REGISTER']['mismatch']==0 and ref['totals']['GENERATION_ONLY']['unsafe_accept']>0 and ref['totals']['TARGET_ONLY']['unsafe_accept']>0 and ref['totals']['CONTROL_ONLY_ACCEPT']['unsafe_accept']>0 and ref['equivariance']['mismatches']==0)
  d='PASS_REGISTER_AUTOMATON_IDENTITY_SCOPED' if ok else 'FAIL_REGISTER_AUTOMATON_IDENTITY'
  if result['decision']!=d:e.append('decision')
  return e
def main():
  ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out',required=True); a=ap.parse_args()
  result=json.loads(Path(a.result).read_text()); ref=recompute(result['domain_min'],result['domain_max']); errors=compare(result,ref)
  muts={
    'summary_count':lambda x:x['totals']['TWO_REGISTER'].__setitem__('mismatch',1),
    'stream_digest':lambda x:x.__setitem__('stream_sha256','0'*64),
    'lower_bound':lambda x:x['lower_bound']['checks'][0].__setitem__('required_literal_states',999)}
  cc={}
  for n,f in muts.items():
    c=copy.deepcopy(result); f(c); cc[n]=bool(compare(c,ref))
  out={"decision":"PASS" if not errors and all(cc.values()) else "FAIL","errors":errors,"corruption_controls_detected":cc,"independent_recompute":ref}
  Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
  print(json.dumps({"decision":out['decision'],"errors":errors,"corruption_controls_detected":cc},indent=2,sort_keys=True))
if __name__=='__main__':main()
