from itertools import product, permutations
from fractions import Fraction
import json

P_VALUES=(1,2)
Q_VALUES=(0,1,2,3)
N_VALUES=(2,3,4,5)

def makespan(order,p,q):
    t=0
    m=0
    for i in order:
        t += p[i]
        m=max(m,t+q[i])
    return m

def ltf_order(q):
    return tuple(sorted(range(len(q)), key=lambda i:(-q[i], i)))

rows=[]
total=counterexamples=strict_total=0
global_max=Fraction(1,1)
global_witness=None
for n in N_VALUES:
    n_total=n_bad=n_strict=0
    n_max=Fraction(1,1)
    n_witness=None
    jobs=list(product(P_VALUES,Q_VALUES))
    for spec in product(jobs, repeat=n):
        p=tuple(x[0] for x in spec)
        q=tuple(x[1] for x in spec)
        n_total+=1; total+=1
        order=ltf_order(q)
        candidate=makespan(order,p,q)
        optimum=min(makespan(o,p,q) for o in permutations(range(n)))
        if candidate != optimum:
            n_bad+=1; counterexamples+=1
        baseline=sum(p)+sum(q)
        if candidate < baseline:
            n_strict+=1; strict_total+=1
            speed=Fraction(baseline,candidate)
            if speed > n_max:
                n_max=speed
                n_witness={"p":p,"q":q,"order":order,"baseline":baseline,"ltf":candidate}
            if speed > global_max:
                global_max=speed
                global_witness={"n":n,"p":p,"q":q,"order":order,"baseline":baseline,"ltf":candidate}
    rows.append({
        "n":n,
        "cases":n_total,
        "counterexamples":n_bad,
        "strict_improvement_cases":n_strict,
        "no_improvement_cases":n_total-n_strict,
        "max_speedup_num":n_max.numerator,
        "max_speedup_den":n_max.denominator,
        "max_speedup":float(n_max),
        "witness":n_witness,
    })

out={
    "decision":"PASS_PHASE_LEVEL_OVERLAP_SCOPED" if counterexamples==0 and all(r["strict_improvement_cases"]>0 for r in rows) else "FAIL_PHASE_LEVEL_OVERLAP",
    "formal_invocations":1,
    "ranges":{"n":list(N_VALUES),"p":list(P_VALUES),"q":list(Q_VALUES)},
    "total_cases":total,
    "counterexamples":counterexamples,
    "strict_improvement_cases":strict_total,
    "rows":rows,
    "global_max_speedup_num":global_max.numerator,
    "global_max_speedup_den":global_max.denominator,
    "global_max_speedup":float(global_max),
    "global_max_witness":global_witness,
}
print(json.dumps(out,indent=2,sort_keys=True))
