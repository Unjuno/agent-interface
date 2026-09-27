from __future__ import annotations
import json,sys,math
C={'A':1.0,'B':2.0,'C':5.0,'D':10.0}; NAIVE=['D','C','B','A']; OPT=['A','B','C','D']
CASES={}
def add(i,e,w,a,b,c,d): CASES[i]=(e,w,{'A':a,'B':b,'C':c,'D':d})
for x in [
('and_A_false','AND',25,'F','T','T','T'),('and_B_false','AND',22,'T','F','T','T'),('and_C_false','AND',10,'T','T','F','T'),('and_D_false','AND',10,'T','T','T','F'),('and_all_true','AND',12,'T','T','T','T'),('and_U_only','AND',8,'U','T','T','T'),('and_U_then_F','AND',7,'U','F','T','T'),('and_late_U','AND',6,'T','T','T','U'),
('or_A_true','OR',25,'T','F','F','F'),('or_B_true','OR',22,'F','T','F','F'),('or_C_true','OR',10,'F','F','T','F'),('or_D_true','OR',10,'F','F','F','T'),('or_all_false','OR',12,'F','F','F','F'),('or_U_only','OR',8,'U','F','F','F'),('or_U_then_T','OR',7,'U','T','F','F'),('or_late_U','OR',6,'F','F','F','U')]: add(*x)
def truth(expr,v):
 xs=list(v.values())
 if expr=='AND': return 'F' if 'F' in xs else ('U' if 'U' in xs else 'T')
 return 'T' if 'T' in xs else ('U' if 'U' in xs else 'F')
def expected_used(expr,v,order):
 u=[];seen=False
 for p in order:
  u.append(p);x=v[p]
  if x=='U':seen=True;continue
  if expr=='AND' and x=='F':return u
  if expr=='OR' and x=='T':return u
 return u
def q(xs,p):
 xs=sorted(xs);return xs[max(0,min(len(xs)-1,math.ceil(p*len(xs))-1))]
def audit(o):
 err=[]; metrics={}; denom=sum(w for _,w,_ in CASES.values())
 if set(o.get('results',{}))!={'NAIVE_ORDER','COST_SELECTIVITY_ORDER'}:err.append('POLICY_SET')
 for pol,order in [('NAIVE_ORDER',NAIVE),('COST_SELECTIVITY_ORDER',OPT)]:
  rows=o.get('results',{}).get(pol,{}).get('rows',[]); by={r.get('id'):r for r in rows}
  if set(by)!=set(CASES) or len(rows)!=len(CASES):err.append(pol+':ROW_SET')
  costs=[];tw=0;wrong=unk=0
  for i,(expr,w,v) in CASES.items():
   r=by.get(i,{})
   t=truth(expr,v); eu=expected_used(expr,v,order); ec=sum(C[p] for p in eu)
   if r.get('expr')!=expr or r.get('w')!=w or r.get('truth')!=t:err.append(pol+':'+i+':PROVENANCE')
   if r.get('used')!=eu:err.append(pol+':'+i+':USED')
   if r.get('cost')!=ec:err.append(pol+':'+i+':COST')
   if r.get('decision')!=t: wrong+=w
   if (r.get('decision')=='U')!=(t=='U'):unk+=w
   costs += [ec]*w;tw+=ec*w
  metrics[pol]={'weighted_cost':tw/denom,'p95':q(costs,.95),'wrong':wrong/denom,'unknown_mismatch':unk/denom}
 op=metrics['COST_SELECTIVITY_ORDER'];na=metrics['NAIVE_ORDER']
 if op['wrong']>0:err.append('SEMANTICS')
 if op['unknown_mismatch']>0:err.append('UNKNOWN')
 if not(op['weighted_cost']<na['weighted_cost'] and op['p95']<=na['p95']):err.append('COST_GATE')
 return {'decision':'PASS_COST_BASED_PREDICATE_ORDERING_SCOPED' if not err else 'FAIL_AUDIT','errors':err,'metrics':metrics}
if __name__=='__main__':print(json.dumps(audit(json.load(open(sys.argv[1]))),sort_keys=True,separators=(',',':')))
