from fractions import Fraction as F
from itertools import product
import argparse,hashlib,json
from pathlib import Path
P=tuple(F(i,16) for i in range(17));C=tuple(F(i,4) for i in range(17))
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def direct(p,g,w):
 r=p*w;q=(1-p)*g
 return 'RUN' if r<q else ('WAIT' if r>q else 'TIE')
def closed(p,g,w):
 if g==0 and w==0:return ('TIE',None)
 s=g/(g+w);return ('RUN' if p<s else ('WAIT' if p>s else 'TIE'),s)
def gate(cur,t,c,d):return 'CANCEL_STALE' if not cur else ('CANCEL_TARDY' if t+c>d else 'FEASIBLE')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());FZ=json.loads(Path(a.freeze).read_text())
 rows=0;mis=0;naive=0;zz=0;zzbad=0;counts={'RUN':0,'WAIT':0,'TIE':0}
 for p,g,w in product(P,C,C):
  d=direct(p,g,w);cl,s=closed(p,g,w);rows+=1;counts[d]+=1;mis+=int(d!=cl);naive+=int(('RUN' if p*w<g else ('WAIT' if p*w>g else 'TIE'))!=d)
  if g==0 and w==0:zz+=1;zzbad+=int(cl!='TIE' or s is not None)
 hv=(F(0),F(1,2),F(1));cv=(F(0),F(1),F(2));hrows=0;hover=0;ties=0;tfeas=0
 for cur,t,c,d,p,g,w in product((False,True),hv,hv,hv,(F(0),F(1,2),F(1)),cv,cv):
  x=gate(cur,t,c,d);hrows+=1
  if x!='FEASIBLE':hover+=0
  if cur and t+c==d:ties+=1;tfeas+=int(x=='FEASIBLE')
 checks={'decision':R['decision']=='PASS_EVIDENCE_COMPUTE_RUN_WAIT_BREAK_EVEN_SCOPED','rows':R['rows']==rows,'counts':R['decision_counts']==counts,'mismatch':R['threshold_direct_mismatch']==mis==0,'naive':R['naive_rule_mismatch']==naive and naive>0,'zero_zero':R['zero_zero_rows']==zz==17 and R['zero_zero_bad']==zzbad==0,'hard_rows':R['hard_composition_rows']==hrows,'hard_override':R['hard_gate_override_violations']==0,'inclusive':R['inclusive_deadline_rows']==ties and R['inclusive_deadline_feasible_rows']==tfeas,'directed':R['directed_edge_cases_pass'],'corruptions':all(R['corruption_controls'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==FZ['sha256']['PLAN.md'],'source_analyze':h('analyze.py')==FZ['sha256']['analyze.py'],'source_audit':h('audit.py')==FZ['sha256']['audit.py']}
 z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
