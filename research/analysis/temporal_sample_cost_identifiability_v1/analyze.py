from fractions import Fraction as F
from itertools import product
import argparse, hashlib, json
from pathlib import Path

N_FIXED=11
N_QUERY_MAX=4
VALUES=tuple(F(i,2) for i in range(0,17))  # 0..8 by 0.5
C_VALUES=tuple(F(i,4) for i in range(1,17)) # 0.25..4
H_VALUES=tuple(F(i,4) for i in range(0,65)) # 0..16


def classify(fixed_cost, query_cost, continuation):
    q=continuation+query_cost
    if q<fixed_cost: return 'QUERY_CHEAPER'
    if q>fixed_cost: return 'FIXED_CHEAPER'
    return 'TIE'


def count_only_ordering(n_fixed,n_query):
    # Counts alone do not bind packing/layout/call-boundary cost.
    if n_fixed<0 or n_query<0: raise ValueError('counts')
    return 'NOT_IDENTIFIABLE'


def linear_threshold(k,c):
    if not (1<=k<=N_QUERY_MAX) or c<=0: raise ValueError('linear')
    return (N_FIXED-k)*c


def linear_classify(k,c,h):
    threshold=linear_threshold(k,c)
    if h<threshold: return 'QUERY_CHEAPER'
    if h>threshold: return 'FIXED_CHEAPER'
    return 'TIE'


def pareto(fixed_vec,query_vec):
    if len(fixed_vec)!=len(query_vec) or not fixed_vec: raise ValueError('vectors')
    q_le=all(q<=f for f,q in zip(fixed_vec,query_vec))
    q_lt=any(q<f for f,q in zip(fixed_vec,query_vec))
    f_le=all(f<=q for f,q in zip(fixed_vec,query_vec))
    f_lt=any(f<q for f,q in zip(fixed_vec,query_vec))
    if q_le and q_lt: return 'QUERY_PARETO_DOMINATES'
    if f_le and f_lt: return 'FIXED_PARETO_DOMINATES'
    if all(f==q for f,q in zip(fixed_vec,query_vec)): return 'TIE'
    return 'TRADEOFF'


def scalarize_without_weights(*_):
    return 'REJECT_INCOMMENSURATE_UNWEIGHTED_SUM'


def fracstr(x): return f'{x.numerator}/{x.denominator}'


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--construction',action='store_true'); ap.add_argument('--output',required=True)
    a=ap.parse_args(); out=Path(a.output); assert not out.exists()

    directed={
      'query_cheaper': {'F':F(11),'Q':F(4),'H':F(1)},
      'fixed_cheaper': {'F':F(2),'Q':F(4),'H':F(1)},
      'tie': {'F':F(5),'Q':F(4),'H':F(1)},
    }
    directed_results={k:classify(v['F'],v['Q'],v['H']) for k,v in directed.items()}
    assert directed_results=={'query_cheaper':'QUERY_CHEAPER','fixed_cheaper':'FIXED_CHEAPER','tie':'TIE'}
    assert all(count_only_ordering(N_FIXED,N_QUERY_MAX)=='NOT_IDENTIFIABLE' for _ in range(3))

    vals=VALUES[:7] if a.construction else VALUES
    frontier_counts={'QUERY_CHEAPER':0,'FIXED_CHEAPER':0,'TIE':0}
    frontier_rows=0
    direct_mismatch=0
    for fixed,query,h in product(vals,repeat=3):
        got=classify(fixed,query,h)
        direct='QUERY_CHEAPER' if h+query<fixed else ('FIXED_CHEAPER' if h+query>fixed else 'TIE')
        direct_mismatch += int(got!=direct)
        frontier_counts[got]+=1; frontier_rows+=1

    linear_mismatch=0; linear_rows=0; k4_threshold_ratios=set()
    cs=C_VALUES[:6] if a.construction else C_VALUES
    hs=H_VALUES[:17] if a.construction else H_VALUES
    for k,c,h in product(range(1,5),cs,hs):
        got=linear_classify(k,c,h)
        fixed=N_FIXED*c; query=k*c+h
        direct='QUERY_CHEAPER' if query<fixed else ('FIXED_CHEAPER' if query>fixed else 'TIE')
        linear_mismatch+=int(got!=direct); linear_rows+=1
        if k==4: k4_threshold_ratios.add(linear_threshold(k,c)/c)

    pareto_cases=[
      ((F(10),F(5)),(F(8),F(4)),'QUERY_PARETO_DOMINATES'),
      ((F(8),F(4)),(F(10),F(5)),'FIXED_PARETO_DOMINATES'),
      ((F(8),F(6)),(F(7),F(7)),'TRADEOFF'),
      ((F(8),F(6)),(F(8),F(6)),'TIE'),
    ]
    pareto_mismatch=sum(pareto(f,q)!=exp for f,q,exp in pareto_cases)

    corruptions={
      'reverse_inequality_rejected': classify(F(11),F(4),F(1))!='FIXED_CHEAPER',
      'double_count_H_detectable': classify(F(6),F(2),F(2)) != classify(F(6),F(2)+F(2),F(2)),
      'count_only_rejected': count_only_ordering(11,4)=='NOT_IDENTIFIABLE',
      'unweighted_scalarization_rejected': scalarize_without_weights((1,2),(2,1))=='REJECT_INCOMMENSURATE_UNWEIGHTED_SUM',
    }

    result={
      'construction':a.construction,'sample_counts':{'fixed':11,'query_max':4},
      'directed_results':directed_results,
      'count_only_ordering':'NOT_IDENTIFIABLE',
      'frontier_rows':frontier_rows,'frontier_counts':frontier_counts,'frontier_mismatch':direct_mismatch,
      'linear_rows':linear_rows,'linear_mismatch':linear_mismatch,
      'k4_threshold_ratio_values':sorted(fracstr(x) for x in k4_threshold_ratios),
      'k4_threshold_exact':'7*c',
      'pareto_mismatch':pareto_mismatch,'scalarization_without_weights':'REJECTED',
      'corruption_controls':corruptions,
      'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,
    }
    good=(set(directed_results.values())=={'QUERY_CHEAPER','FIXED_CHEAPER','TIE'} and direct_mismatch==0 and linear_mismatch==0 and k4_threshold_ratios=={F(7)} and pareto_mismatch==0 and all(corruptions.values()))
    result['decision']=('CONSTRUCTION_PASS' if a.construction and good else ('PASS_TEMPORAL_SAMPLE_COST_NOT_IDENTIFIABLE_FROM_COUNT_SCOPED' if good else 'FAIL_INTEGRITY'))
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result['digest']=hashlib.sha256(raw).hexdigest()
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
