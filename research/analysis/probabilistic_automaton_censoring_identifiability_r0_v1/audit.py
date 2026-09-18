from fractions import Fraction as F
from collections import defaultdict
import argparse,hashlib,json
from pathlib import Path
P=tuple(F(i,10) for i in range(1,10));C=tuple(F(i,4) for i in range(1,5))
def counts():
 s={'rows':0,'bias_theorem_mismatch':0,'state_independent_rows':0,'state_independent_mismatch':0,'state_dependent_rows':0,'state_dependent_zero_bias':0,'bias_sign_mismatch':0,'completed_naive_wrong_rows':0,'censor_as_no_transition_false_rows':0,'observable_groups':0,'ambiguous_observable_groups':0,'ambiguous_distinct_p_total':0,'feasible_interval_violations':0};g=defaultdict(set)
 for p in P:
  for a in C:
   for b in C:
    x=p*a;y=(1-p)*b;q=x/(x+y);z=1-x-y;s['rows']+=1;g[(x,y)].add(p);eq=q==p;s['bias_theorem_mismatch']+=int(eq!=(a==b))
    if a==b:s['state_independent_rows']+=1;s['state_independent_mismatch']+=int(q!=p)
    else:
     s['state_dependent_rows']+=1;s['state_dependent_zero_bias']+=int(q==p);s['bias_sign_mismatch']+=int((q>p)!=(a>b))
    s['completed_naive_wrong_rows']+=int(q!=p);s['censor_as_no_transition_false_rows']+=int(z>0)
 s['observable_groups']=len(g)
 for (x,y),ps in g.items():
  if len(ps)>1:
   s['ambiguous_observable_groups']+=1;s['ambiguous_distinct_p_total']+=len(ps)
   for p in ps:s['feasible_interval_violations']+=int(not(x<=p<=1-y))
 return s
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());Z=json.loads(Path(a.freeze).read_text());S=counts();rs=R['stats'];checks={'decision':R['decision']=='PASS_PROBABILISTIC_AUTOMATON_CENSORING_IDENTIFIABILITY_SCOPED','stats':rs==S,'theorem':rs['bias_theorem_mismatch']==0,'independent':rs['state_independent_mismatch']==0,'dependent':rs['state_dependent_zero_bias']==0 and rs['bias_sign_mismatch']==0,'ambiguity':rs['ambiguous_observable_groups']>0,'interval':rs['feasible_interval_violations']==0,'naive':rs['completed_naive_wrong_rows']>0,'censor_false':rs['censor_as_no_transition_false_rows']>0,'directed':all(R['directed'].values()),'corruptions':all(R['corruptions'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==Z['sha256']['PLAN.md'],'source_formal':h('formal.py')==Z['sha256']['formal.py'],'source_audit':h('audit.py')==Z['sha256']['audit.py']};out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'audit_stats':S,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out['status']=='PASS' else 1)
if __name__=='__main__':main()
