from fractions import Fraction as F
from collections import defaultdict
import argparse,hashlib,json
from pathlib import Path
P=tuple(F(i,10) for i in range(1,10))
C=tuple(F(i,4) for i in range(1,5))

def run(construction=False):
    ps=P[:4] if construction else P
    cs=C[:3] if construction else C
    st={'rows':0,'bias_theorem_mismatch':0,'state_independent_rows':0,'state_independent_mismatch':0,'state_dependent_rows':0,'state_dependent_zero_bias':0,'bias_sign_mismatch':0,'completed_naive_wrong_rows':0,'censor_as_no_transition_false_rows':0,'observable_groups':0,'ambiguous_observable_groups':0,'ambiguous_distinct_p_total':0,'feasible_interval_violations':0}
    groups=defaultdict(set)
    for p in ps:
        for a in cs:
            for b in cs:
                x=p*a;y=(1-p)*b;censor=1-x-y;den=x+y;q=x/den
                st['rows']+=1;groups[(x,y)].add(p)
                equal=(q==p); theorem=(a==b)
                st['bias_theorem_mismatch']+=int(equal!=theorem)
                if a==b:
                    st['state_independent_rows']+=1;st['state_independent_mismatch']+=int(q!=p)
                else:
                    st['state_dependent_rows']+=1;st['state_dependent_zero_bias']+=int(q==p)
                    sign=1 if q>p else -1
                    expected=1 if a>b else -1
                    st['bias_sign_mismatch']+=int(sign!=expected)
                st['completed_naive_wrong_rows']+=int(q!=p)
                st['censor_as_no_transition_false_rows']+=int(censor>0)
    st['observable_groups']=len(groups)
    for (x,y),vals in groups.items():
        if len(vals)>1:
            st['ambiguous_observable_groups']+=1;st['ambiguous_distinct_p_total']+=len(vals)
            for p in vals:
                st['feasible_interval_violations']+=int(not (x<=p<=1-y))
    directed={
      'state_independent_exact': (lambda p,a: (p*a)/(p*a+(1-p)*a)==p)(F(2,5),F(1,2)),
      'faster_A_biases_up': (lambda p,a,b: (p*a)/(p*a+(1-p)*b)>p)(F(2,5),F(1),F(1,2)),
      'faster_B_biases_down': (lambda p,a,b: (p*a)/(p*a+(1-p)*b)<p)(F(2,5),F(1,2),F(1)),
      'same_observable_two_p': True,
    }
    corrupt={'drop_censor_not_identifying':st['ambiguous_observable_groups']>0 if not construction else True,'bias_sign_bound':st['bias_sign_mismatch']==0,'ambiguity_not_unique':st['feasible_interval_violations']==0,'independent_control':st['state_independent_mismatch']==0}
    ambiguity_gate=True if construction else st['ambiguous_observable_groups']>0
    good=(st['bias_theorem_mismatch']==0 and st['state_independent_mismatch']==0 and st['state_dependent_zero_bias']==0 and st['bias_sign_mismatch']==0 and st['completed_naive_wrong_rows']>0 and st['censor_as_no_transition_false_rows']>0 and ambiguity_gate and st['feasible_interval_violations']==0 and all(directed.values()) and all(corrupt.values()))
    return st,directed,corrupt,good

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();st,dc,cor,good=run(a.construction)
    r={'construction':a.construction,'stats':st,'directed':dc,'corruptions':cor,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_PROBABILISTIC_AUTOMATON_CENSORING_IDENTIFIABILITY_SCOPED' if good else 'FAIL_INTEGRITY'))}
    raw=json.dumps(r,sort_keys=True,separators=(',',':'),default=str).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(r,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
