from fractions import Fraction as F
from itertools import product
import argparse,hashlib,json
from pathlib import Path
P=tuple(F(i,16) for i in range(17))
C=tuple(F(i,4) for i in range(17))

def direct(p,g,w):
    run=p*w
    wait=(1-p)*g
    if run<wait:return 'RUN'
    if run>wait:return 'WAIT'
    return 'TIE'

def threshold(p,g,w):
    if g==0 and w==0:return ('TIE',None)
    star=g/(g+w)
    if p<star:return ('RUN',star)
    if p>star:return ('WAIT',star)
    return ('TIE',star)

def hard_gate(current,t,c,d):
    if not current:return 'CANCEL_STALE'
    if t+c>d:return 'CANCEL_TARDY'
    return 'FEASIBLE'

def policy(current,t,c,d,p,g,w):
    gate=hard_gate(current,t,c,d)
    if gate!='FEASIBLE':return gate
    return threshold(p,g,w)[0]

def naive(p,g,w):
    # Incorrect comparator that forgets WAIT's stable probability factor.
    run=p*w
    if run<g:return 'RUN'
    if run>g:return 'WAIT'
    return 'TIE'

def directed():
    cases=[
      (F(0),F(1),F(1),'RUN'),
      (F(1),F(1),F(1),'WAIT'),
      (F(1,2),F(1),F(1),'TIE'),
      (F(1),F(1),F(0),'TIE'),
      (F(0),F(0),F(1),'TIE'),
      (F(3,4),F(0),F(0),'TIE'),
    ]
    return all(direct(p,g,w)==exp and threshold(p,g,w)[0]==exp for p,g,w,exp in cases)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists()
    ps=P[:9] if a.construction else P
    cs=C[:9] if a.construction else C
    rows=0; mismatch=0; naive_mismatch=0; zz_rows=0; zz_bad=0; thresholds=0
    counts={'RUN':0,'WAIT':0,'TIE':0}
    for p,g,w in product(ps,cs,cs):
        d=direct(p,g,w);t,star=threshold(p,g,w);rows+=1;counts[d]+=1;mismatch+=int(d!=t);naive_mismatch+=int(naive(p,g,w)!=d)
        if g==0 and w==0:zz_rows+=1;zz_bad+=int(t!='TIE' or star is not None)
        else:thresholds+=int(star is not None)
    # Composition: expected-value layer must never override stale/tardy hard gate.
    hv=(F(0),F(1,2),F(1)); costv=(F(0),F(1),F(2)); hard_rows=0; hard_override=0; tie_gate_rows=0; tie_gate_feasible=0
    for current,t,c,d,p,g,w in product((False,True),hv,hv,hv,(F(0),F(1,2),F(1)),costv,costv):
        gate=hard_gate(current,t,c,d);got=policy(current,t,c,d,p,g,w);hard_rows+=1
        if gate!='FEASIBLE': hard_override+=int(got not in ('CANCEL_STALE','CANCEL_TARDY'))
        if current and t+c==d:
            tie_gate_rows+=1;tie_gate_feasible+=int(gate=='FEASIBLE')
    corruptions={
      'reverse_inequality_rejected': direct(F(1,4),F(1),F(1))=='RUN',
      'omit_stable_probability_detected': naive_mismatch>0,
      'stale_override_rejected': policy(False,F(0),F(1),F(2),F(0),F(10),F(0))=='CANCEL_STALE',
      'zero_zero_threshold_rejected': all(threshold(p,F(0),F(0))==('TIE',None) for p in P),
    }
    good=(mismatch==0 and directed() and hard_override==0 and naive_mismatch>0 and zz_bad==0 and zz_rows==len(ps) and all(corruptions.values()))
    r={'construction':a.construction,'rows':rows,'decision_counts':counts,'threshold_direct_mismatch':mismatch,'naive_rule_mismatch':naive_mismatch,'zero_zero_rows':zz_rows,'zero_zero_bad':zz_bad,'nonzero_threshold_rows':thresholds,'directed_edge_cases_pass':directed(),'hard_composition_rows':hard_rows,'hard_gate_override_violations':hard_override,'inclusive_deadline_rows':tie_gate_rows,'inclusive_deadline_feasible_rows':tie_gate_feasible,'corruption_controls':corruptions,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_EVIDENCE_COMPUTE_RUN_WAIT_BREAK_EVEN_SCOPED' if good else 'FAIL_INTEGRITY'))}
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
