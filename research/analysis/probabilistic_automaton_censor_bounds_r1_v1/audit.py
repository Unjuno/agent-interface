from fractions import Fraction as F
import argparse,hashlib,json
from pathlib import Path
P=tuple(F(i,10) for i in range(1,10));C=tuple(F(i,4) for i in range(1,5))
def ints(v):return tuple((lo,hi) for lo in C for hi in C if lo<=v<=hi)
def rec():
 s={'rows':0,'interval_mismatch':0,'true_excluded':0,'empty_interval':0,'outside_noinfo':0,'point_bound_rows':0,'point_bound_not_exact':0,'strict_noinfo_tightening':0,'partial_nonpoint_rows':0,'a_only_strictly_wider':0,'both_wider_than_a_only':0,'completion_only_wrong':0,'midpoint_plugin_wrong':0,'sharp_endpoint_checks':0,'sharp_endpoint_failures':0}
 for p in P:
  for a in C:
   for b in C:
    x=p*a;y=(1-p)*b;q=x/(x+y)
    for al,au in ints(a):
     for bl,bu in ints(b):
      L=max(F(0),x/au,F(1)-y/bl);U=min(F(1),x/al,F(1)-y/bu);s['rows']+=1;s['true_excluded']+=int(not(L<=p<=U));s['empty_interval']+=int(L>U);s['outside_noinfo']+=int(L<x or U>1-y)
      if al==au==a and bl==bu==b:s['point_bound_rows']+=1;s['point_bound_not_exact']+=int(not(L==U==p))
      s['strict_noinfo_tightening']+=int(L>x or U<1-y);s['partial_nonpoint_rows']+=int(L<U)
      AL=max(F(0),x/au);AU=min(F(1),x/al,F(1)-y);s['a_only_strictly_wider']+=int(AL<L or AU>U);s['both_wider_than_a_only']+=int(L<AL or U>AU)
      s['completion_only_wrong']+=int(q!=p);am=(al+au)/2;bm=(bl+bu)/2;mp=(x/am)/((x/am)+(y/bm));s['midpoint_plugin_wrong']+=int(mp!=p)
      for e in (L,U):
       if 0<e<1:s['sharp_endpoint_checks']+=1;s['sharp_endpoint_failures']+=int(not(al<=x/e<=au and bl<=y/(1-e)<=bu))
 return s
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());Z=json.loads(Path(a.freeze).read_text());S=rec();rs=R['stats'];checks={'decision':R['decision']=='PASS_PROBABILISTIC_AUTOMATON_CENSOR_BOUND_PARTIAL_ID_SCOPED','stats':rs==S,'contain':rs['true_excluded']==0,'empty':rs['empty_interval']==0,'noinfo':rs['outside_noinfo']==0,'point':rs['point_bound_not_exact']==0 and rs['point_bound_rows']>0,'tighten':rs['strict_noinfo_tightening']>0,'partial':rs['partial_nonpoint_rows']>0,'a_only':rs['a_only_strictly_wider']>0 and rs['both_wider_than_a_only']==0,'naive':rs['completion_only_wrong']>0,'midpoint':rs['midpoint_plugin_wrong']>0,'sharp':rs['sharp_endpoint_failures']==0,'directed':all(R['directed'].values()),'corruptions':all(R['corruptions'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==Z['sha256']['PLAN.md'],'source_formal':h('formal.py')==Z['sha256']['formal.py'],'source_audit':h('audit.py')==Z['sha256']['audit.py']};out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'audit_stats':S,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out['status']=='PASS' else 1)
if __name__=='__main__':main()
